# Deployment Guide

## Quick Start (Local Development)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend will be available at: http://localhost:8000
API Documentation: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

---

## Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Backend Only (Docker)

```bash
cd backend
docker build -t portfolio-optimizer-backend .
docker run -p 8000:8000 -e CORS_ORIGINS="*" portfolio-optimizer-backend
```

---

## Production Deployment

### Backend - Render / Fly.io

#### Render

1. Create a new Web Service
2. Connect your GitHub repository
3. Configure:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Environment Variables:
     - `APP_ENV=production`
     - `APP_DEBUG=false`
     - `CORS_ORIGINS=https://your-frontend-domain.vercel.app`

#### Fly.io

```bash
cd backend
fly launch
fly deploy
```

Create `fly.toml`:
```toml
app = "portfolio-optimizer-api"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  APP_ENV = "production"
  APP_DEBUG = "false"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]
```

### Frontend - Vercel / Netlify

#### Vercel

```bash
cd frontend
npm install -g vercel
vercel
```

Or connect via GitHub:
1. Import your repository
2. Framework: Vite
3. Build command: `npm run build`
4. Output directory: `dist`
5. Environment variables:
   - `VITE_API_URL=https://your-backend-url.com`

#### Netlify

```bash
cd frontend
npm run build
netlify deploy --prod --dir=dist
```

Or via `netlify.toml`:
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/api/*"
  to = "https://your-backend-url.com/api/:splat"
  status = 200
```

---

## Environment Variables

### Backend (.env)

```bash
APP_ENV=production
APP_DEBUG=false
CACHE_DIR=./cache
CACHE_TTL_HOURS=24
CORS_ORIGINS=https://your-frontend-domain.com
API_HOST=0.0.0.0
API_PORT=8000
```

### Frontend (.env)

```bash
VITE_API_URL=https://your-backend-url.com
```

---

## Performance Optimization

### Backend

1. **Enable Redis caching** (optional):
   - Uncomment Redis service in `docker-compose.yml`
   - Update `data_service.py` to use Redis instead of diskcache

2. **Increase worker processes**:
   ```bash
   uvicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000
   ```

3. **Use Gunicorn with Uvicorn workers**:
   ```bash
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

### Frontend

1. **Optimize build**:
   ```bash
   npm run build
   # Output is in dist/
   ```

2. **Enable compression** on your hosting platform

3. **Configure CDN** for static assets

---

## Monitoring

### Backend Monitoring

1. **Health Check Endpoint**: `GET /api/health`

2. **Add Sentry** (optional):
   ```bash
   pip install sentry-sdk
   ```

   In `app/main.py`:
   ```python
   import sentry_sdk

   sentry_sdk.init(
       dsn="your-sentry-dsn",
       traces_sample_rate=1.0,
   )
   ```

3. **Logging**:
   - Logs are written to stdout
   - Configure log aggregation (e.g., Papertrail, Logtail)

### Frontend Monitoring

1. **Error Tracking**: Add error boundary in React

2. **Analytics**: Google Analytics, Plausible, etc.

---

## Security Considerations

1. **CORS**: Configure properly for production
   ```python
   CORS_ORIGINS=https://your-domain.com
   ```

2. **Rate Limiting**: Consider adding rate limiting middleware

3. **API Keys**: If using premium data sources, use environment variables

4. **HTTPS**: Always use HTTPS in production

---

## Scaling

### Horizontal Scaling

- Deploy multiple backend instances behind a load balancer
- Use Redis for shared caching across instances

### Vertical Scaling

- Increase CPU/memory for compute-intensive operations
- Optimize optimization algorithm iterations

---

## Troubleshooting

### Backend won't start

- Check Python version (3.11+)
- Verify all dependencies installed
- Check port 8000 is not in use
- Review logs for errors

### Frontend can't connect to backend

- Verify CORS settings
- Check `VITE_API_URL` environment variable
- Ensure backend is running and accessible
- Check browser console for errors

### Optimization is slow

- Reduce `n_iterations` in config
- Decrease `top_k_per_sector`
- Enable caching
- Use Redis instead of diskcache

### Data fetch errors

- Yahoo Finance may rate-limit
- Check internet connectivity
- Verify ticker symbols are valid
- Review cache settings

---

## Backup & Maintenance

1. **Cache Management**:
   - Cache auto-expires after 24 hours
   - Manual clear: `DELETE /api/cache` (implement if needed)

2. **Database** (if added):
   - Regular backups
   - Migration strategy

3. **Updates**:
   - Keep dependencies updated
   - Monitor security advisories
   - Test before deploying to production
