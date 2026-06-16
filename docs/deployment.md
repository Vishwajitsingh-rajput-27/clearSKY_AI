# Deployment

## Target Stack

```text
Frontend: Vercel
Backend: Render
Database: Neon PostgreSQL
Storage: Cloudinary or Supabase Storage
Inference: CPU-safe OpenCV fallback with optional PyTorch weights
```

## Frontend: Vercel

Project root:

```text
apps/web
```

Required environment:

```text
NEXT_PUBLIC_API_BASE_URL=https://<render-api-domain>
```

Build:

```bash
npm install
npm run build
```

## Backend: Render

Use `render.yaml` or create a Docker web service manually.

Root directory:

```text
apps/api
```

Health check:

```text
/api/health
```

Production environment:

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
ALLOWED_INFERENCE_EXTENSIONS=.png,.jpg,.jpeg,.tif,.tiff,.jp2,.j2k
MAX_INFERENCE_DIMENSION=2048
MAX_INFERENCE_PIXELS=25000000
SERVED_FILES_ENABLED=false
```

For Supabase:

```text
STORAGE_PROVIDER=supabase
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
SUPABASE_STORAGE_BUCKET=clearsky
```

## Neon PostgreSQL

Use a Neon connection string with SSL:

```text
postgresql+psycopg://USER:PASSWORD@HOST/DB?sslmode=require
```

Tables are created automatically when `AUTO_CREATE_TABLES=true`. For stricter production governance, replace auto-create with Alembic migrations before final launch.

## Storage

Development:

```text
STORAGE_PROVIDER=local
SERVED_FILES_ENABLED=true
```

Production:

- Cloudinary is suitable for public previews and reports.
- Supabase Storage is preferred for scientific file outputs and larger artifacts.
- Future production hardening should add signed URLs for private scientific assets.

## Authentication

Public users can sign up, log in, create projects, and track history. Production requires:

```text
JWT_SECRET=<long-random-secret>
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEFAULT_USER_STORAGE_QUOTA_MB=512
```

The backend intentionally refuses to boot in production with the development JWT secret.

## CPU-Safe Inference

The deployed API does not require GPU. It uses:

- OpenCV thresholding.
- OpenCV morphology.
- OpenCV Telea inpainting.
- Optional PyTorch checkpoint loading only when weights are present.

This makes the app suitable for Render CPU instances.

## Smoke Test

```bash
curl https://<render-api-domain>/api/health
curl https://<render-api-domain>/api/demo/sample
curl -X POST https://<render-api-domain>/api/demo/run
curl -X POST https://<render-api-domain>/api/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"judge@example.com","password":"StrongPass123"}'
```

Then open:

```text
https://<vercel-domain>
```

Click `Run sample demo` and verify:

- Dashboard opens.
- Original, mask, reconstruction, attention map, confidence map, recommendations, and metrics are visible.
- Benchmarking page shows model comparison.
- Evaluation page shows full-reference demo metrics.
- Operational Workflow page shows explainability and time-series comparison.
