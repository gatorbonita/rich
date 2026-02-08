# Northflank Deployment Guide

## Overview

You have two deployment options for Northflank:

1. **Two Services (Recommended)** - Separate frontend and backend services
2. **Monolithic** - Single service serving both frontend and backend

---

## Option 1: Two Separate Services (Recommended)

This approach provides better scalability and separation of concerns.

### Step 1: Deploy Backend Service

1. **Create Backend Service** in Northflank:
   - Service Type: **Deployment**
   - Source: Connect your GitHub repository
   - Build Settings:
     - Dockerfile Path: `backend/Dockerfile`
     - Build Context: `backend/`
   - Port: **8000**

2. **Environment Variables**:
   ```
   APP_ENV=production
   APP_DEBUG=false
   CACHE_DIR=/app/cache
   CORS_ORIGINS=https://your-frontend-url.northflank.app
   ```

3. **Resource Allocation**:
   - CPU: 0.5 vCPU
   - Memory: 1 GB
   - Storage: 2 GB (for cache)

4. **Health Check**:
   - Path: `/api/health`
   - Port: 8000
   - Initial Delay: 10s

### Step 2: Deploy Frontend Service

1. **Create Frontend Service** in Northflank:
   - Service Type: **Deployment**
   - Source: Same GitHub repository
   - Build Settings:
     - Dockerfile Path: `frontend/Dockerfile`
     - Build Context: `frontend/`
   - Port: **80**

2. **Environment Variables** (Build-time):
   ```
   VITE_API_URL=https://your-backend-url.northflank.app
   ```

   Note: Update `frontend/.env.production` or pass as build arg:
   ```dockerfile
   # In frontend/Dockerfile, modify build stage:
   ARG VITE_API_URL
   ENV VITE_API_URL=$VITE_API_URL
   ```

3. **Resource Allocation**:
   - CPU: 0.2 vCPU
   - Memory: 512 MB

4. **Health Check**:
   - Path: `/health`
   - Port: 80
   - Initial Delay: 5s

### Step 3: Update CORS

After deployment, update the backend's `CORS_ORIGINS` environment variable with your actual frontend URL.

### Advantages
- ✅ Independent scaling
- ✅ Separate deployment pipelines
- ✅ Better for microservices architecture
- ✅ Frontend can be cached at CDN

---

## Option 2: Monolithic Single Service

Serve both frontend and backend from one container.

### Prerequisites

You need to modify the FastAPI backend to serve static files. Add to `backend/app/main.py`:

```python
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

# ... existing code ...

# Mount static files (built frontend)
static_dir = Path(__file__).parent.parent / "static"
if static_dir.exists():
    app.mount("/assets", StaticFiles(directory=str(static_dir / "assets")), name="assets")

    # Serve index.html for all non-API routes (SPA routing)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Skip API routes
        if full_path.startswith("api/") or full_path.startswith("docs"):
            return {"error": "Not found"}

        index_file = static_dir / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
        return {"error": "Frontend not built"}
```

### Deployment Steps

1. **Create Service** in Northflank:
   - Service Type: **Deployment**
   - Source: GitHub repository
   - Build Settings:
     - Dockerfile Path: `Dockerfile.monolithic`
     - Build Context: `.` (root directory)
   - Port: **8000**

2. **Environment Variables**:
   ```
   APP_ENV=production
   APP_DEBUG=false
   CACHE_DIR=/app/cache
   CORS_ORIGINS=*
   VITE_API_URL=/
   ```

3. **Resource Allocation**:
   - CPU: 1 vCPU
   - Memory: 2 GB
   - Storage: 2 GB

4. **Health Check**:
   - Path: `/api/health`
   - Port: 8000

### Advantages
- ✅ Simpler deployment (one service)
- ✅ No CORS configuration needed
- ✅ Lower cost (one container)

### Disadvantages
- ❌ Cannot scale frontend and backend independently
- ❌ Rebuilding frontend requires redeploying backend
- ❌ Larger container image

---

## Recommended: Option 1 (Two Services)

For production use, **Option 1** is recommended because:
1. Better scalability
2. Independent deployments
3. Can use CDN for frontend
4. Standard microservices pattern

---

## Cost Estimation (Northflank)

### Option 1 (Two Services)
- Backend: ~$20-30/month (0.5 vCPU, 1GB RAM)
- Frontend: ~$10-15/month (0.2 vCPU, 512MB RAM)
- **Total: ~$30-45/month**

### Option 2 (One Service)
- Single Service: ~$35-50/month (1 vCPU, 2GB RAM)
- **Total: ~$35-50/month**

---

## Next Steps

1. Choose your deployment option
2. Push code to GitHub
3. Create services in Northflank
4. Configure environment variables
5. Deploy!

### Testing After Deployment

1. Check backend health: `https://your-backend.northflank.app/api/health`
2. Check API docs: `https://your-backend.northflank.app/docs`
3. Test frontend: `https://your-frontend.northflank.app` (Option 1) or `https://your-app.northflank.app` (Option 2)
4. Test optimization with default parameters

---

## Troubleshooting

### CORS Errors
- Update `CORS_ORIGINS` environment variable with your frontend URL
- Restart backend service after updating

### Frontend Can't Connect to Backend
- Check `VITE_API_URL` is set correctly
- Verify backend is accessible
- Check network policies in Northflank

### Timeout Errors
- First optimization takes 40-60 seconds (data fetching)
- Subsequent runs are cached and fast
- Ensure frontend timeout is set to 60s (already configured)

### Cache Issues
- Ensure persistent storage is mounted to `/app/cache`
- Cache persists between deployments if storage is configured

---

## Files Created

- `frontend/Dockerfile` - Frontend container configuration
- `frontend/nginx.conf` - Nginx configuration for SPA
- `Dockerfile.monolithic` - Single container for both services
- `NORTHFLANK_DEPLOYMENT.md` - This guide

---

## Support

For issues specific to Northflank, consult:
- Northflank Documentation: https://northflank.com/docs
- Your project's README.md
- DEPLOYMENT.md (general deployment guide)
