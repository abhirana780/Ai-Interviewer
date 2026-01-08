# 🎯 AI Interviewer - Separated Frontend & Backend

A modern AI-powered interview platform with face detection, real-time feedback, and comprehensive analytics.

## 🏗️ Project Structure

```
ai-interviewer/
├── backend/                 # Python Flask API
│   ├── app.py              # Main application
│   ├── interviewer.py      # Interview logic
│   ├── requirements.txt    # Python dependencies
│   ├── database/           # Database helpers
│   │   ├── db_helper.py
│   │   └── auth_helper.py
│   ├── model/              # AI models
│   └── utils/              # Utility functions
│
├── frontend-new/           # React Frontend
│   ├── src/
│   │   ├── pages/          # Page components
│   │   │   ├── Login.jsx
│   │   │   ├── Register.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   └── Interview.jsx
│   │   ├── App.jsx         # Main app component
│   │   ├── index.css       # Global styles
│   │   └── main.jsx        # Entry point
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
└── frontend/               # Old static frontend (legacy)
```

## ✨ Features

### 🔐 Authentication
- User registration with email validation
- Secure login with JWT tokens
- Password hashing with bcrypt
- Protected routes and sessions

### 🎨 Modern UI/UX
- **Glassmorphism design** with blur effects
- **Gradient backgrounds** and smooth animations
- **Responsive layout** for all devices
- **Dark theme** with vibrant accents
- **Premium aesthetics** with micro-interactions

### 🤖 AI Interview
- Real-time face detection using face-api.js
- Multiple face warning system
- Video recording and transcription
- AI-powered question generation
- Instant feedback and scoring
- Technology-specific questions

### 📊 Dashboard
- User statistics and progress tracking
- Technology selection cards
- Custom topic input
- Interview history

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Create virtual environment:**
```bash
python -m venv venv
```

3. **Activate virtual environment:**
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

4. **Install dependencies:**
```bash
pip install -r requirements.txt
```

5. **Set environment variables:**
Create a `.env` file in the backend directory:
```env
JWT_SECRET_KEY=your-super-secret-key-change-this
HF_API_KEY=your-huggingface-api-key
```

6. **Run the backend:**
```bash
python app.py
```

Backend will run on `http://localhost:7860`

### Frontend Setup

1. **Navigate to frontend directory:**
```bash
cd frontend-new
```

2. **Install dependencies:**
```bash
npm install
```

3. **Set environment variables:**
Create a `.env` file in the frontend-new directory:
```env
VITE_API_URL=http://localhost:7860
```

4. **Run the development server:**
```bash
npm run dev
```

Frontend will run on `http://localhost:5173`

## 📦 Deployment

### Backend Deployment (Python/Flask)

#### Option 1: Render / Railway / Heroku

1. **Create `Procfile`:**
```
web: gunicorn app:app
```

2. **Update `requirements.txt` to include:**
```
gunicorn
```

3. **Set environment variables** in your hosting platform:
   - `JWT_SECRET_KEY`
   - `HF_API_KEY`

4. **Deploy** using Git or platform CLI

#### Option 2: Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "app:app"]
```

### Frontend Deployment (React/Vite)

#### Option 1: Vercel / Netlify

1. **Build the project:**
```bash
npm run build
```

2. **Deploy the `dist` folder** to Vercel/Netlify

3. **Set environment variable:**
   - `VITE_API_URL=https://your-backend-url.com`

#### Option 2: Static Hosting (AWS S3, GitHub Pages)

1. **Build:**
```bash
npm run build
```

2. **Upload `dist` folder** to your hosting service

3. **Configure** environment variables before build

## 🔧 Configuration

### Backend Configuration

**`backend/.env`:**
```env
# JWT Secret (CHANGE THIS!)
JWT_SECRET_KEY=your-secret-key-here

# Hugging Face API Key
HF_API_KEY=your-hf-api-key

# Database paths (optional, defaults to local)
DB_PATH=database/interviews.db
AUTH_DB_PATH=database/auth.db
```

### Frontend Configuration

**`frontend-new/.env`:**
```env
# Backend API URL
VITE_API_URL=http://localhost:7860

# For production
# VITE_API_URL=https://your-backend-api.com
```

## 🎨 Design System

### Color Palette
- **Primary Gradient:** `#667eea → #764ba2`
- **Secondary Gradient:** `#f093fb → #f5576c`
- **Success Gradient:** `#4facfe → #00f2fe`
- **Background:** `#0f0f23` (Dark)
- **Cards:** Glassmorphism with blur

### Typography
- **Primary Font:** Inter
- **Display Font:** Outfit
- **Monospace:** Courier New (for timers)

### Components
- Glassmorphism cards
- Gradient buttons with hover effects
- Smooth animations and transitions
- Responsive grid layouts

## 🔒 Security

- **Password Hashing:** bcrypt with salt
- **JWT Tokens:** 7-day expiration
- **CORS:** Configured for cross-origin requests
- **Input Validation:** Server-side validation
- **SQL Injection Protection:** Parameterized queries

## 📱 Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Required Permissions:**
- Camera access
- Microphone access

## 🐛 Troubleshooting

### Backend Issues

**Database errors:**
```bash
# Delete and recreate databases
rm backend/database/*.db
python backend/app.py
```

**Port already in use:**
```bash
# Change port in app.py
app.run(host="127.0.0.1", port=8000)
```

### Frontend Issues

**API connection failed:**
- Check `.env` file has correct `VITE_API_URL`
- Ensure backend is running
- Check CORS configuration

**Face detection not working:**
- Ensure camera permissions are granted
- Check if face-api.js models are loaded
- Try using HTTPS (required for some browsers)

## 📝 API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user (requires JWT)

### Interview
- `POST /start` - Start interview session
- `POST /answer` - Submit answer with video
- `POST /tts` - Generate text-to-speech
- `GET /transcript/<session_id>` - Get interview transcript

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - feel free to use this project for learning and development.

## 🙏 Acknowledgments

- **face-api.js** for face detection
- **Whisper** for speech-to-text
- **GPT4All** for AI question generation
- **React** and **Vite** for frontend
- **Flask** for backend API

---

**Built with ❤️ for better interview preparation**
