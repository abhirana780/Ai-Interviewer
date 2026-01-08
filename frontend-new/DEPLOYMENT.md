# Frontend Deployment Configuration

## Build for Production

```bash
npm run build
```

This creates a `dist` folder with optimized production files.

## Environment Variables

Create `.env.production`:
```
VITE_API_URL=https://your-backend-api.com
```

## Deployment Platforms

### Vercel (Recommended)
1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel`
3. Follow prompts
4. Set environment variable: `VITE_API_URL`
5. Deploy: `vercel --prod`

**Or use Vercel Dashboard:**
1. Import Git repository
2. Framework: Vite
3. Root directory: `frontend-new`
4. Add environment variable
5. Deploy

### Netlify
1. Build command: `npm run build`
2. Publish directory: `dist`
3. Add environment variable: `VITE_API_URL`
4. Deploy

**Netlify CLI:**
```bash
npm install -g netlify-cli
netlify deploy --prod
```

### GitHub Pages
1. Install gh-pages: `npm install --save-dev gh-pages`
2. Add to `package.json`:
```json
{
  "scripts": {
    "predeploy": "npm run build",
    "deploy": "gh-pages -d dist"
  },
  "homepage": "https://yourusername.github.io/repo-name"
}
```
3. Run: `npm run deploy`

### AWS S3 + CloudFront
```bash
# Build
npm run build

# Upload to S3
aws s3 sync dist/ s3://your-bucket-name

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_ID --paths "/*"
```

### Firebase Hosting
```bash
npm install -g firebase-tools
firebase login
firebase init hosting
# Select dist as public directory
firebase deploy
```

## Important Notes

### Base URL Configuration
If deploying to a subdirectory, update `vite.config.js`:
```javascript
export default defineConfig({
  base: '/your-subdirectory/',
  // ...
})
```

### CORS
Ensure backend CORS allows your frontend domain:
```python
CORS(app, origins=["https://your-frontend.vercel.app"])
```

### HTTPS Required
Face detection requires HTTPS in production. All recommended platforms provide SSL certificates automatically.

## Testing Production Build Locally

```bash
npm run build
npm run preview
```

Visit `http://localhost:4173` to test the production build.
