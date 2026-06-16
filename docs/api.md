# API Reference

Base URL:

```text
Local:      http://127.0.0.1:8000
Production: https://<render-api-domain>
```

All JSON endpoints use:

```json
{
  "success": true,
  "data": {},
  "error": null,
  "message": "optional",
  "request_id": "uuid"
}
```

## Health

### `GET /api/health`

Returns service status and environment.

### `GET /api/ready`

Returns dependency readiness where implemented.

## Inference

### `POST /api/inference/run`

Multipart form data:

```text
file=<PNG|JPG|TIFF|GeoTIFF|JP2>
requested_model=opencv-baseline|attention-unet|swin-unet|multi-sensor-fusion
target=<optional cloud-free reference image>
project_id=<optional authenticated user project UUID>
```

Returns:

- original image URL
- cloud mask URL
- shadow mask URL
- reconstructed image URL
- difference map URL
- attention map URL
- confidence map URL
- analysis GeoTIFF URL when available
- QGIS manifest URL
- cloud coverage percent
- shadow coverage percent
- quality score
- reconstruction confidence score
- processing time
- requested model
- used model
- fallback status
- geospatial metadata
- evaluation metrics
- benchmark rows
- AI recommendations
- report URLs

If an `Authorization: Bearer <token>` header is present, the run is attached to the authenticated user and optional project, and generated assets count toward the user's storage quota.

## Authentication and Users

### `POST /api/auth/signup`

Creates a public user account and returns a JWT.

### `POST /api/auth/login`

Authenticates a user and returns a JWT.

### `GET /api/auth/me`

Returns the current user profile. Requires `Authorization: Bearer <token>`.

### `GET /api/users/me/history`

Returns authenticated scene and inference history plus storage usage.

### `GET /api/users/me/storage`

Returns quota, used bytes, remaining bytes, and usage percent.

## Projects

```text
GET  /api/projects
POST /api/projects
GET  /api/projects/{project_id}
```

Project routes require JWT authentication.

## Model Registry and Research

```text
GET  /api/model-registry/summary
GET  /api/model-registry/models
GET  /api/model-registry/models/best
GET  /api/model-registry/training-history
GET  /api/model-registry/metrics-history
GET  /api/model-registry/checkpoints
GET  /api/research/summary
POST /api/research/export
```

Research export supports `pdf`, `csv`, `json`, and `markdown`. Public exports work without authentication; authenticated exports are attached to the user and count toward storage quota.

## Demo

### `GET /api/demo/sample`

Returns the cached judge demo sample. If no cached result exists, it creates one.

### `POST /api/demo/run`

Runs or returns the cached synthetic demo pipeline.

Query parameters:

```text
force=true
```

When `force=true`, a new demo inference result is generated. By default, the endpoint returns the precomputed cached result to keep public deployment fast.

The demo response includes:

- sample ID
- synthetic flag
- cloudy sample URL
- reference image URL
- normal inference result payload
- explanation
- limitations

## Benchmarks

### `GET /api/benchmarks`

Lists recent benchmark records.

### `GET /api/benchmarks/latest`

Returns the most recent benchmark result.

### `GET /api/benchmarks/{benchmark_id}`

Returns one benchmark result.

## Files

### `GET /api/files/{asset_id}`

Serves local files in development or redirects to Cloudinary/Supabase URLs in production.

## Scenes and Jobs

Scene and job routes remain available for operational expansion:

```text
GET  /api/scenes
POST /api/scenes
POST /api/scenes/upload
GET  /api/jobs
POST /api/jobs
```

## Error Format

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "unsupported_inference_image_type",
    "message": "Unsupported inference image type.",
    "details": {}
  },
  "message": null,
  "request_id": "uuid"
}
```
