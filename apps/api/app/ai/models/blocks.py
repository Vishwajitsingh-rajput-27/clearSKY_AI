from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F


class ConvBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, *, dropout: float = 0.0) -> None:
        super().__init__()
        layers: list[nn.Module] = [
            nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.GELU(),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(out_channels),
            nn.GELU(),
        ]
        if dropout > 0:
            layers.append(nn.Dropout2d(dropout))

        self.block = nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.block(x)


class DownBlock(nn.Module):
    def __init__(self, in_channels: int, out_channels: int, *, dropout: float = 0.0) -> None:
        super().__init__()
        self.pool = nn.MaxPool2d(kernel_size=2)
        self.conv = ConvBlock(in_channels, out_channels, dropout=dropout)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.conv(self.pool(x))


class UpBlock(nn.Module):
    def __init__(self, in_channels: int, skip_channels: int, out_channels: int) -> None:
        super().__init__()
        self.up = nn.ConvTranspose2d(in_channels, out_channels, kernel_size=2, stride=2)
        self.conv = ConvBlock(out_channels + skip_channels, out_channels)

    def forward(self, x: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        x = self.up(x)
        x = resize_like(x, skip)
        return self.conv(torch.cat([skip, x], dim=1))


class AttentionGate(nn.Module):
    def __init__(self, gating_channels: int, skip_channels: int, intermediate_channels: int) -> None:
        super().__init__()
        self.gating_projection = nn.Sequential(
            nn.Conv2d(gating_channels, intermediate_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(intermediate_channels),
        )
        self.skip_projection = nn.Sequential(
            nn.Conv2d(skip_channels, intermediate_channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(intermediate_channels),
        )
        self.psi = nn.Sequential(
            nn.Conv2d(intermediate_channels, 1, kernel_size=1),
            nn.Sigmoid(),
        )
        self.activation = nn.GELU()

    def forward(self, gating: torch.Tensor, skip: torch.Tensor) -> torch.Tensor:
        gating = resize_like(gating, skip)
        attention = self.activation(self.gating_projection(gating) + self.skip_projection(skip))
        attention = self.psi(attention)
        return skip * attention


class ResidualBlock(nn.Module):
    def __init__(self, channels: int) -> None:
        super().__init__()
        self.block = ConvBlock(channels, channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return x + self.block(x)


class WindowSelfAttention(nn.Module):
    def __init__(
        self,
        dim: int,
        *,
        num_heads: int = 4,
        window_size: int = 8,
        shift_size: int = 0,
        dropout: float = 0.0,
    ) -> None:
        super().__init__()
        if dim % num_heads != 0:
            raise ValueError("dim must be divisible by num_heads")

        self.dim = dim
        self.num_heads = num_heads
        self.window_size = window_size
        self.shift_size = shift_size
        self.scale = (dim // num_heads) ** -0.5
        self.qkv = nn.Linear(dim, dim * 3)
        self.proj = nn.Linear(dim, dim)
        self.dropout = nn.Dropout(dropout)
        self.norm = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.LayerNorm(dim),
            nn.Linear(dim, dim * 4),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(dim * 4, dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        b, c, h, w = x.shape
        shortcut = x
        pad_h = (self.window_size - h % self.window_size) % self.window_size
        pad_w = (self.window_size - w % self.window_size) % self.window_size
        x = F.pad(x, (0, pad_w, 0, pad_h))

        if self.shift_size > 0:
            x = torch.roll(x, shifts=(-self.shift_size, -self.shift_size), dims=(2, 3))

        _, _, padded_h, padded_w = x.shape
        windows = window_partition(x, self.window_size)
        windows = windows.reshape(-1, self.window_size * self.window_size, c)
        windows = self.norm(windows)

        qkv = self.qkv(windows)
        qkv = qkv.reshape(qkv.shape[0], qkv.shape[1], 3, self.num_heads, c // self.num_heads)
        q, k, v = qkv.permute(2, 0, 3, 1, 4)
        attention = (q @ k.transpose(-2, -1)) * self.scale
        attention = attention.softmax(dim=-1)
        attention = self.dropout(attention)
        attended = (attention @ v).transpose(1, 2).reshape(windows.shape[0], windows.shape[1], c)
        attended = windows + self.proj(attended)
        attended = attended + self.mlp(attended)
        attended = attended.reshape(-1, self.window_size, self.window_size, c)

        x = window_reverse(attended, self.window_size, padded_h, padded_w, b)
        if self.shift_size > 0:
            x = torch.roll(x, shifts=(self.shift_size, self.shift_size), dims=(2, 3))

        x = x[:, :, :h, :w]
        return shortcut + x


def resize_like(x: torch.Tensor, reference: torch.Tensor) -> torch.Tensor:
    if x.shape[-2:] == reference.shape[-2:]:
        return x

    return F.interpolate(x, size=reference.shape[-2:], mode="bilinear", align_corners=False)


def window_partition(x: torch.Tensor, window_size: int) -> torch.Tensor:
    b, c, h, w = x.shape
    x = x.view(b, c, h // window_size, window_size, w // window_size, window_size)
    windows = x.permute(0, 2, 4, 3, 5, 1).contiguous()
    return windows.view(-1, window_size, window_size, c)


def window_reverse(
    windows: torch.Tensor,
    window_size: int,
    height: int,
    width: int,
    batch_size: int,
) -> torch.Tensor:
    x = windows.view(
        batch_size,
        height // window_size,
        width // window_size,
        window_size,
        window_size,
        -1,
    )
    x = x.permute(0, 5, 1, 3, 2, 4).contiguous()
    return x.view(batch_size, -1, height, width)
