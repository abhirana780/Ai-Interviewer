# 🚂 Railway Deployment Guide - AI Interviewer

## ✅ Prerequisites Checklist

Before starting, make sure you have:

- [ ] GitHub account
- [ ] Railway account (sign up at https://railway.app)
- [ ] Hugging Face API key (get from https://huggingface.co/settings/tokens)
- [ ] JWT secret key (we'll generate this)
- [ ] Code pushed to GitHub

---

## 📋 Step-by-Step Deployment (30 minutes)

### Step 1: Prepare Environment Variables (5 minutes)

#### 1.1 Generate JWT Secret

Run this command and save the output:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**Save this value** - you'll need it in Step 3!

Example output: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e1f2`

#### 1.2 Get Hugging Face API Key

1. Go to https://huggingface.co/settings/tokens
2. Click "New token"
3. Name it "AI Interviewer"
4. Select "Read" access
5. Click "Generate"
6. **Copy and save the token** (starts with `hf_...`)

---

### Step 2: Push Code to GitHub (10 minutes)

#### 2.1 Initialize Git (if not already done)

```bash
cd "d:\ai interview\interviewer with tab switch warning\ai interviewer\ai final"

# Initialize git
git init

# Add all files
git add .

# Commit
git commit -m "Prepare for Railway deployment"
```

#### 2.2 Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `ai-interviewer`
3. Make it **Private** (recommended for security)
4. **Don't** initialize with README (we already have one)
5. Click "Create repository"

#### 2.3 Push to GitHub

```bash
# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/ai-interviewer.git

# Push code
git branch -M main
git push -u origin main
```

**✅ Checkpoint**: Your code should now be visible on GitHub!

---

### Step 3: Deploy Backend to Railway (10 minutes)

#### 3.1 Create Railway Project

1. Go to https://railway.app
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Click **"Configure GitHub App"**
5. Select your `ai-interviewer` repository
6. Click **"Deploy Now"**

#### 3.2 Configure Backend Service

Railway will auto-detect it's a Python project. Now configure it:

1. Click on your deployed service
2. Go to **"Settings"** tab
3. Scroll to **"Service Settings"**

**Root Directory**: 
```
backend
```

**Build Command** (if not auto-detected):
```
pip install -r requirements-light.txt
```

**Start Command**:
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

#### 3.3 Add Environment Variables

1. Go to **"Variables"** tab
2. Click **"+ New Variable"**
3. Add these variables one by one:

**Required Variables:**

| Variable Name | Value | Where to Get |
|--------------|-------|--------------|
| `JWT_SECRET_KEY` | `<your-generated-secret>` | From Step 1.1 |
| `HF_API_KEY` | `hf_...` | From Step 1.2 |
| `ALLOWED_ORIGINS` | `*` | Temporary (we'll update later) |
| `FLASK_ENV` | `production` | Type exactly |
| `FLASK_DEBUG` | `False` | Type exactly |

**How to add each variable:**
1. Click "+ New Variable"
2. Enter Variable Name
3. Enter Value
4. Click "Add"

#### 3.4 Deploy Backend

1. Railway will automatically deploy after adding variables
2. Wait for deployment to complete (2-5 minutes)
3. Look for **"Success"** status

#### 3.5 Get Backend URL

1. Go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**
4. **Copy the URL** (e.g., `https://ai-interviewer-backend-production.up.railway.app`)

**✅ Checkpoint**: Test your backend!

```bash
# Replace with your actual URL
curl https://your-backend-url.up.railway.app/health
```

Expected response:
```json
{"status":"healthy","time":1234567890}
```

---

### Step 4: Deploy Frontend to Railway (10 minutes)

#### 4.1 Add Frontend Service

1. In your Railway project, click **"+ New"**
2. Select **"GitHub Repo"**
3. Select the **same repository** (`ai-interviewer`)
4. Click **"Deploy"**

#### 4.2 Configure Frontend Service

1. Click on the new service
2. Go to **"Settings"** tab
3. Configure:

**Service Name**: `ai-interviewer-frontend`

**Root Directory**:
```
frontend-new
```

**Build Command**:
```
npm install && npm run build
```

**Start Command**:
```
npm run preview -- --host 0.0.0.0 --port $PORT
```

#### 4.3 Add Frontend Environment Variable

1. Go to **"Variables"** tab
2. Click **"+ New Variable"**

| Variable Name | Value |
|--------------|-------|
| `VITE_API_URL` | `https://your-backend-url.up.railway.app` |

**Important**: Replace with your actual backend URL from Step 3.5!

#### 4.4 Generate Frontend Domain

1. Go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**
4. **Copy the URL** (e.g., `https://ai-interviewer-frontend.up.railway.app`)

---

### Step 5: Update CORS Configuration (5 minutes)

Now that we have the frontend URL, update backend CORS:

#### 5.1 Update Backend Environment Variable

1. Go to **Backend service** in Railway
2. Go to **"Variables"** tab
3. Find `ALLOWED_ORIGINS`
4. Click **"Edit"**
5. Replace `*` with your frontend URL:

```
https://your-frontend-url.up.railway.app
```

**Example**:
```
https://ai-interviewer-frontend.up.railway.app
```

6. Click **"Update"**

#### 5.2 Redeploy Backend

Railway will automatically redeploy after updating the variable. Wait for it to complete.

---

### Step 6: Test Your Deployment (10 minutes)

#### 6.1 Test Backend Health

```bash
curl https://your-backend-url.up.railway.app/health
```

Expected: `{"status":"healthy","time":...}`

#### 6.2 Test Frontend

1. Open your frontend URL in a browser
2. Check browser console (F12) for errors
3. Verify no CORS errors

#### 6.3 Test Full User Flow

1. **Register**: Create a new account
2. **Login**: Sign in with your credentials
3. **Select Technology**: Choose a track (e.g., "Software Engineer")
4. **Start Interview**: Begin the interview
5. **Answer Questions**: Provide answers (text or voice)
6. **Check Feedback**: Verify you receive scores and feedback
7. **Complete Interview**: Finish all questions

**✅ If all steps work, you're live!** 🎉

---

## 🔧 Configuration Summary

### Backend Service

| Setting | Value |
|---------|-------|
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements-light.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT` |

**Environment Variables:**
- `JWT_SECRET_KEY` = Your generated secret
- `HF_API_KEY` = Your Hugging Face API key
- `ALLOWED_ORIGINS` = Your frontend URL
- `FLASK_ENV` = `production`
- `FLASK_DEBUG` = `False`

### Frontend Service

| Setting | Value |
|---------|-------|
| **Root Directory** | `frontend-new` |
| **Build Command** | `npm install && npm run build` |
| **Start Command** | `npm run preview -- --host 0.0.0.0 --port $PORT` |

**Environment Variables:**
- `VITE_API_URL` = Your backend URL

---

## 💰 Cost Estimate

Railway pricing (as of 2026):

- **Free Trial**: $5 credit (good for testing)
- **Hobby Plan**: $5/month (500 hours)
- **Pro Plan**: $20/month (unlimited)

**Estimated cost for this project**:
- **Lightweight deployment**: $5-10/month
- **Full deployment**: $15-25/month

**Recommendation**: Start with Hobby plan ($5/month)

---

## 📊 Monitoring Your Deployment

### View Logs

1. Go to your service in Railway
2. Click **"Deployments"** tab
3. Click on the latest deployment
4. View real-time logs

### Check Metrics

1. Go to **"Metrics"** tab
2. Monitor:
   - CPU usage
   - Memory usage
   - Network traffic
   - Request count

### Set Up Alerts

1. Go to **"Settings"** tab
2. Scroll to **"Health Checks"**
3. Configure health check endpoint: `/health`

---

## 🐛 Troubleshooting

### Issue: "Application failed to respond"

**Solution**: Check logs for errors

1. Go to **"Deployments"** tab
2. Click latest deployment
3. Check logs for error messages

Common causes:
- Missing environment variables
- Wrong start command
- Port binding issues

### Issue: CORS errors in browser

**Solution**: Update `ALLOWED_ORIGINS`

1. Verify frontend URL is correct in backend variables
2. Make sure there's no trailing slash
3. Redeploy backend after changes

### Issue: "Module not found" errors

**Solution**: Check build command

For lightweight deployment:
```
pip install -r requirements-light.txt
```

For full deployment:
```
pip install -r requirements.txt
```

### Issue: Frontend shows "Failed to fetch"

**Solution**: Check `VITE_API_URL`

1. Go to frontend service
2. Check **"Variables"** tab
3. Verify `VITE_API_URL` matches backend URL
4. Redeploy frontend

### Issue: "JWT_SECRET_KEY environment variable is required"

**Solution**: Add the variable

1. Go to backend service
2. Go to **"Variables"** tab
3. Add `JWT_SECRET_KEY` with your generated secret
4. Redeploy

---

## 🚀 Advanced Configuration (Optional)

### Add PostgreSQL Database

1. In Railway project, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will create and configure it
4. Add to backend variables:

```
DATABASE_URL = ${{Postgres.DATABASE_URL}}
```

### Add Redis for Caching

1. Click **"+ New"** → **"Database"** → **"Redis"**
2. Add to backend variables:

```
REDIS_URL = ${{Redis.REDIS_URL}}
```

### Custom Domain

1. Go to **"Settings"** → **"Domains"**
2. Click **"Custom Domain"**
3. Enter your domain (e.g., `app.yourdomain.com`)
4. Follow DNS configuration instructions
5. SSL certificate is automatic!

---

## 📈 Scaling Your Application

### Vertical Scaling (More Resources)

Railway automatically scales resources based on usage.

### Horizontal Scaling (Multiple Instances)

Available on Pro plan:
1. Go to **"Settings"**
2. Scroll to **"Replicas"**
3. Increase replica count

### Auto-Scaling

Railway handles this automatically based on traffic.

---

## 🔒 Security Best Practices

### ✅ Already Implemented
- [x] Environment variables for secrets
- [x] CORS whitelist
- [x] HTTPS by default
- [x] File upload limits

### 🔧 Recommended Additions

1. **Add Rate Limiting**
   - Implement in backend code
   - Prevents abuse

2. **Enable Monitoring**
   - Set up health checks
   - Configure alerts

3. **Regular Updates**
   - Keep dependencies updated
   - Monitor security advisories

4. **Backup Strategy**
   - Export database regularly
   - Keep code in GitHub

---

## 📝 Post-Deployment Checklist

- [ ] Backend deployed successfully
- [ ] Frontend deployed successfully
- [ ] Environment variables configured
- [ ] CORS updated with frontend URL
- [ ] Health check passing
- [ ] Registration working
- [ ] Login working
- [ ] Interview flow working
- [ ] No console errors
- [ ] Logs look clean
- [ ] Monitoring set up
- [ ] Custom domain configured (optional)

---

## 🎉 Success!

If you've completed all steps, your AI Interviewer is now live on Railway!

**Your URLs**:
- Backend: `https://your-backend-url.up.railway.app`
- Frontend: `https://your-frontend-url.up.railway.app`

**Next Steps**:
1. Share with users
2. Monitor logs for 24 hours
3. Gather feedback
4. Plan improvements

---

## 📞 Support

### Railway Support
- Documentation: https://docs.railway.app
- Discord: https://discord.gg/railway
- Status: https://status.railway.app

### Project Support
- Check logs in Railway dashboard
- Review `DEPLOYMENT_GUIDE.md` for general troubleshooting
- Check `OPTIMIZATION_REPORT.md` for code issues

---

## 🔄 Updating Your Deployment

When you make code changes:

```bash
# Commit changes
git add .
git commit -m "Update: description of changes"

# Push to GitHub
git push origin main
```

Railway will **automatically redeploy** when you push to GitHub! 🚀

---

**Deployment Time**: ~30 minutes  
**Monthly Cost**: $5-10  
**Difficulty**: ⭐ Easy  
**Status**: Production-Ready

Good luck with your Railway deployment! 🚂✨
