from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.inference import InferenceRun
from app.schemas.demo import DemoSampleResponse
from app.services.inference import (
    InferencePipelineResult,
    persist_existing_product,
    run_baseline_inference,
)
from app.services.inference_records import (
    build_inference_response,
    inference_run_to_response,
    persist_inference_result,
)

DEMO_SAMPLE_ID = "synthetic-liss-iv-cloud-demo-v1"
DEMO_CLOUDY_FILENAME = "clearsky-demo-synthetic-liss-iv-cloudy.png"
DEMO_REFERENCE_FILENAME = "clearsky-demo-synthetic-liss-iv-reference.png"


@dataclass
class LocalUploadFile:
    path: Path
    filename: str

    def __post_init__(self) -> None:
        self._file = self.path.open("rb")

    async def read(self, size: int = -1) -> bytes:
        return self._file.read(size)

    async def close(self) -> None:
        self._file.close()


async def get_or_create_demo_sample(
    db: Session,
    *,
    use_cache: bool = True,
) -> DemoSampleResponse:
    ensure_demo_image_files()

    if use_cache:
        cached_run = get_cached_demo_run(db)
        if cached_run is not None:
            return build_demo_response(db, cached_run, cached=True)

    result = await run_demo_pipeline()
    reference_url = await persist_demo_reference(result)
    result.metadata["demo"] = build_demo_metadata(reference_url=reference_url, cached=False)
    persist_inference_result(db, result)
    db.commit()

    return DemoSampleResponse(
        sample_id=DEMO_SAMPLE_ID,
        title="Synthetic LISS-IV-style cloud demo",
        description=demo_description(),
        is_synthetic=True,
        cached=False,
        sample_filename=DEMO_CLOUDY_FILENAME,
        sample_image_url=result.original_image_url,
        reference_image_url=reference_url,
        result=build_inference_response(result),
        explanation=demo_explanation(),
        limitations=demo_limitations(),
    )


def get_cached_demo_run(db: Session) -> InferenceRun | None:
    return db.scalars(
        select(InferenceRun)
        .where(InferenceRun.original_filename == DEMO_CLOUDY_FILENAME)
        .order_by(InferenceRun.created_at.desc())
        .limit(1)
    ).first()


def build_demo_response(
    db: Session,
    inference_run: InferenceRun,
    *,
    cached: bool,
) -> DemoSampleResponse:
    metadata = inference_run.metadata_json or {}
    demo_metadata = metadata.get("demo") or {}
    return DemoSampleResponse(
        sample_id=DEMO_SAMPLE_ID,
        title="Synthetic LISS-IV-style cloud demo",
        description=demo_description(),
        is_synthetic=True,
        cached=cached,
        sample_filename=DEMO_CLOUDY_FILENAME,
        sample_image_url=inference_run.original_image_url,
        reference_image_url=demo_metadata.get("reference_image_url"),
        result=inference_run_to_response(db, inference_run),
        explanation=demo_explanation(),
        limitations=demo_limitations(),
    )


async def run_demo_pipeline() -> InferencePipelineResult:
    cloudy_path, reference_path = ensure_demo_image_files()
    upload = LocalUploadFile(cloudy_path, DEMO_CLOUDY_FILENAME)
    target = LocalUploadFile(reference_path, DEMO_REFERENCE_FILENAME)
    result = await run_baseline_inference(
        upload,
        requested_model="opencv-baseline",
        target_file=target,
    )
    result.metadata["demo"] = build_demo_metadata(reference_url=None, cached=False)
    return result


async def persist_demo_reference(result: InferencePipelineResult) -> str:
    _, reference_path = ensure_demo_image_files()
    product = await persist_existing_product(
        reference_path,
        run_id=result.run_id,
        asset_type="demo_reference_image",
        original_filename=DEMO_REFERENCE_FILENAME,
        content_type="image/png",
    )
    result.products.append(product)
    return product.storage.storage_url


def ensure_demo_image_files() -> tuple[Path, Path]:
    demo_dir = settings.inference_dir / "demo"
    demo_dir.mkdir(parents=True, exist_ok=True)
    cloudy_path = demo_dir / DEMO_CLOUDY_FILENAME
    reference_path = demo_dir / DEMO_REFERENCE_FILENAME

    if cloudy_path.exists() and reference_path.exists():
        return cloudy_path, reference_path

    reference = generate_reference_scene()
    cloudy = apply_clouds_and_shadows(reference)
    write_rgb_png(reference_path, reference)
    write_rgb_png(cloudy_path, cloudy)
    return cloudy_path, reference_path


def generate_reference_scene(width: int = 768, height: int = 512) -> np.ndarray:
    rng = np.random.default_rng(2026)
    y = np.linspace(0, 1, height, dtype=np.float32)[:, None]
    x = np.linspace(0, 1, width, dtype=np.float32)[None, :]

    scene = np.zeros((height, width, 3), dtype=np.float32)
    scene[..., 0] = 74 + 42 * x + 18 * y
    scene[..., 1] = 112 + 36 * y
    scene[..., 2] = 68 + 20 * x

    field_palette = np.array(
        [
            [86, 132, 67],
            [112, 151, 78],
            [142, 139, 82],
            [96, 121, 91],
            [161, 150, 98],
        ],
        dtype=np.float32,
    )
    for row in range(8):
        for col in range(12):
            x0 = col * width // 12
            x1 = (col + 1) * width // 12
            y0 = row * height // 8
            y1 = (row + 1) * height // 8
            color = field_palette[(row * 3 + col) % len(field_palette)]
            color = color + rng.normal(0, 7, size=3)
            cv2.rectangle(scene, (x0 + 2, y0 + 2), (x1 - 3, y1 - 3), color.tolist(), -1)

    water = np.array(
        [
            [0, height - 96],
            [width // 4, height - 128],
            [width // 2, height - 70],
            [width, height - 118],
            [width, height],
            [0, height],
        ],
        dtype=np.int32,
    )
    cv2.fillPoly(scene, [water], color=(44, 82, 104))

    for offset in range(-80, width, 160):
        cv2.line(scene, (offset, 0), (offset + 280, height), (125, 118, 95), 3)

    for _ in range(42):
        center = (int(rng.integers(0, width)), int(rng.integers(0, height)))
        radius = int(rng.integers(3, 11))
        color = tuple((rng.normal([114, 116, 104], [18, 16, 12])).clip(70, 165))
        cv2.circle(scene, center, radius, color, -1)

    noise = rng.normal(0, 5, size=scene.shape)
    scene = np.clip(scene + noise, 0, 255).astype(np.uint8)
    return scene


def apply_clouds_and_shadows(reference: np.ndarray) -> np.ndarray:
    height, width = reference.shape[:2]
    cloudy = reference.astype(np.float32)
    cloud_layer = np.zeros((height, width), dtype=np.uint8)
    shadow_layer = np.zeros((height, width), dtype=np.uint8)

    ellipses = [
        ((230, 150), (150, 52), -12),
        ((380, 215), (185, 68), 14),
        ((560, 130), (132, 44), 8),
        ((610, 305), (170, 54), -18),
    ]

    for center, axes, angle in ellipses:
        cv2.ellipse(cloud_layer, center, axes, angle, 0, 360, 255, -1)
        shadow_center = (center[0] + 42, center[1] + 56)
        cv2.ellipse(shadow_layer, shadow_center, axes, angle, 0, 360, 190, -1)

    cloud_layer = cv2.GaussianBlur(cloud_layer, (45, 45), sigmaX=14)
    shadow_layer = cv2.GaussianBlur(shadow_layer, (39, 39), sigmaX=16)

    shadow_alpha = (shadow_layer.astype(np.float32) / 255.0) * 0.38
    cloudy *= 1 - shadow_alpha[..., None]

    cloud_alpha = (cloud_layer.astype(np.float32) / 255.0) * 0.86
    cloud_color = np.array([242, 244, 238], dtype=np.float32)
    cloudy = cloudy * (1 - cloud_alpha[..., None]) + cloud_color * cloud_alpha[..., None]

    return np.clip(cloudy, 0, 255).astype(np.uint8)


def write_rgb_png(path: Path, image: np.ndarray) -> None:
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(path), bgr)


def build_demo_metadata(*, reference_url: str | None, cached: bool) -> dict:
    return {
        "sample_id": DEMO_SAMPLE_ID,
        "synthetic": True,
        "cached": cached,
        "reference_image_url": reference_url,
        "note": "Generated locally for judge demos; not a real LISS-IV acquisition.",
    }


def demo_description() -> str:
    return (
        "A deterministic satellite-like synthetic scene with agricultural texture, water, "
        "clouds, and shadows. It is provided so judges can run the public deployment "
        "without uploading data or requiring GPU inference."
    )


def demo_explanation() -> list[str]:
    return [
        "The demo uses the same CPU-safe OpenCV baseline pipeline as a normal upload.",
        "Cloud-free reference metrics are computed against the synthetic clear base image.",
        "Advanced model rows are clearly marked as research estimates unless weights exist.",
    ]


def demo_limitations() -> list[str]:
    return [
        "The sample is synthetic and must not be presented as an actual ISRO/NRSC scene.",
        (
            "The demo validates workflow, outputs, reports, and deployment behavior, "
            "not trained model accuracy."
        ),
    ]
