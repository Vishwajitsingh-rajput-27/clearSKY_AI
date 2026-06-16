from __future__ import annotations

import torch
from torch import nn

from app.ai.models.blocks import ConvBlock, UpBlock, WindowSelfAttention


class SwinStage(nn.Module):
    def __init__(
        self,
        channels: int,
        *,
        depth: int,
        num_heads: int,
        window_size: int,
        dropout: float,
    ) -> None:
        super().__init__()
        blocks: list[nn.Module] = []
        shift_size = max(1, window_size // 2)
        for index in range(depth):
            blocks.append(
                WindowSelfAttention(
                    channels,
                    num_heads=num_heads,
                    window_size=window_size,
                    shift_size=0 if index % 2 == 0 else shift_size,
                    dropout=dropout,
                )
            )
        self.blocks = nn.Sequential(*blocks)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.blocks(x)


class SwinUNetReconstructor(nn.Module):
    """Swin-style U-Net reconstruction network with shifted-window bottleneck attention."""

    def __init__(
        self,
        in_channels: int = 4,
        out_channels: int = 3,
        base_channels: int = 32,
        window_size: int = 8,
        dropout: float = 0.05,
    ) -> None:
        super().__init__()
        channels = [base_channels, base_channels * 2, base_channels * 4, base_channels * 8]
        self.stem = ConvBlock(in_channels, channels[0], dropout=dropout)
        self.down1 = nn.Sequential(
            nn.Conv2d(channels[0], channels[1], kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(channels[1]),
            nn.GELU(),
            SwinStage(
                channels[1],
                depth=2,
                num_heads=4,
                window_size=window_size,
                dropout=dropout,
            ),
        )
        self.down2 = nn.Sequential(
            nn.Conv2d(channels[1], channels[2], kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(channels[2]),
            nn.GELU(),
            SwinStage(
                channels[2],
                depth=2,
                num_heads=4,
                window_size=window_size,
                dropout=dropout,
            ),
        )
        self.down3 = nn.Sequential(
            nn.Conv2d(channels[2], channels[3], kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(channels[3]),
            nn.GELU(),
            SwinStage(
                channels[3],
                depth=4,
                num_heads=8,
                window_size=window_size,
                dropout=dropout,
            ),
        )
        self.bottleneck = nn.Sequential(
            nn.Conv2d(channels[3], channels[3] * 2, kernel_size=3, stride=2, padding=1),
            nn.BatchNorm2d(channels[3] * 2),
            nn.GELU(),
            SwinStage(
                channels[3] * 2,
                depth=4,
                num_heads=8,
                window_size=window_size,
                dropout=dropout,
            ),
        )
        self.up3 = UpBlock(channels[3] * 2, channels[3], channels[3])
        self.up2 = UpBlock(channels[3], channels[2], channels[2])
        self.up1 = UpBlock(channels[2], channels[1], channels[1])
        self.up0 = UpBlock(channels[1], channels[0], channels[0])
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
