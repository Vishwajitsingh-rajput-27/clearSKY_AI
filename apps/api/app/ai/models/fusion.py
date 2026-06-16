from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F

from app.ai.models.attention_unet import AttentionUNetReconstructor
from app.ai.models.blocks import ConvBlock


class SensorEncoder(nn.Module):
    def __init__(self, in_channels: int, out_channels: int) -> None:
        super().__init__()
        self.encoder = nn.Sequential(
            ConvBlock(in_channels, out_channels),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.GELU(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)


class TemporalFusionModule(nn.Module):
    """Attention fusion over temporal references shaped [B, T, C, H, W]."""

    def __init__(self, channels: int, hidden_channels: int = 32) -> None:
        super().__init__()
        self.score = nn.Sequential(
            nn.Conv2d(channels * 2, hidden_channels, kernel_size=3, padding=1),
            nn.GELU(),
            nn.Conv2d(hidden_channels, 1, kernel_size=1),
        )
        self.refine = ConvBlock(channels, channels)

    def forward(
        self,
        cloudy: torch.Tensor,
        temporal_refs: torch.Tensor | None,
    ) -> tuple[torch.Tensor | None, torch.Tensor | None]:
        if temporal_refs is None:
            return None, None

        b, t, c, h, w = temporal_refs.shape
        cloudy_expanded = cloudy.unsqueeze(1).expand(-1, t, -1, -1, -1)
        pairs = torch.cat([cloudy_expanded, temporal_refs], dim=2).reshape(b * t, c * 2, h, w)
        scores = self.score(pairs).reshape(b, t, 1, h, w)
        weights = torch.softmax(scores, dim=1)
        fused = (weights * temporal_refs).sum(dim=1)
        return self.refine(fused), weights.squeeze(2)


class Sentinel1SARFusionModule(nn.Module):
    """VV/VH SAR feature encoder for cloud-robust structural cues."""

    def __init__(self, in_channels: int = 2, out_channels: int = 16) -> None:
        super().__init__()
        self.encoder = SensorEncoder(in_channels, out_channels)

    def forward(self, sentinel1: torch.Tensor | None) -> torch.Tensor | None:
        return None if sentinel1 is None else self.encoder(sentinel1)


class Sentinel2FusionModule(nn.Module):
    """Sentinel-2 optical feature encoder for lower-resolution spectral context."""

    def __init__(self, in_channels: int = 10, out_channels: int = 24) -> None:
        super().__init__()
        self.encoder = SensorEncoder(in_channels, out_channels)

    def forward(self, sentinel2: torch.Tensor | None) -> torch.Tensor | None:
        return None if sentinel2 is None else self.encoder(sentinel2)


class DEMFusionModule(nn.Module):
    """DEM feature encoder for elevation, slope, and hillshade-like terrain cues."""

    def __init__(self, in_channels: int = 1, out_channels: int = 8) -> None:
        super().__init__()
        self.encoder = SensorEncoder(in_channels, out_channels)

    def forward(self, dem: torch.Tensor | None) -> torch.Tensor | None:
        return None if dem is None else self.encoder(dem)


class MultiSensorFusionNetwork(nn.Module):
    """Cloud-free reconstruction model with optional temporal, SAR, Sentinel-2, and DEM inputs."""

    def __init__(
        self,
        liss_channels: int = 4,
        sentinel1_channels: int = 2,
        sentinel2_channels: int = 10,
        dem_channels: int = 1,
        out_channels: int = 3,
        feature_channels: int = 32,
    ) -> None:
        super().__init__()
        self.feature_channels = feature_channels
        self.liss_encoder = SensorEncoder(liss_channels, feature_channels)
        self.temporal_adapter = nn.Conv2d(3, feature_channels, kernel_size=1)
        self.temporal_fusion = TemporalFusionModule(feature_channels)
        self.sentinel1 = Sentinel1SARFusionModule(sentinel1_channels, 16)
        self.sentinel2 = Sentinel2FusionModule(sentinel2_channels, 24)
        self.dem = DEMFusionModule(dem_channels, 8)
        fusion_channels = feature_channels + feature_channels + 16 + 24 + 8
        self.fusion_projection = nn.Sequential(
            nn.Conv2d(fusion_channels, feature_channels * 2, kernel_size=1),
            nn.GELU(),
            ConvBlock(feature_channels * 2, feature_channels),
        )
        self.reconstructor = AttentionUNetReconstructor(
            in_channels=feature_channels,
            out_channels=out_channels,
            base_channels=feature_channels,
        )

    def forward(
        self,
        liss: torch.Tensor,
        *,
        sentinel1: torch.Tensor | None = None,
        sentinel2: torch.Tensor | None = None,
        dem: torch.Tensor | None = None,
        temporal_refs: torch.Tensor | None = None,
    ) -> torch.Tensor:
        liss_features = self.liss_encoder(liss)
        target_size = liss_features.shape[-2:]
        missing_features = liss_features.new_zeros(
            liss_features.shape[0],
            0,
            target_size[0],
            target_size[1],
        )

        temporal_features = None
        if temporal_refs is not None:
            b, t, c, h, w = temporal_refs.shape
            temporal_refs = temporal_refs.reshape(b * t, c, h, w)
            temporal_refs = self.temporal_adapter(temporal_refs)
            temporal_refs = F.interpolate(
                temporal_refs,
                size=target_size,
                mode="bilinear",
                align_corners=False,
            ).reshape(
                b,
                t,
                -1,
                target_size[0],
                target_size[1],
            )
            temporal_features, _ = self.temporal_fusion(liss_features, temporal_refs)

        features = [
            liss_features,
            self._resize_or_zero(
                temporal_features,
                feature_channels=self.feature_channels,
                like=liss_features,
            ),
            self._resize_or_zero(self.sentinel1(sentinel1), feature_channels=16, like=liss_features),
            self._resize_or_zero(self.sentinel2(sentinel2), feature_channels=24, like=liss_features),
            self._resize_or_zero(self.dem(dem), feature_channels=8, like=liss_features),
        ]
        fused = torch.cat([feature if feature is not None else missing_features for feature in features], dim=1)
        return self.reconstructor(self.fusion_projection(fused))

    @staticmethod
    def _resize_or_zero(
        feature: torch.Tensor | None,
        *,
        feature_channels: int,
        like: torch.Tensor,
    ) -> torch.Tensor:
        if feature is None:
            return like.new_zeros(like.shape[0], feature_channels, like.shape[-2], like.shape[-1])

        if feature.shape[-2:] != like.shape[-2:]:
            feature = F.interpolate(feature, size=like.shape[-2:], mode="bilinear", align_corners=False)

        return feature
