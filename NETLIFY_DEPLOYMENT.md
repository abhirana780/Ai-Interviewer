# 🌐 Netlify Deployment Guide - FREE TIER!

## ✅ Why Netlify?

- ✅ **FREE tier** (100GB bandwidth/month)
- ✅ Automatic HTTPS
- ✅ Continuous deployment from GitHub
- ✅ Fast global CDN
- ✅ Easy custom domains
- ✅ Perfect for React/Vite apps

**Note**: Netlify is for **frontend only**. Backend needs separate hosting.

---

## 🚀 Complete Deployment (Frontend + Backend)

### Architecture:
```
Frontend (Netlify) ←→ Backend (PythonAnywhere or Local)
```

---

## Part 1: Deploy Frontend to Netlify (10 min)

### Step 1: Prepare Frontend (2 min)

#### 1.1 Create `netlify.toml` Configuration

Create this file in `frontend-new` folder:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[build.environment]
  NODE_VERSION = "18"
```

#### 1.2 Update `.gitignore`

Make sure `frontend-new/.gitignore` includes:
```
node_modules
dist
.env.local
```

---

### Step 2: Deploy to Netlify (8 min)

#### 2.1 Sign Up / Login

1. Go to: **https://netlify.com**
2. Click **"Sign up"** or **"Log in"**
3. Choose **"GitHub"** (recommended)
4. Authorize Netlify

#### 2.2 Create New Site

1. Click **"Add new site"** → **"Import an existing project"**
2. Choose **"Deploy with GitHub"**
3. Select repository: **`abhirana780/Ai-Interviewer`**
4. Click **"Authorize"** if prompted

#### 2.3 Configure Build Settings

**Site settings:**

| Setting | Value |
|---------|-------|
| **Branch to deploy** | `main` |
| **Base directory** | `frontend-new` |
| **Build command** | `npm run build` |
| **Publish directory** | `frontend-new/dist` |

#### 2.4 Add Environment Variable

Click **"Show advanced"** → **"New variable"**

**For now, use local backend:**
```
VITE_API_URL = http://localhost:7860
```

**Or if you have a deployed backend:**
```
VITE_API_URL = https://your-backend-url.com
```

#### 2.5 Deploy!

1. Click **"Deploy site"**
2. Wait 2-5 minutes for build
3. Watch the deploy logs

#### 2.6 Get Your URL

Once deployed, you'll get a URL like:
```
https://random-name-123.netlify.app
```

You can customize this later!

---

## Part 2: Deploy Backend (Choose One)

### Option A: PythonAnywhere (FREE, Always-On) ⭐ Recommended

**Free tier includes:**
- ✅ Always-on web app
- ✅ 512MB RAM
- ✅ No credit card required

#### Steps:

1. **Sign up**: https://www.pythonanywhere.com/registration/register/beginner/
2. **Upload code**: Use Git or file upload
3. **Configure web app**:
   - Python version: 3.10
   - WSGI file: Point to `app.py`
   - Virtual environment: Create and install requirements
4. **Set environment variables** in WSGI config
5. **Reload** web app

**Your backend URL**: `https://yourusername.pythonanywhere.com`

#### Detailed PythonAnywhere Guide:

```bash
# In PythonAnywhere Bash console:
git clone https://github.com/abhirana780/Ai-Interviewer.git
cd Ai-Interviewer/backend
mkvirtualenv --python=/usr/bin/python3.10 ai-interviewer
pip install -r requirements-light.txt
```

**WSGI Configuration** (`/var/www/yourusername_pythonanywhere_com_wsgi.py`):
```python
import sys
import os

# Add your project directory
project_home = '/home/yourusername/Ai-Interviewer/backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['JWT_SECRET_KEY'] = '46c44fffac1ce5bfd23fd98202e9d0e1f2a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7'
os.environ['HF_API_KEY'] = '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'
os.environ['ALLOWED_ORIGINS'] = 'https://your-netlify-url.netlify.app'
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = 'False'

# Import Flask app
from app import app as application
```

---

### Option B: Local Backend (FREE, For Testing)

**Use ngrok to expose local backend:**

1. **Start backend locally**:
   ```bash
   cd backend
   python app.py
   ```

2. **Install ngrok**: https://ngrok.com/download

3. **Expose backend**:
   ```bash
   ngrok http 7860
   ```

4. **Copy the URL** (e.g., `https://abc123.ngrok.io`)

5. **Update Netlify environment variable**:
   - Go to Netlify dashboard
   - Site settings → Environment variables
   - Edit `VITE_API_URL` to ngrok URL
   - Redeploy site

**Note**: ngrok URL changes each time you restart. Free tier has limitations.

---

### Option C: Paid Backend Hosting

If PythonAnywhere free tier is not enough:

| Platform | Cost | Best For |
|----------|------|----------|
| **Railway** | $5/mo | Easiest |
| **Render** | $7/mo | Reliable |
| **DigitalOcean** | $6/mo | More control |

---

## Part 3: Connect Frontend to Backend

### Step 1: Update Netlify Environment Variable

1. Go to Netlify dashboard
2. Click your site
3. **Site settings** → **Environment variables**
4. Edit `VITE_API_URL`:
   ```
   https://yourusername.pythonanywhere.com
   ```
   Or your backend URL

### Step 2: Update Backend CORS

In your backend `.env` or PythonAnywhere WSGI config:
```env
ALLOWED_ORIGINS=https://your-site-name.netlify.app
```

### Step 3: Redeploy

**Netlify**: 
- Go to **Deploys** tab
- Click **"Trigger deploy"** → **"Clear cache and deploy site"**

**PythonAnywhere**:
- Go to **Web** tab
- Click **"Reload"** button

---

## 🧪 Test Your Deployment

### Test Frontend
1. Open: `https://your-site-name.netlify.app`
2. Check browser console (F12) for errors
3. Verify no CORS errors

### Test Backend
```bash
curl https://yourusername.pythonanywhere.com/health
```

Expected: `{"status":"healthy","time":...}`

### Test Full Flow
1. Register account
2. Login
3. Start interview
4. Answer questions
5. Check feedback

---

## 🎨 Customize Your Netlify Site

### Change Site Name

1. Go to **Site settings** → **Site details**
2. Click **"Change site name"**
3. Enter new name: `ai-interviewer` (if available)
4. Your URL becomes: `https://ai-interviewer.netlify.app`

### Add Custom Domain

1. Buy domain (e.g., from Namecheap)
2. Go to **Domain settings** → **Add custom domain**
3. Follow DNS configuration instructions
4. SSL certificate is automatic!

---

## 💰 Cost Breakdown

### FREE Option:
- **Netlify Frontend**: FREE (100GB bandwidth/month)
- **PythonAnywhere Backend**: FREE (always-on)
- **Total**: **$0/month** ✅

### Paid Option (Better Performance):
- **Netlify Frontend**: FREE
- **Railway Backend**: $5/month
- **Total**: **$5/month**

---

## 🔧 Netlify Configuration Files

### `netlify.toml` (in frontend-new folder)

```toml
[build]
  command = "npm run build"
  publish = "dist"
  
[build.environment]
  NODE_VERSION = "18"
  
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
```

---

## 🐛 Troubleshooting

### Issue: Build fails on Netlify

**Check:**
1. Build command is correct: `npm run build`
2. Publish directory is correct: `frontend-new/dist`
3. Base directory is set: `frontend-new`
4. View build logs for specific error

**Common fixes:**
- Clear cache and redeploy
- Check `package.json` scripts
- Ensure all dependencies are in `package.json`

### Issue: "Page not found" on refresh

**Fix**: Add `netlify.toml` with redirects (see above)

### Issue: CORS errors

**Fix:**
1. Update backend `ALLOWED_ORIGINS` with Netlify URL
2. No trailing slash in URL
3. Redeploy backend

### Issue: Frontend shows "Failed to fetch"

**Fix:**
1. Check `VITE_API_URL` environment variable
2. Verify backend is running
3. Test backend URL directly
4. Check browser console for exact error

---

## 📊 Netlify Free Tier Limits

| Feature | Free Tier | Pro Tier |
|---------|-----------|----------|
| **Bandwidth** | 100GB/month | 1TB/month |
| **Build Minutes** | 300/month | 1000/month |
| **Sites** | Unlimited | Unlimited |
| **Team Members** | 1 | Unlimited |
| **Custom Domain** | ✅ Yes | ✅ Yes |
| **SSL** | ✅ Auto | ✅ Auto |

**For this project**: Free tier is more than enough!

---

## 🚀 Deployment Checklist

### Netlify (Frontend)
- [ ] `netlify.toml` created in frontend-new
- [ ] Netlify account created
- [ ] Repository connected
- [ ] Build settings configured
- [ ] Environment variable added (VITE_API_URL)
- [ ] Site deployed successfully
- [ ] Site URL copied

### Backend (Choose One)
- [ ] PythonAnywhere account created
- [ ] Code uploaded
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] WSGI configured
- [ ] Environment variables set
- [ ] Web app reloaded
- [ ] Backend URL copied

### Integration
- [ ] Netlify VITE_API_URL updated with backend URL
- [ ] Backend ALLOWED_ORIGINS updated with Netlify URL
- [ ] Both services redeployed
- [ ] Full user flow tested
- [ ] No CORS errors
- [ ] No console errors

---

## 🎯 Quick Start Summary

### 1. Create `netlify.toml` in frontend-new
### 2. Deploy to Netlify
- Import from GitHub
- Base: `frontend-new`
- Build: `npm run build`
- Publish: `frontend-new/dist`
- Env: `VITE_API_URL=http://localhost:7860` (temporary)

### 3. Deploy Backend to PythonAnywhere
- Sign up (free)
- Clone repo
- Setup virtualenv
- Configure WSGI
- Set environment variables

### 4. Connect Them
- Update Netlify `VITE_API_URL` with PythonAnywhere URL
- Update backend `ALLOWED_ORIGINS` with Netlify URL
- Redeploy both

---

## 📞 Support

- **Netlify Docs**: https://docs.netlify.com
- **Netlify Community**: https://answers.netlify.com
- **PythonAnywhere**: https://help.pythonanywhere.com

---

**Time**: 20-30 minutes  
**Cost**: FREE (with PythonAnywhere)  
**Difficulty**: ⭐⭐ Medium

Good luck! 🚀
