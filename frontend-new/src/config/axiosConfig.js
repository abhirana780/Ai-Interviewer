import axios from 'axios';

// Create axios instance with default config
const axiosInstance = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
        'Content-Type': 'application/json',
        // Skip ngrok browser warning for free tier
        'ngrok-skip-browser-warning': 'true',
    },
});

export default axiosInstance;
