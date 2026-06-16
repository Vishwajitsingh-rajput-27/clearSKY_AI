from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class TileWindow:
    y: int
    x: int
    height: int
    width: int


def iter_tiles(
    height: int,
    width: int,
    *,
    tile_size: int = 512,
    overlap: int = 32,
) -> Iterator[TileWindow]:
    stride = max(1, tile_size - overlap)
    for y in axis_positions(height, tile_size, stride):
        for x in axis_positions(width, tile_size, stride):
            yield TileWindow(
                y=y,
                x=x,
                height=min(tile_size, height - y),
                width=min(tile_size, width - x),
            )


def extract_tile(image: np.ndarray, window: TileWindow) -> np.ndarray:
    return image[window.y : window.y + window.height, window.x : window.x + window.width].copy()


def merge_tiles(
    tiles: list[np.ndarray],
    windows: list[TileWindow],
    *,
    output_shape: tuple[int, int, int],
) -> np.ndarray:
    height, width, channels = output_shape
    accumulator = np.zeros((height, width, channels), dtype=np.float32)
    weights = np.zeros((height, width, 1), dtype=np.float32)

    for tile, window in zip(tiles, windows, strict=True):
        cropped = tile[: window.height, : window.width]
        accumulator[
            window.y : window.y + window.height,
            window.x : window.x + window.width,
        ] += cropped.astype(np.float32)
        weights[
            window.y : window.y + window.height,
            window.x : window.x + window.width,
        ] += 1.0

    merged = accumulator / np.maximum(weights, 1.0)
    return merged.round().clip(0, 255).astype(np.uint8)


def process_large_image_in_tiles(
    image: np.ndarray,
    processor,
    *,
    tile_size: int = 512,
    overlap: int = 32,
) -> np.ndarray:
    height, width = image.shape[:2]
    windows = list(iter_tiles(height, width, tile_size=tile_size, overlap=overlap))
    processed_tiles = [processor(extract_tile(image, window)) for window in windows]
    return merge_tiles(processed_tiles, windows, output_shape=image.shape)


def axis_positions(length: int, tile_size: int, stride: int) -> list[int]:
    if length <= tile_size:
        return [0]

    positions = list(range(0, length - tile_size + 1, stride))
    last = length - tile_size
    if positions[-1] != last:
        positions.append(last)

    return positions
