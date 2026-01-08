# 🌐 Netlify Deployment - Quick Reference

## ✅ What You Have

- ✅ Code on GitHub: `abhirana780/Ai-Interviewer`
- ✅ `netlify.toml` created in `frontend-new`
- ✅ All credentials ready

---

## 🚀 Deploy Frontend to Netlify (10 min)

### Step 1: Go to Netlify
https://netlify.com → Sign up with GitHub

### Step 2: Import Project
1. **Add new site** → **Import an existing project**
2. **Deploy with GitHub**
3. Select: `abhirana780/Ai-Interviewer`

### Step 3: Configure
| Setting | Value |
|---------|-------|
| Base directory | `frontend-new` |
| Build command | `npm run build` |
| Publish directory | `frontend-new/dist` |

### Step 4: Add Environment Variable
**Show advanced** → **New variable**
```
VITE_API_URL = http://localhost:7860
```
*(Update later with backend URL)*

### Step 5: Deploy
Click **Deploy site** → Wait 3-5 min

---

## 🔧 Backend Options

### Option A: PythonAnywhere (FREE) ⭐
- Sign up: https://pythonanywhere.com
- Always-on, no credit card
- See `NETLIFY_DEPLOYMENT.md` for setup

### Option B: Local + ngrok (FREE, Testing)
```bash
# Terminal 1
cd backend
python app.py

# Terminal 2
ngrok http 7860
```
Copy ngrok URL → Update Netlify `VITE_API_URL`

### Option C: Railway ($5/month)
- Most reliable
- Easy setup
- See `RAILWAY_DEPLOYMENT.md`

---

## 🔗 Connect Frontend & Backend

1. **Get backend URL** (PythonAnywhere/ngrok/Railway)
2. **Update Netlify**:
   - Site settings → Environment variables
   - Edit `VITE_API_URL` → Your backend URL
   - Trigger deploy
3. **Update backend CORS**:
   - Set `ALLOWED_ORIGINS` to your Netlify URL
   - Redeploy backend

---

## 💰 Cost

**FREE Option:**
- Netlify: FREE
- PythonAnywhere: FREE
- **Total: $0/month** ✅

**Paid Option:**
- Netlify: FREE
- Railway: $5/month
- **Total: $5/month**

---

## ✅ Quick Checklist

- [ ] Netlify account created
- [ ] Site imported from GitHub
- [ ] Build settings configured
- [ ] Environment variable added
- [ ] Site deployed
- [ ] Backend deployed (choose option)
- [ ] URLs connected
- [ ] CORS updated
- [ ] Tested end-to-end

---

**Full Guide**: `NETLIFY_DEPLOYMENT.md`  
**Your Netlify URL**: `https://your-site.netlify.app`

🚀 **Ready to deploy!**
