# Backend Deployment Configuration

## Environment Variables Required

```
JWT_SECRET_KEY=your-super-secret-key-minimum-32-characters
HF_API_KEY=your-huggingface-api-key
PORT=7860
```

## Deployment Platforms

### Render.com
1. Create new Web Service
2. Connect your repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. Add environment variables
6. Deploy

### Railway.app
1. Create new project
2. Add Python service
3. Connect repository
4. Set root directory to `backend`
5. Add environment variables
6. Deploy automatically

### Heroku
```bash
heroku create your-app-name
heroku config:set JWT_SECRET_KEY=your-secret-key
heroku config:set HF_API_KEY=your-hf-key
git push heroku main
```

### Docker Deployment
```bash
docker build -t ai-interviewer-backend .
docker run -p 7860:7860 \
  -e JWT_SECRET_KEY=your-secret \
  -e HF_API_KEY=your-key \
  ai-interviewer-backend
```

## CORS Configuration

Update `app.py` CORS origins for production:
```python
CORS(app, origins=["https://your-frontend-domain.com"], supports_credentials=True)
```

## Database

- SQLite databases will be created automatically
- For production, consider PostgreSQL or MySQL
- Databases persist in the deployment environment
