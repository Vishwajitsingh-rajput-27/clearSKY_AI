from __future__ import annotations

import torch
from torch import nn

from app.ai.models.blocks import AttentionGate, ConvBlock, DownBlock, resize_like


class AttentionUpBlock(nn.Module):
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int) -> None:
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)
        self.gate = AttentionGate(out_channels, skip_channels, max(out_channels // 2, 8))
        self.conv = ConvBlock(out_channels + skip_channels, out_channels)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        x = resize_like(x, skip)
        skip = self.gate(x, skip)
        return self.conv(torch.cat([skip, x], dim=1))


class AttentionUNetReconstructor(nn.Module):
    """Attention U-Net for cloud-free image reconstruction.

    The expected input is usually cloudy RGB plus one or more mask/context channels. The output is
    a normalized cloud-free RGB prediction in [0, 1].
    """

    def __init__(
        self,
        in_channels: int = 4,
        out_channels: int = 3,
        base_channels: int = 32,
        dropout: float = 0.05,
    ) -> None:
        super().__init__()
        channels = [base_channels, base_channels * 2, base_channels * 4, base_channels * 8]
        self.stem = ConvBlock(in_channels, channels[0], dropout=dropout)
        self.down1 = DownBlock(channels[0], channels[1], dropout=dropout)
        self.down2 = DownBlock(channels[1], channels[2], dropout=dropout)
        self.down3 = DownBlock(channels[2], channels[3], dropout=dropout)
        self.bottleneck = DownBlock(channels[3], channels[3] * 2, dropout=dropout)
        self.up3 = AttentionUpBlock(channels[3] * 2, channels[3], channels[3])
        self.up2 = AttentionUpBlock(channels[3], channels[2], channels[2])
        self.up1 = AttentionUpBlock(channels[2], channels[1], channels[1])
        self.up0 = AttentionUpBlock(channels[1], channels[0], channels[0])
        self.head = nn.Sequential(
            nn.Conv2d(channels[0], out_channels, kernel_size=1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skip0 = self.stem(x)
        skip1 = self.down1(skip0)
        skip2 = self.down2(skip1)
        skip3 = self.down3(skip2)
        x = self.bottleneck(skip3)
        x = self.up3(x, skip3)
        x = self.up2(x, skip2)
        x = self.up1(x, skip1)
        x = self.up0(x, skip0)
        return self.head(x)
