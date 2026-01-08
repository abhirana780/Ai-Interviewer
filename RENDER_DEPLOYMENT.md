# 🎨 Render.com Deployment Guide - FREE TIER!

## ✅ Why Render?

- ✅ **FREE tier** (no credit card needed to start)
- ✅ Automatic SSL/HTTPS
- ✅ Easy GitHub integration
- ✅ Good for testing and small projects

**Note**: Free tier spins down after 15 min of inactivity (takes ~30 sec to wake up)

---

## 🚀 Deploy to Render (25 minutes)

### Step 1: Create Render Account (2 min)

1. Go to: **https://render.com**
2. Click **"Get Started"**
3. Sign up with **GitHub** (recommended)
4. Verify your email

---

### Step 2: Deploy Backend (12 min)

#### 2.1 Create Web Service

1. In Render dashboard, click **"New +"**
2. Select **"Web Service"**
3. Click **"Connect account"** to link GitHub
4. Find and select: **`abhirana780/Ai-Interviewer`**
5. Click **"Connect"**

#### 2.2 Configure Backend

Fill in the form:

**Name:**
```
ai-interviewer-backend
```

**Root Directory:**
```
backend
```

**Environment:**
```
Python 3
```

**Build Command:**
```
pip install -r requirements-light.txt
```

**Start Command:**
```
gunicorn app:app --bind 0.0.0.0:$PORT
```

**Instance Type:**
```
Free
```
*(You can upgrade to paid later: $7/month)*

#### 2.3 Add Environment Variables

Scroll down to **"Environment Variables"** section.

Click **"Add Environment Variable"** for each:

| Key | Value |
|-----|-------|
| `JWT_SECRET_KEY` | `46c44fffac1ce5bfd23fd98202e9d0e1f2a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7` |
| `HF_API_KEY` | `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` |
| `ALLOWED_ORIGINS` | `*` |
| `FLASK_ENV` | `production` |
| `FLASK_DEBUG` | `False` |

#### 2.4 Deploy

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes)
3. Watch the logs for any errors

#### 2.5 Get Backend URL

Once deployed:
1. Your backend URL will be shown at the top
2. Format: `https://ai-interviewer-backend.onrender.com`
3. **Copy this URL** - you'll need it for frontend!

#### 2.6 Test Backend

```bash
curl https://your-backend-url.onrender.com/health
```

Expected: `{"status":"healthy","time":...}`

---

### Step 3: Deploy Frontend (10 min)

#### 3.1 Create Static Site

1. Click **"New +"**
2. Select **"Static Site"**
3. Select **same repository**: `abhirana780/Ai-Interviewer`
4. Click **"Connect"**

#### 3.2 Configure Frontend

**Name:**
```
ai-interviewer-frontend
```

**Root Directory:**
```
frontend-new
```

**Build Command:**
```
npm install && npm run build
```

**Publish Directory:**
```
dist
```

#### 3.3 Add Environment Variable

Click **"Advanced"** → **"Add Environment Variable"**

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://your-backend-url.onrender.com` |

**Replace** with your actual backend URL from Step 2.5!

#### 3.4 Deploy

1. Click **"Create Static Site"**
2. Wait for deployment (3-5 minutes)
3. Watch the build logs

#### 3.5 Get Frontend URL

Once deployed:
1. Your frontend URL will be shown
2. Format: `https://ai-interviewer-frontend.onrender.com`
3. **This is your live app URL!**

---

### Step 4: Update CORS (2 min)

1. Go to **Backend service** in Render
2. Click **"Environment"** in left sidebar
3. Find `ALLOWED_ORIGINS`
4. Click **"Edit"**
5. Replace `*` with your frontend URL:
   ```
   https://ai-interviewer-frontend.onrender.com
   ```
6. Click **"Save Changes"**

Render will automatically redeploy the backend.

---

## 🧪 Test Your Deployment

### Test Backend
```bash
curl https://your-backend-url.onrender.com/health
```

### Test Frontend
1. Open: `https://your-frontend-url.onrender.com`
2. Check browser console (F12) for errors
3. Try the full flow:
   - Register
   - Login
   - Start interview
   - Answer questions

---

## 💰 Cost

**Free Tier:**
- ✅ Free forever
- ⚠️ Spins down after 15 min inactivity
- ⚠️ 750 hours/month limit
- ⚠️ Slower performance

**Paid Tier ($7/month per service):**
- ✅ Always on
- ✅ Better performance
- ✅ No limits

**Total for this project:**
- Free: $0/month
- Paid: $14/month (backend + frontend)

---

## 🐛 Troubleshooting

### Issue: Build fails with "Module not found"

**Fix:**
- Check build command uses `requirements-light.txt`
- View build logs for specific error
- Ensure `requirements-light.txt` exists in backend folder

### Issue: "Application failed to start"

**Fix:**
1. Check start command is correct
2. View logs in Render dashboard
3. Ensure all environment variables are set

### Issue: CORS errors

**Fix:**
- Update `ALLOWED_ORIGINS` with exact frontend URL
- No trailing slash
- Redeploy backend

### Issue: Frontend shows blank page

**Fix:**
1. Check `VITE_API_URL` is set correctly
2. Check browser console for errors
3. Verify backend is running

### Issue: "Service unavailable" (Free tier)

**Explanation:**
- Free tier spins down after 15 min
- First request takes ~30 sec to wake up
- This is normal for free tier

**Fix:**
- Wait 30 seconds and refresh
- Or upgrade to paid tier ($7/month)

---

## 📊 Free Tier Limitations

| Feature | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Cost** | $0/month | $7/month |
| **Uptime** | Spins down after 15 min | Always on |
| **Performance** | Slower | Faster |
| **Build Time** | Limited | Unlimited |
| **SSL** | ✅ Yes | ✅ Yes |
| **Custom Domain** | ✅ Yes | ✅ Yes |

---

## 🔄 Updating Your App

When you push changes to GitHub:

1. Render **automatically detects** the push
2. **Auto-deploys** the new version
3. No manual action needed!

To disable auto-deploy:
- Go to service → Settings → Auto-Deploy → Toggle off

---

## 📈 Upgrading to Paid

When ready to upgrade:

1. Go to service in Render
2. Click **"Settings"**
3. Scroll to **"Instance Type"**
4. Select **"Starter"** ($7/month)
5. Click **"Save Changes"**

Benefits:
- Always on (no spin down)
- Better performance
- More resources

---

## ✅ Deployment Checklist

- [ ] Render account created
- [ ] Backend web service created
- [ ] Backend environment variables added (5 variables)
- [ ] Backend deployed successfully
- [ ] Backend URL copied
- [ ] Backend health check passing
- [ ] Frontend static site created
- [ ] Frontend environment variable added (VITE_API_URL)
- [ ] Frontend deployed successfully
- [ ] Frontend URL copied
- [ ] CORS updated with frontend URL
- [ ] Full user flow tested
- [ ] No errors in browser console

---

## 🎯 Your Deployment Info

**GitHub Repository:**
```
https://github.com/abhirana780/Ai-Interviewer
```

**Backend URL (after deployment):**
```
https://ai-interviewer-backend.onrender.com
```

**Frontend URL (after deployment):**
```
https://ai-interviewer-frontend.onrender.com
```

**Environment Variables:**
```env
JWT_SECRET_KEY=46c44fffac1ce5bfd23fd98202e9d0e1f2a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7
HF_API_KEY=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
ALLOWED_ORIGINS=https://ai-interviewer-frontend.onrender.com
FLASK_ENV=production
FLASK_DEBUG=False
```

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Render Community**: https://community.render.com
- **Status Page**: https://status.render.com

---

## 🎉 Success!

Once deployed, your AI Interviewer will be live at:
```
https://ai-interviewer-frontend.onrender.com
```

**Time**: 25 minutes  
**Cost**: FREE (or $14/month for paid)  
**Difficulty**: ⭐ Easy

Good luck! 🚀
