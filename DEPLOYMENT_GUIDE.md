# AI Interviewer - Complete Deployment Guide

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Quick Start (Railway - Recommended)](#quick-start-railway)
3. [Alternative: Render.com](#alternative-rendercom)
4. [Alternative: Docker Deployment](#alternative-docker-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Post-Deployment Testing](#post-deployment-testing)
7. [Monitoring & Maintenance](#monitoring--maintenance)
8. [Troubleshooting](#troubleshooting)

---

## Pre-Deployment Checklist

### ✅ Required Steps

1. **Get API Keys**
   - [ ] Hugging Face API Key: https://huggingface.co/settings/tokens
   - [ ] Generate JWT Secret: `python -c "import secrets; print(secrets.token_hex(32))"`

2. **Review Configuration**
   - [ ] Copy `.env.example` to `.env`
   - [ ] Fill in all required environment variables
   - [ ] Update `ALLOWED_ORIGINS` with your frontend domain

3. **Code Optimization** (Optional but Recommended)
   - [ ] Review `OPTIMIZATION_REPORT.md`
   - [ ] Switch to `requirements-light.txt` for smaller deployment
   - [ ] Remove unused files (see report)

### 📊 Deployment Size Comparison

| Configuration | Size | Pros | Cons |
|--------------|------|------|------|
| **Full** (current) | ~2GB | All features local | Slow, expensive |
| **Lightweight** (recommended) | ~200MB | Fast, cheap | API dependencies |

---

## Quick Start (Railway)

### Why Railway?
- ✅ Easiest deployment
- ✅ Auto-scaling
- ✅ Built-in PostgreSQL
- ✅ Affordable ($5-10/month)
- ✅ GitHub integration

### Step-by-Step

#### 1. Prepare Your Repository

```bash
# Ensure you're in the project root
cd "d:\ai interview\interviewer with tab switch warning\ai interviewer\ai final"

# Initialize git if not already done
git init
git add .
git commit -m "Prepare for deployment"

# Push to GitHub
git remote add origin https://github.com/YOUR_USERNAME/ai-interviewer.git
git push -u origin main
```

#### 2. Deploy Backend

1. Go to [Railway.app](https://railway.app) and sign up
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Configure:
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements-light.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

5. Add Environment Variables:
   ```
   JWT_SECRET_KEY=<your-generated-secret>
   HF_API_KEY=<your-hf-api-key>
   ALLOWED_ORIGINS=https://your-frontend-domain.railway.app
   FLASK_ENV=production
   ```

6. Click "Deploy"
7. Note your backend URL (e.g., `https://ai-interviewer-backend.railway.app`)

#### 3. Deploy Frontend

1. Click "New" → "GitHub Repo" (same repo)
2. Configure:
   - **Root Directory**: `frontend-new`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm run preview`

3. Add Environment Variable:
   ```
   VITE_API_URL=https://your-backend-url.railway.app
   ```

4. Click "Deploy"

#### 4. Update CORS

Go back to backend environment variables and update:
```
ALLOWED_ORIGINS=https://your-frontend-url.railway.app
```

Redeploy backend.

### ✅ Done! Your app is live!

---

## Alternative: Render.com

### Step-by-Step

#### 1. Deploy Backend

1. Go to [Render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `ai-interviewer-backend`
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements-light.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: Free or Starter ($7/month)

5. Add Environment Variables (same as Railway)

6. Click "Create Web Service"

#### 2. Deploy Frontend

1. Click "New +" → "Static Site"
2. Connect same repository
3. Configure:
   - **Name**: `ai-interviewer-frontend`
   - **Root Directory**: `frontend-new`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`

4. Add Environment Variable:
   ```
   VITE_API_URL=https://ai-interviewer-backend.onrender.com
   ```

5. Click "Create Static Site"

#### 3. Update CORS (same as Railway)

---

## Alternative: Docker Deployment

### Local Testing

```bash
# Copy environment file
cp .env.example .env

# Edit .env with your values
notepad .env

# Build and run with optimized configuration
docker-compose -f docker-compose.prod.yml up --build
```

### Deploy to VPS (DigitalOcean, AWS, etc.)

```bash
# SSH into your server
ssh user@your-server-ip

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Clone your repository
git clone https://github.com/YOUR_USERNAME/ai-interviewer.git
cd ai-interviewer

# Set up environment
cp .env.example .env
nano .env  # Fill in your values

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Set Up Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:7860;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Environment Configuration

### Required Variables

```env
# MUST be set for production
JWT_SECRET_KEY=<64-character-hex-string>
HF_API_KEY=<your-huggingface-api-key>
```

### Recommended Variables

```env
ALLOWED_ORIGINS=https://yourdomain.com
FLASK_ENV=production
FLASK_DEBUG=False
MAX_CONTENT_LENGTH=16777216
```

### Optional Variables

```env
# PostgreSQL (recommended for production)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Redis (for caching)
REDIS_URL=redis://host:6379/0

# Rate limiting
RATE_LIMIT_ENABLED=True
RATE_LIMIT_PER_MINUTE=60
```

---

## Post-Deployment Testing

### 1. Health Check

```bash
curl https://your-backend-url.com/health
```

Expected response:
```json
{"status": "healthy", "time": 1234567890}
```

### 2. Test Registration

```bash
curl -X POST https://your-backend-url.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### 3. Test Login

```bash
curl -X POST https://your-backend-url.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123"
  }'
```

### 4. Full User Flow

1. Open frontend URL
2. Register a new account
3. Login
4. Select a technology track
5. Start interview
6. Answer questions
7. Check scoring and feedback

---

## Monitoring & Maintenance

### Railway Dashboard

- View logs in real-time
- Monitor resource usage
- Set up alerts for downtime
- View deployment history

### Render Dashboard

- Check build logs
- Monitor metrics
- Set up health check alerts
- View deployment history

### Custom Monitoring

Add to your backend:

```python
# app.py
@app.route("/metrics", methods=["GET"])
def metrics():
    return jsonify({
        "uptime": time.time() - start_time,
        "total_sessions": get_session_count(),
        "active_users": get_active_user_count()
    })
```

### Log Aggregation

For production, consider:
- **Sentry** for error tracking
- **LogRocket** for session replay
- **DataDog** for comprehensive monitoring

---

## Troubleshooting

### Issue: "JWT_SECRET_KEY environment variable is required"

**Solution**: Set the environment variable in your deployment platform

```bash
# Railway/Render
JWT_SECRET_KEY=your-secret-key

# Docker
echo "JWT_SECRET_KEY=your-secret-key" >> .env
```

### Issue: CORS errors in browser

**Solution**: Update ALLOWED_ORIGINS

```bash
# Backend environment
ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

### Issue: "Module not found" errors

**Solution**: Ensure correct requirements file

```bash
# For lightweight deployment
pip install -r requirements-light.txt

# For full deployment
pip install -r requirements.txt
```

### Issue: Database errors

**Solution**: Initialize database

```bash
# SSH into your server or use Railway shell
python -c "from database.db_helper import init_db; init_db('database/interviews.db')"
python -c "from database.auth_helper import init_auth_db; init_auth_db('database/auth.db')"
```

### Issue: Slow performance

**Solutions**:
1. Use lightweight deployment
2. Enable caching with Redis
3. Upgrade instance size
4. Use PostgreSQL instead of SQLite
5. Enable CDN for static assets

### Issue: Out of memory

**Solutions**:
1. Switch to `requirements-light.txt`
2. Reduce worker count in gunicorn
3. Upgrade instance size
4. Use external API services instead of local models

---

## Cost Optimization Tips

1. **Use Free Tiers**
   - Render: Free tier available (with limitations)
   - Railway: $5 credit/month free

2. **Optimize Resources**
   - Use lightweight deployment (~90% cost reduction)
   - Enable auto-scaling
   - Use spot instances (AWS)

3. **Cache Aggressively**
   - Use Redis for session data
   - Cache API responses
   - Use CDN for static assets

4. **Monitor Usage**
   - Set up billing alerts
   - Track API usage
   - Monitor database size

---

## Security Checklist

- [ ] All secrets in environment variables (not code)
- [ ] CORS properly configured (not wildcard)
- [ ] HTTPS enabled
- [ ] Rate limiting enabled
- [ ] Input validation implemented
- [ ] SQL injection protection
- [ ] XSS protection
- [ ] CSRF protection
- [ ] Regular security updates
- [ ] Backup strategy in place

---

## Next Steps

1. **Custom Domain**
   - Purchase domain from Namecheap/GoDaddy
   - Configure DNS in Railway/Render
   - Enable SSL/TLS

2. **Analytics**
   - Add Google Analytics
   - Track user behavior
   - Monitor conversion rates

3. **Continuous Deployment**
   - Set up GitHub Actions
   - Automated testing
   - Auto-deploy on merge to main

4. **Scaling**
   - Add load balancer
   - Use database replicas
   - Implement caching layer
   - Use CDN

---

## Support

For issues:
1. Check logs in deployment platform
2. Review this troubleshooting guide
3. Check `OPTIMIZATION_REPORT.md`
4. Review GitHub issues

---

## Summary

**Recommended Path**: Railway with lightweight deployment

**Total Time**: 30-60 minutes
**Monthly Cost**: $5-15
**Deployment Size**: ~200MB (lightweight) or ~2GB (full)

Good luck with your deployment! 🚀
