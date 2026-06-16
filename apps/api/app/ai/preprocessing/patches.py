from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PatchWindow:
    y: int
    x: int
    height: int
    width: int


def iter_patch_windows(
    height: int,
    width: int,
    *,
    patch_size: int,
    stride: int | None = None,
) -> Iterator[PatchWindow]:
    stride = stride or patch_size
    y_positions = _positions(height, patch_size, stride)
    x_positions = _positions(width, patch_size, stride)

    for y in y_positions:
        for x in x_positions:
            yield PatchWindow(
                y=y,
                x=x,
                height=min(patch_size, height - y),
                width=min(patch_size, width - x),
            )


def extract_patch(array: np.ndarray, window: PatchWindow, *, patch_size: int) -> np.ndarray:
    patch = array[..., window.y : window.y + window.height, window.x : window.x + window.width]
    pad_h = patch_size - window.height
    pad_w = patch_size - window.width

    if pad_h <= 0 and pad_w <= 0:
        return patch

    pad_width = [(0, 0)] * patch.ndim
    pad_width[-2] = (0, max(0, pad_h))
    pad_width[-1] = (0, max(0, pad_w))
    return np.pad(patch, pad_width, mode="reflect")


def merge_patches(
    patches: list[np.ndarray],
    windows: list[PatchWindow],
    *,
    output_shape: tuple[int, int, int],
) -> np.ndarray:
    channels, height, width = output_shape
    accumulator = np.zeros((channels, height, width), dtype=np.float32)
    weights = np.zeros((1, height, width), dtype=np.float32)

    for patch, window in zip(patches, windows, strict=True):
        cropped = patch[..., : window.height, : window.width]
        accumulator[
            :,
            window.y : window.y + window.height,
            window.x : window.x + window.width,
        ] += cropped
        weights[
            :,
            window.y : window.y + window.height,
            window.x : window.x + window.width,
        ] += 1

    return accumulator / np.maximum(weights, 1.0)


def random_crop(
    arrays: dict[str, np.ndarray | None],
    *,
    patch_size: int,
    rng: np.random.Generator,
) -> dict[str, np.ndarray | None]:
    first_array = next(array for array in arrays.values() if array is not None)
    height, width = first_array.shape[-2:]
    y = int(rng.integers(0, max(1, height - patch_size + 1)))
    x = int(rng.integers(0, max(1, width - patch_size + 1)))
    window = PatchWindow(
        y=y,
        x=x,
        height=min(patch_size, height - y),
        width=min(patch_size, width - x),
    )

    return {
        key: None if value is None else extract_patch(value, window, patch_size=patch_size)
        for key, value in arrays.items()
    }


def center_crop(
    arrays: dict[str, np.ndarray | None],
    *,
    patch_size: int,
) -> dict[str, np.ndarray | None]:
    first_array = next(array for array in arrays.values() if array is not None)
    height, width = first_array.shape[-2:]
    y = max(0, (height - patch_size) // 2)
    x = max(0, (width - patch_size) // 2)
    window = PatchWindow(
        y=y,
        x=x,
        height=min(patch_size, height - y),
        width=min(patch_size, width - x),
    )

    return {
        key: None if value is None else extract_patch(value, window, patch_size=patch_size)
        for key, value in arrays.items()
    }


def _positions(length: int, patch_size: int, stride: int) -> list[int]:
    if length <= patch_size:
        return [0]

    positions = list(range(0, length - patch_size + 1, stride))
    last = length - patch_size
    if positions[-1] != last:
        positions.append(last)

    return positions
