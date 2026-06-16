from typing import Any


def build_ai_recommendations(
    *,
    metrics: dict[str, Any],
    metadata: dict[str, Any],
    requested_model: str,
    used_model: str,
    fallback_used: bool,
) -> list[dict[str, Any]]:
    cloud = as_float(metrics.get("cloud_coverage_percent")) or 0.0
    shadow = as_float(metrics.get("shadow_coverage_percent")) or 0.0
    mask = as_float(metrics.get("mask_coverage_percent")) or 0.0
    confidence = as_float(metrics.get("reconstruction_confidence_score")) or 0.0
    recommendations: list[dict[str, Any]] = []

    if cloud >= 35:
        recommendations.append(
            recommendation(
                title="Use Sentinel-1 fusion",
                message=(
                    "This image would benefit from Sentinel-1 fusion due to heavy cloud "
                    "cover."
                ),
                severity="high",
                rationale=f"Cloud coverage is {cloud:.1f}%, which limits optical context.",
                inputs=["Sentinel-1 SAR", "cloud mask", "LISS-IV"],
            )
        )
    elif cloud >= 18:
        recommendations.append(
            recommendation(
                title="Add temporal reference imagery",
                message="Moderate cloud cover suggests temporal fusion can improve reconstruction.",
                severity="medium",
                rationale=f"Cloud coverage is {cloud:.1f}% and mask coverage is {mask:.1f}%.",
                inputs=["near-date LISS-IV", "Sentinel-2 reference"],
            )
        )

    if shadow >= 8:
        recommendations.append(
            recommendation(
                title="Use DEM-guided shadow reasoning",
                message=(
                    "Shadow coverage is elevated; DEM integration can reduce "
                    "terrain-shadow error."
                ),
                severity="medium",
                rationale=f"Shadow coverage is {shadow:.1f}%.",
                inputs=["DEM", "solar geometry metadata", "shadow mask"],
            )
        )

    if not metadata.get("is_geospatial"):
        recommendations.append(
            recommendation(
                title="Prefer analysis-ready GeoTIFF input",
                message=(
                    "Upload GeoTIFF when possible so CRS, transform, and output rasters "
                    "are preserved."
                ),
                severity="info",
                rationale="The current input is a browser image without geospatial metadata.",
                inputs=["GeoTIFF", "CRS", "affine transform"],
            )
        )

    if fallback_used:
        recommendations.append(
            recommendation(
                title="Register trained reconstruction weights",
                message=(
                    f"Requested {requested_model}, but {used_model} was used. Add validated "
                    "weights to enable learned reconstruction."
                ),
                severity="medium",
                rationale="The deployment correctly fell back to CPU-safe OpenCV inference.",
                inputs=["Attention U-Net checkpoint", "Swin-UNet checkpoint"],
            )
        )

    if confidence < 65:
        recommendations.append(
            recommendation(
                title="Run multi-date comparison",
                message=(
                    "Low reconstruction confidence should be reviewed with earlier/later "
                    "dates."
                ),
                severity="high",
                rationale=f"Reconstruction confidence score is {confidence:.1f}.",
                inputs=["previous clear date", "next clear date", "temporal stack"],
            )
        )

    if not recommendations:
        recommendations.append(
            recommendation(
                title="Proceed with operational QA",
                message=(
                    "The reconstruction confidence is suitable for standard visual and "
                    "metric review."
                ),
                severity="info",
                rationale=f"Confidence score is {confidence:.1f} with cloud coverage {cloud:.1f}%.",
                inputs=["evaluation report", "QGIS output"],
            )
        )

    return recommendations


def recommendation(
    *,
    title: str,
    message: str,
    severity: str,
    rationale: str,
    inputs: list[str],
) -> dict[str, Any]:
    return {
        "title": title,
        "message": message,
        "severity": severity,
        "rationale": rationale,
        "recommended_inputs": inputs,
    }


def as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None

    if isinstance(value, int | float):
        return float(value)

    return None
