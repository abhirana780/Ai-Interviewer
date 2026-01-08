# 🚂 Railway Quick Reference Card

## 🎯 Pre-Deployment (5 min)

### Generate JWT Secret
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
**Save this!** You'll need it later.

### Get Hugging Face API Key
1. Go to: https://huggingface.co/settings/tokens
2. Create new token
3. **Save it!** (starts with `hf_...`)

---

## 📦 Backend Configuration

### Settings
| Setting | Value |
|---------|-------|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements-light.txt` |
| Start Command | `gunicorn app:app --bind 0.0.0.0:$PORT` |

### Environment Variables
```env
JWT_SECRET_KEY=<your-generated-secret-from-step-1>
HF_API_KEY=<your-hf-api-key-from-step-2>
ALLOWED_ORIGINS=<your-frontend-url>
FLASK_ENV=production
FLASK_DEBUG=False
```

**Note**: Set `ALLOWED_ORIGINS=*` initially, update after frontend is deployed

---

## 🎨 Frontend Configuration

### Settings
| Setting | Value |
|---------|-------|
| Root Directory | `frontend-new` |
| Build Command | `npm install && npm run build` |
| Start Command | `npm run preview -- --host 0.0.0.0 --port $PORT` |

### Environment Variables
```env
VITE_API_URL=<your-backend-url>
```

**Example**: `https://ai-interviewer-backend-production.up.railway.app`

---

## ✅ Deployment Checklist

- [ ] Generate JWT secret
- [ ] Get HF API key
- [ ] Push code to GitHub
- [ ] Create Railway project
- [ ] Deploy backend service
- [ ] Add backend environment variables
- [ ] Generate backend domain
- [ ] Test backend health endpoint
- [ ] Deploy frontend service
- [ ] Add frontend environment variable
- [ ] Generate frontend domain
- [ ] Update backend CORS with frontend URL
- [ ] Test full application

---

## 🧪 Testing Commands

### Test Backend Health
```bash
curl https://your-backend-url.up.railway.app/health
```

Expected: `{"status":"healthy","time":1234567890}`

### Test Registration
```bash
curl -X POST https://your-backend-url.up.railway.app/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"test123"}'
```

---

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| "JWT_SECRET_KEY required" | Add variable in Railway |
| CORS errors | Update `ALLOWED_ORIGINS` with frontend URL |
| "Module not found" | Check build command uses `requirements-light.txt` |
| Frontend can't connect | Verify `VITE_API_URL` matches backend URL |

---

## 💰 Cost

- **Hobby Plan**: $5/month (recommended)
- **Pro Plan**: $20/month (for scaling)

**Estimated**: $5-10/month for this project

---

## 📞 Quick Links

- Railway Dashboard: https://railway.app/dashboard
- Railway Docs: https://docs.railway.app
- HF API Keys: https://huggingface.co/settings/tokens
- Project Logs: Railway → Service → Deployments

---

## 🔄 Update Deployment

```bash
git add .
git commit -m "Update message"
git push origin main
```

Railway auto-deploys on push! 🚀

---

**Total Time**: ~30 minutes  
**Difficulty**: ⭐ Easy  
**Full Guide**: See `RAILWAY_DEPLOYMENT.md`
