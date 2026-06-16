# clearSKY AI Deployment Guide

This document covers the public deployment path for Module 4.

## Production Topology

```text
Vercel Next.js frontend
  -> Render FastAPI backend
  -> Neon PostgreSQL
  -> Cloudinary or Supabase Storage
```

Local development remains supported with SQLite and local file storage.

## Required Environment Variables

### Frontend: Vercel

Set these in the Vercel project for `apps/web`:

```text
NEXT_PUBLIC_API_BASE_URL=https://<render-api-domain>
BACKEND_URL=https://<render-api-domain>
FRONTEND_URL=https://<vercel-domain>
```

Only variables prefixed with `NEXT_PUBLIC_` are available in browser code.

### Backend: Render

Set these on the Render API service and worker:

```text
APP_ENV=production
DATABASE_URL=postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require
FRONTEND_URL=https://<vercel-domain>
BACKEND_URL=https://<render-api-domain>
ALLOWED_ORIGINS=https://<vercel-domain>
STORAGE_PROVIDER=cloudinary
CLOUDINARY_URL=cloudinary://KEY:SECRET@CLOUD_NAME
JWT_SECRET=<long-random-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEFAULT_USER_STORAGE_QUOTA_MB=512
MAX_UPLOAD_SIZE_MB=512
INFERENCE_DIR=/app/inference
ALLOWED_UPLOAD_EXTENSIONS=.tif,.tiff,.zip
ALLOWED_INFERENCE_EXTENSIONS=.png,.jpg,.jpeg,.tif,.tiff,.jp2,.j2k
MAX_INFERENCE_DIMENSION=2048
MAX_INFERENCE_PIXELS=25000000
SERVED_FILES_ENABLED=false
API_INTERNAL_TOKEN=<generated-secret>
```

For Supabase Storage instead of Cloudinary:

```text
STORAGE_PROVIDER=supabase
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_STORAGE_BUCKET=clearsky
```

The Supabase bucket must exist before deployment. If using public object URLs, configure the bucket policy accordingly. For private buckets, later modules should add signed download URLs.

## Neon PostgreSQL

1. Create a Neon project.
2. Copy the pooled or direct connection string.
3. Use the SQLAlchemy/psycopg form:

```text
postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require
```

The API also normalizes `postgres://` and `postgresql://` URLs to the psycopg driver.

## Render

`render.yaml` defines:

- `clearsky-api`: public FastAPI web service.
- `clearsky-worker`: background worker placeholder.

Use Render Blueprints or create services manually with:

```text
Root directory: apps/api
Runtime: Docker
Health check path: /api/health
```

Production startup fails intentionally if:

- `DATABASE_URL` is missing.
- `STORAGE_PROVIDER=local`.
- Cloudinary/Supabase credentials are missing for the selected provider.
- `JWT_SECRET` is missing or left as the development default.

## Vercel

Deploy `apps/web` as the Vercel project root.

`apps/web/vercel.json` is ready for Next.js:

```text
Install command: npm install
Build command: npm run build
```

Set `NEXT_PUBLIC_API_BASE_URL` to the Render API domain.

## Storage Modes

### Local Development

```text
STORAGE_PROVIDER=local
UPLOAD_DIR=.local/uploads
SERVED_FILES_ENABLED=true
BACKEND_URL=http://localhost:8000
```

Uploads are saved on disk and served from:

```text
/api/files/{asset_id}
```

If `BACKEND_URL` is set, persisted file URLs become absolute.

The Module 5 inference pipeline also stores intermediate outputs locally under:

```text
INFERENCE_DIR=.local/inference
```

### Cloudinary Production

```text
STORAGE_PROVIDER=cloudinary
CLOUDINARY_URL=cloudinary://KEY:SECRET@CLOUD_NAME
SERVED_FILES_ENABLED=false
```

Uploads are pushed as raw files and database assets store the Cloudinary URL.

### Supabase Production

```text
STORAGE_PROVIDER=supabase
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_STORAGE_BUCKET=clearsky
SERVED_FILES_ENABLED=false
```

Uploads are stored under:

```text
uploads/{scene_id}/{safe_filename}
```

## CORS

Use both:

```text
FRONTEND_URL=https://<vercel-domain>
ALLOWED_ORIGINS=https://<vercel-domain>
```

Local defaults include:

```text
http://localhost:3000,http://127.0.0.1:3000
```

## Smoke Test

After deployment:

```bash
curl https://<render-api-domain>/api/health
curl https://<render-api-domain>/api/ready
```

For Module 5 inference, send a sample image:

```bash
curl -X POST https://<render-api-domain>/api/inference/run \
  -F "requested_model=swin-unet" \
  -F "file=@sample-cloudy-scene.png"
```

The response should include public URLs for the original preview, cloud mask, shadow mask, reconstructed image, difference map, attention map, and confidence map, plus coverage, quality, confidence, and recommendation fields.

Authentication smoke test:

```bash
curl -X POST https://<render-api-domain>/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"judge@example.com","password":"StrongPass123"}'
```

Then open:

```text
https://<vercel-domain>/dashboard
```

The dashboard API health card should report `ok`.
