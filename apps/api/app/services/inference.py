import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID, uuid4

import cv2
import numpy as np
from fastapi import UploadFile
from PIL import Image

from app.ai.inference.predictor import run_weighted_reconstruction_if_available
from app.core.config import settings
from app.core.exceptions import AppError
from app.services.evaluation_engine import benchmark_models, evaluate_reconstruction
from app.services.geotiff_reader import RasterReadResult, read_raster
from app.services.geotiff_writer import (
    create_qgis_output_folder,
    export_analysis_ready_geotiff,
    scale_transform_for_resize,
)
from app.services.recommendation_engine import build_ai_recommendations
from app.services.report_generator import generate_evaluation_report
from app.services.storage import StorageResult, persist_upload
from app.services.tiling_service import iter_tiles
from app.services.uploads import StoredUpload
from app.utils.files import get_original_filename, safe_filename

Image.MAX_IMAGE_PIXELS = settings.max_inference_pixels

BASELINE_ALIASES = {
    "baseline",
    "baseline-opencv",
    "opencv",
    "opencv-baseline",
    "opencv-inpaint",
    "opencv-inpaint-telea",
}


@dataclass(frozen=True)
class InferenceProduct:
    asset_id: UUID
    asset_type: str
    safe_filename: str
    stored: StoredUpload
    storage: StorageResult


@dataclass(frozen=True)
class InferencePipelineResult:
    run_id: UUID
    requested_model: str
    used_model: str
    fallback_used: bool
    original_filename: str
    original_image_url: str
    cloud_mask_url: str
    shadow_mask_url: str
    reconstructed_image_url: str
    difference_map_url: str
    attention_map_url: str | None
    confidence_map_url: str | None
    analysis_geotiff_url: str | None
    qgis_manifest_url: str | None
    cloud_coverage_percent: float
    shadow_coverage_percent: float
    quality_score: float
    reconstruction_confidence_score: float
    processing_time_seconds: float
    metrics: dict
    metadata: dict
    evaluation_mode: str
    evaluation_metrics: dict[str, float | None]
    evaluation_explanation: dict[str, str]
    benchmark_rows: list[dict]
    recommendations: list[dict]
    evaluation_report_url: str | None
    evaluation_report_markdown_url: str | None
    products: list[InferenceProduct]


async def run_baseline_inference(
    upload_file: UploadFile,
    *,
    requested_model: str,
    target_file: UploadFile | None = None,
) -> InferencePipelineResult:
    started = time.perf_counter()
    run_id = uuid4()
    working_dir = settings.inference_dir / str(run_id)
    working_dir.mkdir(parents=True, exist_ok=True)

    original_filename = get_original_filename(upload_file.filename)
    validate_inference_extension(original_filename)
    uploaded_path = await save_inference_upload(upload_file, working_dir, original_filename)
    requested = requested_model.strip() or "opencv-baseline"

    raster = read_satellite_image(uploaded_path)
    image_metadata = raster.metadata
    rgb = raster.rgb
    original_height, original_width = rgb.shape[:2]
    rgb = resize_for_cpu(rgb)
    processed_height, processed_width = rgb.shape[:2]
    target_rgb, target_metadata = await load_optional_target(
        target_file,
        working_dir=working_dir,
        output_size=(processed_width, processed_height),
    )

    cloud_mask = clean_mask(generate_cloud_mask(rgb))
    shadow_mask = clean_mask(generate_shadow_mask(rgb, cloud_mask))
    invalid_mask = cv2.bitwise_or(cloud_mask, shadow_mask)

    ai_attempt = run_weighted_reconstruction_if_available(
        rgb=rgb,
        invalid_mask=invalid_mask,
        requested_model=requested,
        model_dir=settings.model_dir,
        device="cpu",
    )
    if ai_attempt.prediction:
        reconstructed = ai_attempt.prediction.reconstructed_rgb
        used_model = ai_attempt.prediction.used_model
        fallback_used = False
    else:
        reconstructed = reconstruct_image(rgb, invalid_mask)
        used_model = "opencv-inpaint-telea"
        fallback_used = requested.lower() not in BASELINE_ALIASES

    enhanced = enhance_image(reconstructed)
    difference_map, mean_absolute_difference = generate_difference_map(rgb, enhanced)
    attention_map = generate_attention_map(
        rgb=rgb,
        cloud_mask=cloud_mask,
        shadow_mask=shadow_mask,
        difference_map=difference_map,
    )
    confidence_map, reconstruction_confidence = generate_confidence_map(
        invalid_mask=invalid_mask,
        difference_map=difference_map,
        cloud_coverage=mask_percent(cloud_mask),
        shadow_coverage=mask_percent(shadow_mask),
        mean_absolute_difference=mean_absolute_difference,
        fallback_used=fallback_used,
    )

    cloud_coverage = mask_percent(cloud_mask)
    shadow_coverage = mask_percent(shadow_mask)
    mask_coverage = mask_percent(invalid_mask)
    quality_score = calculate_quality_score(
        cloud_coverage=cloud_coverage,
        shadow_coverage=shadow_coverage,
        mask_coverage=mask_coverage,
        mean_absolute_difference=mean_absolute_difference,
    )

    outputs = {
        "original_image": rgb,
        "cloud_mask": mask_to_rgb(cloud_mask),
        "shadow_mask": mask_to_rgb(shadow_mask),
        "reconstructed_image": enhanced,
        "difference_map": difference_map,
        "attention_map": attention_map,
        "confidence_map": confidence_map,
    }

    products: list[InferenceProduct] = []
    urls: dict[str, str] = {}

    for asset_type, image in outputs.items():
        product = await save_and_persist_product(
            image,
            run_id=run_id,
            asset_type=asset_type,
            working_dir=working_dir,
        )
        products.append(product)
        urls[asset_type] = product.storage.storage_url

    geospatial_exports = export_geospatial_outputs(
        enhanced,
        working_dir=working_dir,
        raster=raster,
        metadata=image_metadata,
        product_urls=urls,
        original_width=original_width,
        original_height=original_height,
    )

    if geospatial_exports["analysis_geotiff_path"]:
        product = await persist_existing_product(
            geospatial_exports["analysis_geotiff_path"],
            run_id=run_id,
            asset_type="analysis_geotiff",
            original_filename="analysis_ready_reconstruction.tif",
            content_type="image/tiff",
        )
        products.append(product)
        urls["analysis_geotiff"] = product.storage.storage_url

    if geospatial_exports["qgis_manifest_path"]:
        product = await persist_existing_product(
            geospatial_exports["qgis_manifest_path"],
            run_id=run_id,
            asset_type="qgis_manifest",
            original_filename="manifest.json",
            content_type="application/json",
        )
        products.append(product)
        urls["qgis_manifest"] = product.storage.storage_url

    processing_time = time.perf_counter() - started
    evaluation = evaluate_reconstruction(
        original_rgb=rgb,
        reconstructed_rgb=enhanced,
        cloud_mask=cloud_mask,
        shadow_mask=shadow_mask,
        target_rgb=target_rgb,
        processing_time_seconds=processing_time,
    )
    benchmark_rows = benchmark_models(
        base_metrics=evaluation.metrics,
        processing_time_seconds=processing_time,
        requested_model=requested,
        used_model=used_model,
        fallback_used=fallback_used,
    )

    metrics = {
        "cloud_coverage_percent": round(cloud_coverage, 3),
        "shadow_coverage_percent": round(shadow_coverage, 3),
        "quality_score": round(quality_score, 3),
        "reconstruction_confidence_score": round(reconstruction_confidence, 3),
        "mean_absolute_difference": round(mean_absolute_difference, 3),
        "mask_coverage_percent": round(mask_coverage, 3),
        "input_width": original_width,
        "input_height": original_height,
        "processed_width": processed_width,
        "processed_height": processed_height,
        "tile_count": geospatial_exports["tile_count"],
    }
    metadata = {
        **image_metadata,
        "input_path": str(uploaded_path),
        "cpu_resized": (original_width, original_height) != (processed_width, processed_height),
        "thresholds": {
            "cloud_brightness": 205,
            "cloud_saturation": 90,
            "shadow_brightness": 75,
        },
        "ai_inference": {
            "fallback_reason": ai_attempt.fallback_reason,
            **ai_attempt.metadata,
            **(ai_attempt.prediction.metadata if ai_attempt.prediction else {}),
        },
        "geospatial_export": {
            "analysis_geotiff_created": geospatial_exports["analysis_geotiff_path"] is not None,
            "qgis_folder": geospatial_exports["qgis_folder"],
            "qgis_manifest_created": geospatial_exports["qgis_manifest_path"] is not None,
            "fallback_reason": geospatial_exports["fallback_reason"],
        },
        "evaluation": {
            "mode": evaluation.metric_mode,
            "target_available": target_rgb is not None,
            "target_metadata": target_metadata,
        },
    }
    recommendations = build_ai_recommendations(
        metrics=metrics,
        metadata=image_metadata,
        requested_model=requested,
        used_model=used_model,
        fallback_used=fallback_used,
    )
    metadata["explainability"] = {
        "attention_map": "Proxy attention derived from cloud, shadow, edge, and change signals.",
        "confidence_map": "Proxy confidence derived from mask distance and reconstruction delta.",
        "reconstruction_confidence_score": round(reconstruction_confidence, 3),
    }
    metadata["recommendations"] = recommendations

    report_json_url = None
    report_markdown_url = None
    report_json_path, report_markdown_path = generate_evaluation_report(
        report_dir=working_dir / "reports",
        inference_run_id=run_id,
        original_filename=original_filename,
        requested_model=requested,
        used_model=used_model,
        metric_mode=evaluation.metric_mode,
        metrics=evaluation.metrics,
        benchmark_rows=benchmark_rows,
        metadata=metadata,
    )
    report_json_product = await persist_existing_product(
        report_json_path,
        run_id=run_id,
        asset_type="evaluation_report_json",
        original_filename="evaluation_report.json",
        content_type="application/json",
    )
    products.append(report_json_product)
    report_json_url = report_json_product.storage.storage_url

    report_markdown_product = await persist_existing_product(
        report_markdown_path,
        run_id=run_id,
        asset_type="evaluation_report_markdown",
        original_filename="evaluation_report.md",
        content_type="text/markdown",
    )
    products.append(report_markdown_product)
    report_markdown_url = report_markdown_product.storage.storage_url

    return InferencePipelineResult(
        run_id=run_id,
        requested_model=requested,
        used_model=used_model,
        fallback_used=fallback_used,
        original_filename=original_filename,
        original_image_url=urls["original_image"],
        cloud_mask_url=urls["cloud_mask"],
        shadow_mask_url=urls["shadow_mask"],
        reconstructed_image_url=urls["reconstructed_image"],
        difference_map_url=urls["difference_map"],
        attention_map_url=urls.get("attention_map"),
        confidence_map_url=urls.get("confidence_map"),
        analysis_geotiff_url=urls.get("analysis_geotiff"),
        qgis_manifest_url=urls.get("qgis_manifest"),
        cloud_coverage_percent=round(cloud_coverage, 3),
        shadow_coverage_percent=round(shadow_coverage, 3),
        quality_score=round(quality_score, 3),
        reconstruction_confidence_score=round(reconstruction_confidence, 3),
        processing_time_seconds=round(processing_time, 3),
        metrics=metrics,
        metadata=metadata,
        evaluation_mode=evaluation.metric_mode,
        evaluation_metrics=evaluation.metrics,
        evaluation_explanation=evaluation.explanation,
        benchmark_rows=benchmark_rows,
        recommendations=recommendations,
        evaluation_report_url=report_json_url,
        evaluation_report_markdown_url=report_markdown_url,
        products=products,
    )


def validate_inference_extension(filename: str) -> None:
    suffix = Path(filename).suffix.lower()

    if suffix not in settings.allowed_inference_extensions:
        raise AppError(
            "Unsupported inference image type.",
            code="unsupported_inference_image_type",
            details={
                "filename": filename,
                "allowed_extensions": settings.allowed_inference_extensions,
            },
        )


async def save_inference_upload(
    upload_file: UploadFile,
    working_dir: Path,
    original_filename: str,
) -> Path:
    filename = safe_inference_filename(original_filename)
    upload_path = working_dir / filename
    file_size = 0

    try:
        with upload_path.open("wb") as target:
            while chunk := await upload_file.read(1024 * 1024):
                file_size += len(chunk)

                if file_size > settings.max_upload_bytes:
                    raise AppError(
                        "Uploaded file exceeds configured size limit.",
                        code="upload_too_large",
                        details={"max_upload_size_mb": settings.max_upload_size_mb},
                    )

                target.write(chunk)
    finally:
        await upload_file.close()

    if file_size == 0:
        upload_path.unlink(missing_ok=True)
        raise AppError("Uploaded file is empty.", code="empty_upload")

    return upload_path


def safe_inference_filename(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    validate_inference_extension(filename)
    temporary_settings_extensions = settings.allowed_upload_extensions

    if suffix in temporary_settings_extensions:
        return safe_filename(filename)

    stem = Path(filename).stem
    sanitized = "".join(character if character.isalnum() else "-" for character in stem)
    sanitized = sanitized.strip("-").lower() or "image"
    return f"{sanitized}-{uuid4().hex[:12]}{suffix}"


def read_satellite_image(path: Path) -> RasterReadResult:
    return read_raster(path)


async def load_optional_target(
    target_file: UploadFile | None,
    *,
    working_dir: Path,
    output_size: tuple[int, int],
) -> tuple[np.ndarray | None, dict | None]:
    if target_file is None or not target_file.filename:
        return None, None

    target_filename = get_original_filename(target_file.filename)
    validate_inference_extension(target_filename)
    target_path = await save_inference_upload(target_file, working_dir, target_filename)
    target_raster = read_satellite_image(target_path)
    target_rgb = resize_for_cpu(target_raster.rgb)
    output_width, output_height = output_size

    if target_rgb.shape[1] != output_width or target_rgb.shape[0] != output_height:
        target_rgb = cv2.resize(
            target_rgb,
            (output_width, output_height),
            interpolation=cv2.INTER_AREA,
        )

    return target_rgb, target_raster.metadata


def export_geospatial_outputs(
    image: np.ndarray,
    *,
    working_dir: Path,
    raster: RasterReadResult,
    metadata: dict,
    product_urls: dict[str, str],
    original_width: int,
    original_height: int,
) -> dict:
    qgis_folder = working_dir / "qgis"
    analysis_path = None
    fallback_reason = None

    if raster.is_geospatial and raster.profile is not None:
        output_transform = scale_transform_for_resize(
            raster.transform,
            original_width=original_width,
            original_height=original_height,
            output_width=image.shape[1],
            output_height=image.shape[0],
        )
        analysis_path = export_analysis_ready_geotiff(
            image_rgb=image,
            output_path=qgis_folder / "analysis_ready_reconstruction.tif",
            reference_profile=raster.profile,
            crs=raster.crs,
            transform=output_transform,
        )
        if analysis_path is None:
            fallback_reason = "rasterio_unavailable"
    else:
        fallback_reason = "non_geospatial_input"

    qgis_result = create_qgis_output_folder(
        qgis_folder=qgis_folder,
        metadata=metadata,
        products=product_urls,
        analysis_geotiff_path=analysis_path,
    )
    tile_count = len(
        list(
            iter_tiles(
                image.shape[0],
                image.shape[1],
                tile_size=512,
                overlap=32,
            )
        )
    )

    return {
        "analysis_geotiff_path": analysis_path,
        "qgis_folder": str(qgis_result.qgis_folder),
        "qgis_manifest_path": qgis_result.manifest_path,
        "fallback_reason": fallback_reason or qgis_result.fallback_reason,
        "tile_count": tile_count,
    }


def resize_for_cpu(rgb: np.ndarray) -> np.ndarray:
    height, width = rgb.shape[:2]
    largest_dimension = max(width, height)

    if largest_dimension <= settings.max_inference_dimension:
        return rgb

    scale = settings.max_inference_dimension / largest_dimension
    new_width = max(1, int(width * scale))
    new_height = max(1, int(height * scale))
    return cv2.resize(rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)


def generate_cloud_mask(rgb: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    saturation = hsv[:, :, 1]
    brightness = hsv[:, :, 2]

    bright_low_sat = (brightness > 205) & (saturation < 90)
    very_bright = brightness > 238
    mask = np.where(bright_low_sat | very_bright, 255, 0).astype(np.uint8)
    return mask


def generate_shadow_mask(rgb: np.ndarray, cloud_mask: np.ndarray) -> np.ndarray:
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    brightness = hsv[:, :, 2]
    saturation = hsv[:, :, 1]

    dark_regions = (brightness < 75) & (saturation > 20)
    not_cloud = cloud_mask == 0
    mask = np.where(dark_regions & not_cloud, 255, 0).astype(np.uint8)
    return mask


def clean_mask(mask: np.ndarray) -> np.ndarray:
    height, width = mask.shape[:2]
    kernel_size = max(3, min(9, int(max(height, width) / 300)))

    if kernel_size % 2 == 0:
        kernel_size += 1

    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    opened = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)
    return cv2.dilate(closed, kernel, iterations=1)


def reconstruct_image(rgb: np.ndarray, invalid_mask: np.ndarray) -> np.ndarray:
    if int(np.count_nonzero(invalid_mask)) == 0:
        return rgb.copy()

    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    inpainted = cv2.inpaint(bgr, invalid_mask, inpaintRadius=5, flags=cv2.INPAINT_TELEA)
    return cv2.cvtColor(inpainted, cv2.COLOR_BGR2RGB)


def enhance_image(rgb: np.ndarray) -> np.ndarray:
    enhanced = cv2.convertScaleAbs(rgb, alpha=1.08, beta=3)
    blurred = cv2.GaussianBlur(enhanced, (0, 0), sigmaX=1.1)
    sharpened = cv2.addWeighted(enhanced, 1.35, blurred, -0.35, 0)
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def generate_difference_map(
    original: np.ndarray,
    reconstructed: np.ndarray,
) -> tuple[np.ndarray, float]:
    difference = cv2.absdiff(original, reconstructed)
    grayscale = cv2.cvtColor(difference, cv2.COLOR_RGB2GRAY)
    mean_difference = float(np.mean(grayscale))
    normalized = cv2.normalize(grayscale, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heatmap = cv2.applyColorMap(normalized, cv2.COLORMAP_TURBO)
    return cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB), mean_difference


def generate_attention_map(
    *,
    rgb: np.ndarray,
    cloud_mask: np.ndarray,
    shadow_mask: np.ndarray,
    difference_map: np.ndarray,
) -> np.ndarray:
    grayscale = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(grayscale, 50, 140).astype(np.float32)
    difference_gray = cv2.cvtColor(difference_map, cv2.COLOR_RGB2GRAY).astype(np.float32)
    attention = (
        cloud_mask.astype(np.float32) * 0.46
        + shadow_mask.astype(np.float32) * 0.28
        + difference_gray * 0.18
        + edges * 0.08
    )
    attention = cv2.GaussianBlur(attention, (0, 0), sigmaX=2.0)
    normalized = cv2.normalize(attention, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    heatmap = cv2.applyColorMap(normalized, cv2.COLORMAP_TURBO)
    heatmap_rgb = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    return cv2.addWeighted(rgb, 0.48, heatmap_rgb, 0.52, 0)


def generate_confidence_map(
    *,
    invalid_mask: np.ndarray,
    difference_map: np.ndarray,
    cloud_coverage: float,
    shadow_coverage: float,
    mean_absolute_difference: float,
    fallback_used: bool,
) -> tuple[np.ndarray, float]:
    inverse_mask = cv2.bitwise_not(invalid_mask)
    distance = cv2.distanceTransform(inverse_mask, cv2.DIST_L2, 5)
    distance_norm = cv2.normalize(distance, None, 0, 255, cv2.NORM_MINMAX).astype(np.float32)
    difference_gray = cv2.cvtColor(difference_map, cv2.COLOR_RGB2GRAY).astype(np.float32)
    confidence = distance_norm * 0.74 + (255.0 - difference_gray) * 0.26
    confidence[invalid_mask > 0] *= 0.58
    confidence = cv2.GaussianBlur(confidence, (0, 0), sigmaX=1.4)
    confidence_uint8 = np.clip(confidence, 0, 255).astype(np.uint8)
    color_map = cv2.applyColorMap(confidence_uint8, cv2.COLORMAP_VIRIDIS)
    confidence_rgb = cv2.cvtColor(color_map, cv2.COLOR_BGR2RGB)

    coverage_penalty = cloud_coverage * 0.52 + shadow_coverage * 0.24
    change_penalty = min(18.0, mean_absolute_difference / 255 * 100)
    fallback_penalty = 4.0 if fallback_used else 0.0
    score = 100.0 - coverage_penalty - change_penalty - fallback_penalty
    return confidence_rgb, float(np.clip(score, 0, 100))


def mask_to_rgb(mask: np.ndarray) -> np.ndarray:
    return cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)


def mask_percent(mask: np.ndarray) -> float:
    return float(np.count_nonzero(mask) / mask.size * 100)


def calculate_quality_score(
    *,
    cloud_coverage: float,
    shadow_coverage: float,
    mask_coverage: float,
    mean_absolute_difference: float,
) -> float:
    difference_penalty = min(25.0, mean_absolute_difference / 255 * 100)
    score = 100 - cloud_coverage * 0.45 - shadow_coverage * 0.2 - mask_coverage * 0.15
    score -= difference_penalty * 0.35
    return float(np.clip(score, 0, 100))


async def save_and_persist_product(
    image: np.ndarray,
    *,
    run_id: UUID,
    asset_type: str,
    working_dir: Path,
) -> InferenceProduct:
    safe_name = f"{asset_type}.png"
    asset_id = uuid4()
    path = working_dir / safe_name
    bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

    if not cv2.imwrite(str(path), bgr):
        raise AppError("Failed to write inference output.", code="output_write_failed")

    stored = stored_upload_from_path(
        path,
        original_filename=safe_name,
        content_type="image/png",
    )
    storage = await persist_upload(stored, scene_id=run_id, asset_id=asset_id)

    return InferenceProduct(
        asset_id=asset_id,
        asset_type=asset_type,
        safe_filename=safe_name,
        stored=stored,
        storage=storage,
    )


async def persist_existing_product(
    path: Path,
    *,
    run_id: UUID,
    asset_type: str,
    original_filename: str,
    content_type: str,
) -> InferenceProduct:
    asset_id = uuid4()
    stored = stored_upload_from_path(
        path,
        original_filename=original_filename,
        content_type=content_type,
    )
    storage = await persist_upload(stored, scene_id=run_id, asset_id=asset_id)

    return InferenceProduct(
        asset_id=asset_id,
        asset_type=asset_type,
        safe_filename=path.name,
        stored=stored,
        storage=storage,
    )


def stored_upload_from_path(
    path: Path,
    *,
    original_filename: str,
    content_type: str,
) -> StoredUpload:
    file_bytes = path.read_bytes()
    return StoredUpload(
        original_filename=original_filename,
        safe_filename=path.name,
        local_path=path,
        file_size_bytes=len(file_bytes),
        checksum_sha256=hashlib.sha256(file_bytes).hexdigest(),
        content_type=content_type,
    )
