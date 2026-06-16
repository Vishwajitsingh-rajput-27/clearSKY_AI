from __future__ import annotations

import torch
from torch import nn

from app.ai.models.blocks import ConvBlock, DownBlock, UpBlock


class UNetCloudSegmenter(nn.Module):
    """U-Net cloud segmentation model returning cloud-mask logits."""

    def __init__(
        self,
        in_channels: int = 3,
        out_channels: int = 1,
        base_channels: int = 32,
        dropout: float = 0.1,
    ) -> None:
        super().__init__()
        channels = [base_channels, base_channels * 2, base_channels * 4, base_channels * 8]
        self.stem = ConvBlock(in_channels, channels[0], dropout=dropout)
        self.down1 = DownBlock(channels[0], channels[1], dropout=dropout)
        self.down2 = DownBlock(channels[1], channels[2], dropout=dropout)
        self.down3 = DownBlock(channels[2], channels[3], dropout=dropout)
        self.bottleneck = DownBlock(channels[3], channels[3] * 2, dropout=dropout)
        self.up3 = UpBlock(channels[3] * 2, channels[3], channels[3])
        self.up2 = UpBlock(channels[3], channels[2], channels[2])
        self.up1 = UpBlock(channels[2], channels[1], channels[1])
        self.up0 = UpBlock(channels[1], channels[0], channels[0])
        self.head = nn.Conv2d(channels[0], out_channels, kernel_size=1)

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
