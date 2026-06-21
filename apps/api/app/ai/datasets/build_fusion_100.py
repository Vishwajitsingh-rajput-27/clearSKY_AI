from __future__ import annotations

import argparse
import io
import json
import math
import random
import sys
import time
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

S2_COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"
S1_COLLECTION = "COPERNICUS/S1_GRD"
DEM_IMAGE = "USGS/SRTMGL1_003"

S2_RGB_BANDS = ["B4", "B3", "B2"]
S2_FUSION_BANDS = ["B2", "B3", "B4", "B5", "B6", "B7", "B8", "B8A", "B11", "B12"]

DEFAULT_REGIONS = [
    {"name": "punjab_agriculture", "lat": 30.7333, "lon": 76.7794},
    {"name": "gujarat_coast", "lat": 22.4707, "lon": 70.0577},
    {"name": "assam_floodplain", "lat": 26.2006, "lon": 92.9376},
    {"name": "karnataka_agriculture", "lat": 12.9141, "lon": 77.2410},
    {"name": "rajasthan_drylands", "lat": 26.9124, "lon": 75.7873},
    {"name": "uttarakhand_hills", "lat": 30.3165, "lon": 78.0322},
    {"name": "odisha_coast", "lat": 20.2961, "lon": 85.8245},
    {"name": "telangana_mixed", "lat": 17.3850, "lon": 78.4867},
    {"name": "kerala_vegetation", "lat": 10.8505, "lon": 76.2711},
    {"name": "maharashtra_urban_agri", "lat": 18.5204, "lon": 73.8567},
]


@dataclass(frozen=True)
class BuilderConfig:
    project: str | None = None
    output_dir: Path = Path("data")
    target_count: int = 100
    image_size: int = 512
    chip_size_km: float = 5.12
    start_date: str = "2022-01-01"
    end_date: str = "2025-12-31"
    max_cloud_percent: float = 10.0
    temporal_min_days: int = 20
    temporal_max_days: int = 120
    s1_window_days: int = 18
    min_mask_percent: float = 5.0
    max_mask_percent: float = 70.0
    max_candidates_per_aoi: int = 8
    download_pause_seconds: float = 0.5
    skip_existing: bool = True
    dry_run: bool = False
    seed: int = 2026
    regions: list[dict[str, float | str]] = field(default_factory=lambda: DEFAULT_REGIONS)


@dataclass(frozen=True)
class Candidate:
    image: Any
    image_id: str
    acquired: date
    cloud_percent: float


def main() -> None:
    args = parse_args()
    config = load_config(args)
    initialize_earth_engine(config.project, authenticate=args.authenticate)

    random.seed(config.seed)
    np.random.seed(config.seed)
    rows = build_dataset(config)

    if not config.dry_run:
        write_manifests(rows, config.output_dir)

    print(
        json.dumps(
            {
                "created_or_reused_scenes": len(rows),
                "output_dir": str(config.output_dir),
                "dry_run": config.dry_run,
            },
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a 100-scene multi-sensor fusion dataset from Earth Engine."
    )
    parser.add_argument("--config", default="configs/fusion_dataset_100.json")
    parser.add_argument("--project", default=None, help="Google Cloud project for Earth Engine.")
    parser.add_argument("--output-dir", default=None)
    parser.add_argument("--target-count", type=int, default=None)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--image-size", type=int, default=None)
    parser.add_argument("--chip-size-km", type=float, default=None)
    parser.add_argument("--max-cloud-percent", type=float, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--authenticate", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> BuilderConfig:
    payload: dict[str, Any] = {}
    config_path = Path(args.config)
    if config_path.exists():
        payload = json.loads(config_path.read_text(encoding="utf-8"))

    overrides = {
        "project": args.project,
        "output_dir": args.output_dir,
        "target_count": args.target_count,
        "start_date": args.start_date,
        "end_date": args.end_date,
        "image_size": args.image_size,
        "chip_size_km": args.chip_size_km,
        "max_cloud_percent": args.max_cloud_percent,
    }
    payload.update({key: value for key, value in overrides.items() if value is not None})

    if args.dry_run:
        payload["dry_run"] = True
    if args.overwrite:
        payload["skip_existing"] = False

    if "output_dir" in payload:
        payload["output_dir"] = Path(payload["output_dir"])

    return BuilderConfig(**payload)


def initialize_earth_engine(project: str | None, *, authenticate: bool) -> None:
    try:
        import ee
    except ImportError as exc:
        raise SystemExit(
            "Missing earthengine-api. Install dataset tools with: "
            "pip install -r requirements-dataset.txt"
        ) from exc

    if authenticate:
        ee.Authenticate()

    try:
        ee.Initialize(project=project) if project else ee.Initialize()
    except Exception as exc:
        raise SystemExit(
            "Earth Engine is not initialized. Run once with --authenticate and pass "
            "--project YOUR_GOOGLE_CLOUD_PROJECT if your account requires it."
        ) from exc


def build_dataset(config: BuilderConfig) -> list[dict[str, Any]]:
    import ee

    raw_dir = config.output_dir / "raw"
    manifest_dir = config.output_dir / "manifests"
    if not config.dry_run:
        raw_dir.mkdir(parents=True, exist_ok=True)
        manifest_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    aoi_index = 0
    attempts = 0
    max_attempts = max(config.target_count * 20, 500)

    while len(rows) < config.target_count and attempts < max_attempts:
        attempts += 1
        region = config.regions[aoi_index % len(config.regions)]
        chip = chip_for_region(region, aoi_index, config)
        aoi_index += 1

        scene_id = f"scene-{len(rows) + 1:03d}"
        scene_dir = raw_dir / scene_id

        if config.skip_existing and is_complete_scene(scene_dir):
            rows.append(manifest_row(scene_id))
            continue

        geometry = ee.Geometry.Rectangle(chip["bounds"])
        candidates = find_s2_candidates(geometry, config)
        if not candidates:
            log(f"skip {scene_id}: no low-cloud Sentinel-2 target for {chip['region_name']}")
            continue

        built = False
        for candidate in candidates:
            before = find_temporal_ref(geometry, candidate.acquired, before=True, config=config)
            after = find_temporal_ref(geometry, candidate.acquired, before=False, config=config)
            if before is None or after is None:
                continue

            s1 = build_s1_image(geometry, candidate.acquired, config)
            if s1 is None:
                continue

            if config.dry_run:
                rows.append(manifest_row(scene_id))
                log(
                    f"planned {scene_id}: {chip['region_name']} {candidate.acquired.isoformat()} "
                    f"cloud={candidate.cloud_percent:.2f}%"
                )
                built = True
                break

            scene_dir.mkdir(parents=True, exist_ok=True)
            try:
                build_scene_files(
                    scene_id=scene_id,
                    scene_dir=scene_dir,
                    geometry=geometry,
                    target=candidate,
                    before=before,
                    after=after,
                    s1=s1,
                    chip=chip,
                    config=config,
                )
            except Exception as exc:
                log(f"skip {scene_id}: failed download/build ({exc})")
                remove_incomplete_scene(scene_dir)
                continue

            if not is_complete_scene(scene_dir):
                log(f"skip {scene_id}: scene failed QA")
                remove_incomplete_scene(scene_dir)
                continue

            rows.append(manifest_row(scene_id))
            log(f"built {scene_id}: {chip['region_name']} {candidate.acquired.isoformat()}")
            built = True
            time.sleep(config.download_pause_seconds)
            break

        if not built:
            log(f"skip {scene_id}: no complete matched sensor pack for {chip['region_name']}")

    if len(rows) < config.target_count:
        raise SystemExit(
            f"Only built {len(rows)} scenes after {attempts} attempts. "
            "Widen date/cloud filters or add more regions."
        )

    return rows


def chip_for_region(
    region: dict[str, float | str],
    index: int,
    config: BuilderConfig,
) -> dict[str, Any]:
    lat = float(region["lat"])
    lon = float(region["lon"])
    offsets = spiral_offsets()
    offset_lat_km, offset_lon_km = offsets[index % len(offsets)]
    center_lat = lat + offset_lat_km / 111.32
    center_lon = lon + offset_lon_km / max(1e-6, 111.32 * math.cos(math.radians(lat)))
    half_km = config.chip_size_km / 2
    lat_delta = half_km / 111.32
    lon_delta = half_km / max(1e-6, 111.32 * math.cos(math.radians(center_lat)))
    return {
        "region_name": str(region["name"]),
        "center_lat": center_lat,
        "center_lon": center_lon,
        "bounds": [
            center_lon - lon_delta,
            center_lat - lat_delta,
            center_lon + lon_delta,
            center_lat + lat_delta,
        ],
    }


def spiral_offsets() -> list[tuple[float, float]]:
    offsets = [(0.0, 0.0)]
    step = 8.0
    for radius in range(1, 6):
        distance = radius * step
        offsets.extend(
            [
                (distance, 0.0),
                (-distance, 0.0),
                (0.0, distance),
                (0.0, -distance),
                (distance, distance),
                (distance, -distance),
                (-distance, distance),
                (-distance, -distance),
            ]
        )
    return offsets


def find_s2_candidates(geometry: Any, config: BuilderConfig) -> list[Candidate]:
    import ee

    collection = (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(geometry)
        .filterDate(config.start_date, config.end_date)
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", config.max_cloud_percent))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
        .limit(config.max_candidates_per_aoi)
    )
    return collection_candidates(collection)


def find_temporal_ref(
    geometry: Any,
    target_date: date,
    *,
    before: bool,
    config: BuilderConfig,
) -> Candidate | None:
    import ee

    if before:
        start = target_date - timedelta(days=config.temporal_max_days)
        end = target_date - timedelta(days=config.temporal_min_days)
    else:
        start = target_date + timedelta(days=config.temporal_min_days)
        end = target_date + timedelta(days=config.temporal_max_days)

    collection = (
        ee.ImageCollection(S2_COLLECTION)
        .filterBounds(geometry)
        .filterDate(start.isoformat(), end.isoformat())
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", config.max_cloud_percent))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
        .limit(1)
    )
    candidates = collection_candidates(collection)
    return candidates[0] if candidates else None


def collection_candidates(collection: Any) -> list[Candidate]:
    import ee

    size = int(collection.size().getInfo() or 0)
    if size == 0:
        return []

    items = collection.toList(size)
    candidates: list[Candidate] = []
    for index in range(size):
        ee_image = ee.Image(items.get(index))
        props = ee_image.toDictionary(["system:id", "system:time_start", "CLOUDY_PIXEL_PERCENTAGE"]).getInfo()
        acquired = datetime.utcfromtimestamp(props["system:time_start"] / 1000).date()
        candidates.append(
            Candidate(
                image=ee_image,
                image_id=str(props.get("system:id", "")),
                acquired=acquired,
                cloud_percent=float(props.get("CLOUDY_PIXEL_PERCENTAGE", 0.0)),
            )
        )
    return candidates


def build_s1_image(geometry: Any, target_date: date, config: BuilderConfig) -> Any | None:
    import ee

    start = (target_date - timedelta(days=config.s1_window_days)).isoformat()
    end = (target_date + timedelta(days=config.s1_window_days)).isoformat()
    collection = (
        ee.ImageCollection(S1_COLLECTION)
        .filterBounds(geometry)
        .filterDate(start, end)
        .filter(ee.Filter.eq("instrumentMode", "IW"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
        .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH"))
        .select(["VV", "VH"])
    )
    if int(collection.size().getInfo() or 0) == 0:
        return None

    return collection.median().unitScale(-25, 5).clamp(0, 1).toFloat()


def build_scene_files(
    *,
    scene_id: str,
    scene_dir: Path,
    geometry: Any,
    target: Candidate,
    before: Candidate,
    after: Candidate,
    s1: Any,
    chip: dict[str, Any],
    config: BuilderConfig,
) -> None:
    import ee

    clear_tif = scene_dir / "_clear_rgb.tif"
    before_tif = scene_dir / "_before_rgb.tif"
    after_tif = scene_dir / "_after_rgb.tif"

    target_rgb = target.image.select(S2_RGB_BANDS).divide(10000).clamp(0, 1).toFloat()
    before_rgb = before.image.select(S2_RGB_BANDS).divide(10000).clamp(0, 1).toFloat()
    after_rgb = after.image.select(S2_RGB_BANDS).divide(10000).clamp(0, 1).toFloat()
    s2_stack = target.image.select(S2_FUSION_BANDS).divide(10000).clamp(0, 1).toFloat()
    dem = ee.Image(DEM_IMAGE).select("elevation").unitScale(-100, 5000).clamp(0, 1).toFloat()

    download_ee_tiff(target_rgb, geometry, clear_tif, config.image_size)
    download_ee_tiff(before_rgb, geometry, before_tif, config.image_size)
    download_ee_tiff(after_rgb, geometry, after_tif, config.image_size)
    download_ee_tiff(s1, geometry, scene_dir / "sentinel1.tif", config.image_size)
    download_ee_tiff(s2_stack, geometry, scene_dir / "sentinel2.tif", config.image_size)
    download_ee_tiff(dem, geometry, scene_dir / "dem.tif", config.image_size)

    clear = rgb_tif_to_png(clear_tif, scene_dir / "clear.png")
    rgb_tif_to_png(before_tif, scene_dir / "ref-before.png")
    rgb_tif_to_png(after_tif, scene_dir / "ref-after.png")
    mask_percent = write_synthetic_cloud_pair(
        clear,
        cloudy_path=scene_dir / "cloudy.png",
        mask_path=scene_dir / "cloud_mask.png",
        config=config,
        seed=stable_seed(scene_id, config.seed),
    )

    for temporary in (clear_tif, before_tif, after_tif):
        temporary.unlink(missing_ok=True)

    metadata = {
        "scene_id": scene_id,
        "source": "google-earth-engine",
        "optical_proxy": "sentinel-2-as-liss4-like-input",
        "target_collection": S2_COLLECTION,
        "sentinel1_collection": S1_COLLECTION,
        "dem_image": DEM_IMAGE,
        "target_image_id": target.image_id,
        "target_date": target.acquired.isoformat(),
        "target_cloud_percent": target.cloud_percent,
        "ref_before_image_id": before.image_id,
        "ref_before_date": before.acquired.isoformat(),
        "ref_after_image_id": after.image_id,
        "ref_after_date": after.acquired.isoformat(),
        "synthetic_invalid_mask_percent": mask_percent,
        "mask_includes_shadow": True,
        **chip,
    }
    (scene_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def download_ee_tiff(image: Any, geometry: Any, destination: Path, image_size: int) -> None:
    params = {
        "region": geometry,
        "dimensions": f"{image_size}x{image_size}",
        "format": "GEO_TIFF",
        "filePerBand": False,
    }
    url = image.getDownloadURL(params)
    with urllib.request.urlopen(url, timeout=300) as response:
        payload = response.read()

    destination.parent.mkdir(parents=True, exist_ok=True)
    if payload[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            tif_names = [name for name in archive.namelist() if name.lower().endswith((".tif", ".tiff"))]
            if len(tif_names) != 1:
                raise RuntimeError(f"Expected one GeoTIFF in Earth Engine zip, found {len(tif_names)}")
            destination.write_bytes(archive.read(tif_names[0]))
    else:
        destination.write_bytes(payload)


def rgb_tif_to_png(tif_path: Path, png_path: Path) -> np.ndarray:
    import rasterio

    with rasterio.open(tif_path) as dataset:
        array = dataset.read([1, 2, 3]).astype(np.float32)

    rgb = np.moveaxis(array, 0, -1)
    rgb = np.nan_to_num(rgb, nan=0.0, posinf=1.0, neginf=0.0)
    rgb = (rgb / 0.30 * 255.0).clip(0, 255).astype(np.uint8)
    Image.fromarray(rgb, mode="RGB").save(png_path)
    return rgb


def write_synthetic_cloud_pair(
    clear_rgb: np.ndarray,
    *,
    cloudy_path: Path,
    mask_path: Path,
    config: BuilderConfig,
    seed: int,
) -> float:
    import cv2

    rng = np.random.default_rng(seed)
    height, width = clear_rgb.shape[:2]

    for _ in range(12):
        cloud_layer = np.zeros((height, width), dtype=np.uint8)
        blob_count = int(rng.integers(4, 10))
        for _blob in range(blob_count):
            center = (int(rng.integers(0, width)), int(rng.integers(0, height)))
            axes = (
                int(rng.integers(width * 0.08, width * 0.24)),
                int(rng.integers(height * 0.04, height * 0.16)),
            )
            angle = float(rng.uniform(-35, 35))
            cv2.ellipse(cloud_layer, center, axes, angle, 0, 360, 255, -1)

        blur_kernel = max(21, int(min(width, height) * 0.08) | 1)
        soft_cloud = cv2.GaussianBlur(cloud_layer, (blur_kernel, blur_kernel), sigmaX=blur_kernel / 4)
        cloud_mask = soft_cloud > int(rng.integers(70, 130))
        shadow_mask = shift_mask(cloud_mask, dx=int(width * 0.05), dy=int(height * 0.06))
        invalid_mask = np.logical_or(cloud_mask, shadow_mask)
        coverage = float(invalid_mask.mean() * 100)
        if config.min_mask_percent <= coverage <= config.max_mask_percent:
            break
    else:
        raise RuntimeError("Could not synthesize cloud mask within configured coverage bounds")

    clear_float = clear_rgb.astype(np.float32)
    cloud_alpha = (soft_cloud.astype(np.float32) / 255.0 * rng.uniform(0.62, 0.90))[..., None]
    shadow_alpha = shadow_mask.astype(np.float32)[..., None] * rng.uniform(0.22, 0.42)
    cloud_color = np.array([242, 244, 238], dtype=np.float32)

    cloudy = clear_float * (1.0 - shadow_alpha)
    cloudy = cloudy * (1.0 - cloud_alpha) + cloud_color * cloud_alpha
    cloudy = np.clip(cloudy, 0, 255).astype(np.uint8)

    Image.fromarray(cloudy, mode="RGB").save(cloudy_path)
    Image.fromarray((invalid_mask.astype(np.uint8) * 255), mode="L").save(mask_path)
    return coverage


def shift_mask(mask: np.ndarray, *, dx: int, dy: int) -> np.ndarray:
    shifted = np.zeros_like(mask)
    source_y0 = max(0, -dy)
    source_y1 = mask.shape[0] - max(0, dy)
    source_x0 = max(0, -dx)
    source_x1 = mask.shape[1] - max(0, dx)
    target_y0 = max(0, dy)
    target_y1 = target_y0 + (source_y1 - source_y0)
    target_x0 = max(0, dx)
    target_x1 = target_x0 + (source_x1 - source_x0)
    shifted[target_y0:target_y1, target_x0:target_x1] = mask[source_y0:source_y1, source_x0:source_x1]
    return shifted


def is_complete_scene(scene_dir: Path) -> bool:
    required = [
        "cloudy.png",
        "cloud_mask.png",
        "clear.png",
        "sentinel1.tif",
        "sentinel2.tif",
        "dem.tif",
        "ref-before.png",
        "ref-after.png",
        "metadata.json",
    ]
    if not all((scene_dir / filename).exists() for filename in required):
        return False

    try:
        validate_scene_dimensions(scene_dir)
    except Exception:
        return False
    return True


def validate_scene_dimensions(scene_dir: Path) -> None:
    import rasterio

    clear_size = Image.open(scene_dir / "clear.png").size
    for png_name in ("cloudy.png", "cloud_mask.png", "ref-before.png", "ref-after.png"):
        if Image.open(scene_dir / png_name).size != clear_size:
            raise ValueError(f"{png_name} dimensions do not match clear.png")

    expected_counts = {"sentinel1.tif": 2, "sentinel2.tif": 10, "dem.tif": 1}
    for tif_name, expected_count in expected_counts.items():
        with rasterio.open(scene_dir / tif_name) as dataset:
            if dataset.width != clear_size[0] or dataset.height != clear_size[1]:
                raise ValueError(f"{tif_name} dimensions do not match clear.png")
            if dataset.count < expected_count:
                raise ValueError(f"{tif_name} has {dataset.count} bands, expected {expected_count}")


def remove_incomplete_scene(scene_dir: Path) -> None:
    if not scene_dir.exists():
        return
    for path in sorted(scene_dir.rglob("*"), reverse=True):
        if path.is_file():
            path.unlink(missing_ok=True)
        elif path.is_dir():
            path.rmdir()
    scene_dir.rmdir()


def manifest_row(scene_id: str) -> dict[str, Any]:
    base = f"../raw/{scene_id}"
    return {
        "scene_id": scene_id,
        "cloudy_liss4": f"{base}/cloudy.png",
        "cloud_mask": f"{base}/cloud_mask.png",
        "target": f"{base}/clear.png",
        "sentinel1": f"{base}/sentinel1.tif",
        "sentinel2": f"{base}/sentinel2.tif",
        "dem": f"{base}/dem.tif",
        "temporal_refs": [
            f"{base}/ref-before.png",
            f"{base}/ref-after.png",
        ],
    }


def write_manifests(rows: list[dict[str, Any]], output_dir: Path) -> None:
    manifest_dir = output_dir / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)

    train_end = int(len(rows) * 0.8)
    val_end = train_end + int(len(rows) * 0.1)
    splits = {
        "train": rows[:train_end],
        "val": rows[train_end:val_end],
        "test": rows[val_end:],
    }
    for split, split_rows in splits.items():
        (manifest_dir / f"{split}.json").write_text(
            json.dumps(split_rows, indent=2),
            encoding="utf-8",
        )


def stable_seed(scene_id: str, base_seed: int) -> int:
    return base_seed + sum(ord(character) for character in scene_id)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
