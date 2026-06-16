from __future__ import annotations

import torch
from torch import nn
from torch.nn import functional as F


class SpectralConsistencyLoss(nn.Module):
    """Spectral angle mapper plus L1 consistency for multi-band preservation."""

    def __init__(self, eps: float = 1e-6, l1_weight: float = 0.25) -> None:
        super().__init__()
        self.eps = eps
        self.l1_weight = l1_weight

    def forward(
        self,
        prediction: torch.Tensor,
        target: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        prediction = prediction.clamp(0, 1)
        target = target.clamp(0, 1)
        dot = (prediction * target).sum(dim=1)
        prediction_norm = prediction.norm(dim=1)
        target_norm = target.norm(dim=1)
        cosine = dot / (prediction_norm * target_norm + self.eps)
        spectral_angle = torch.acos(cosine.clamp(-1 + self.eps, 1 - self.eps))
        l1 = (prediction - target).abs().mean(dim=1)
        loss_map = spectral_angle + self.l1_weight * l1
        return masked_mean(loss_map, mask)


class EdgeLoss(nn.Module):
    """Sobel edge difference loss for preserving field boundaries and linear features."""

    def __init__(self) -> None:
        super().__init__()
        sobel_x = torch.tensor(
            [[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]],
            dtype=torch.float32,
        )
        sobel_y = torch.tensor(
            [[-1, -2, -1], [0, 0, 0], [1, 2, 1]],
            dtype=torch.float32,
        )
        self.register_buffer("sobel_x", sobel_x.view(1, 1, 3, 3))
        self.register_buffer("sobel_y", sobel_y.view(1, 1, 3, 3))

    def forward(
        self,
        prediction: torch.Tensor,
        target: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        prediction_edges = self._edges(prediction)
        target_edges = self._edges(target)
        loss_map = (prediction_edges - target_edges).abs().mean(dim=1)
        return masked_mean(loss_map, mask)

    def _edges(self, image: torch.Tensor) -> torch.Tensor:
        channels = image.shape[1]
        sobel_x = self.sobel_x.repeat(channels, 1, 1, 1)
        sobel_y = self.sobel_y.repeat(channels, 1, 1, 1)
        grad_x = F.conv2d(image, sobel_x, padding=1, groups=channels)
        grad_y = F.conv2d(image, sobel_y, padding=1, groups=channels)
        return torch.sqrt(grad_x.square() + grad_y.square() + 1e-6)


class SSIMLoss(nn.Module):
    """Differentiable 1 - SSIM loss computed per channel."""

    def __init__(self, window_size: int = 11, channels: int = 3) -> None:
        super().__init__()
        self.window_size = window_size
        self.channels = channels
        window = torch.ones(channels, 1, window_size, window_size) / (window_size * window_size)
        self.register_buffer("window", window)

    def forward(
        self,
        prediction: torch.Tensor,
        target: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> torch.Tensor:
        channels = prediction.shape[1]
        window = self.window
        if channels != self.channels:
            window = torch.ones(
                channels,
                1,
                self.window_size,
                self.window_size,
                device=prediction.device,
                dtype=prediction.dtype,
            ) / (self.window_size * self.window_size)

        padding = self.window_size // 2
        mu_pred = F.conv2d(prediction, window, padding=padding, groups=channels)
        mu_target = F.conv2d(target, window, padding=padding, groups=channels)
        sigma_pred = F.conv2d(prediction * prediction, window, padding=padding, groups=channels)
        sigma_target = F.conv2d(target * target, window, padding=padding, groups=channels)
        sigma_cross = F.conv2d(prediction * target, window, padding=padding, groups=channels)

        sigma_pred = sigma_pred - mu_pred.square()
        sigma_target = sigma_target - mu_target.square()
        sigma_cross = sigma_cross - mu_pred * mu_target
        c1 = 0.01**2
        c2 = 0.03**2
        numerator = (2 * mu_pred * mu_target + c1) * (2 * sigma_cross + c2)
        denominator = (mu_pred.square() + mu_target.square() + c1) * (
            sigma_pred + sigma_target + c2
        )
        ssim_map = numerator / (denominator + 1e-6)
        loss_map = 1 - ssim_map.mean(dim=1)
        return masked_mean(loss_map, mask)


class ReconstructionLoss(nn.Module):
    def __init__(
        self,
        *,
        l1_weight: float = 1.0,
        spectral_weight: float = 0.2,
        edge_weight: float = 0.1,
        ssim_weight: float = 0.5,
    ) -> None:
        super().__init__()
        self.l1_weight = l1_weight
        self.spectral_weight = spectral_weight
        self.edge_weight = edge_weight
        self.ssim_weight = ssim_weight
        self.spectral = SpectralConsistencyLoss()
        self.edge = EdgeLoss()
        self.ssim = SSIMLoss()

    def forward(
        self,
        prediction: torch.Tensor,
        target: torch.Tensor,
        mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, dict[str, float]]:
        l1 = masked_mean((prediction - target).abs().mean(dim=1), mask)
        spectral = self.spectral(prediction, target, mask)
        edge = self.edge(prediction, target, mask)
        ssim = self.ssim(prediction, target, mask)
        total = (
            self.l1_weight * l1
            + self.spectral_weight * spectral
            + self.edge_weight * edge
            + self.ssim_weight * ssim
        )
        return total, {
            "loss_total": float(total.detach().cpu()),
            "loss_l1": float(l1.detach().cpu()),
            "loss_spectral": float(spectral.detach().cpu()),
            "loss_edge": float(edge.detach().cpu()),
            "loss_ssim": float(ssim.detach().cpu()),
        }


def masked_mean(values: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
    if mask is None:
        return values.mean()

    if mask.ndim == 4:
        mask = mask.squeeze(1)

    mask = mask.float()
    return (values * mask).sum() / mask.sum().clamp_min(1.0)
