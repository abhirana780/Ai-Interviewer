import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import * as faceapi from 'face-api.js';
import './Interview.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:7860';

function Interview() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [faceCount, setFaceCount] = useState(0);
  const [modelsLoaded, setModelsLoaded] = useState(false);
  const [interviewStarted, setInterviewStarted] = useState(false);
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [warning, setWarning] = useState(null);
  const [botAudioUrl, setBotAudioUrl] = useState(null);

  // Load face-api models
  useEffect(() => {
    const loadModels = async () => {
      try {
        const MODEL_URL = '/models';
        await Promise.all([
          faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
          faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
          faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
        ]);
        setModelsLoaded(true);
      } catch (error) {
        console.error('Error loading face-api models:', error);
        // Continue without face detection if models fail to load
        setModelsLoaded(true);
      }
    };
    loadModels();
  }, []);

  // Start webcam
  useEffect(() => {
    const startWebcam = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720 },
          audio: true
        });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      } catch (error) {
        console.error('Error accessing webcam:', error);
        setWarning('Unable to access camera. Please check permissions.');
      }
    };
    startWebcam();

    return () => {
      if (videoRef.current && videoRef.current.srcObject) {
        videoRef.current.srcObject.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Face detection loop
  useEffect(() => {
    if (!modelsLoaded || !videoRef.current) return;

    const detectFaces = async () => {
      try {
        const detections = await faceapi.detectAllFaces(
          videoRef.current,
          new faceapi.TinyFaceDetectorOptions()
        );
        
        setFaceCount(detections.length);

        // Show warnings
        if (detections.length === 0) {
          setWarning('⚠️ No face detected. Please ensure you are visible to the camera.');
        } else if (detections.length > 1) {
          setWarning('⚠️ Multiple faces detected. Please ensure you are alone.');
        } else {
          setWarning(null);
        }
      } catch (error) {
        console.error('Face detection error:', error);
      }
    };

    const interval = setInterval(detectFaces, 1000);
    return () => clearInterval(interval);
  }, [modelsLoaded]);

  // Recording timer
  useEffect(() => {
    let interval;
    if (isRecording) {
      interval = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
    } else {
      setRecordingTime(0);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  // Start interview
  const startInterview = async () => {
    setLoading(true);
    try {
      const selectedTech = localStorage.getItem('selectedTech') || 'Software Engineer';
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      
      const response = await axios.post(`${API_URL}/start`, {
        track: selectedTech,
        candidate_name: user.name || 'Candidate'
      });

      setSessionId(response.data.session_id);
      setCurrentQuestion(response.data.question);
      setChatHistory([{ type: 'bot', text: response.data.question }]);
      setInterviewStarted(true);

      // Play TTS if available
      if (response.data.tts_url) {
        setBotAudioUrl(`${API_URL}${response.data.tts_url}`);
      }
    } catch (error) {
      console.error('Error starting interview:', error);
      setWarning('Failed to start interview. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Start recording
  const startRecording = async () => {
    try {
      const stream = videoRef.current.srcObject;
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'video/webm;codecs=vp9'
      });

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      setWarning('Failed to start recording. Please try again.');
    }
  };

  // Stop recording and submit
  const stopRecording = async () => {
    if (!mediaRecorderRef.current || !isRecording) return;

    setIsRecording(false);
    mediaRecorderRef.current.stop();

    mediaRecorderRef.current.onstop = async () => {
      const blob = new Blob(chunksRef.current, { type: 'video/webm' });
      await submitAnswer(blob);
    };
  };

  // Submit answer
  const submitAnswer = async (videoBlob) => {
    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('media', videoBlob, 'answer.webm');

      const response = await axios.post(`${API_URL}/answer`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      // Update chat history
      const transcribedAnswer = response.data.transcribed_answer || 'Answer submitted';
      setChatHistory(prev => [
        ...prev,
        { type: 'user', text: transcribedAnswer }
      ]);

      if (response.data.next_question) {
        setCurrentQuestion(response.data.next_question);
        setChatHistory(prev => [
          ...prev,
          { type: 'bot', text: response.data.next_question }
        ]);

        // Play TTS if available
        if (response.data.tts_url) {
          setBotAudioUrl(`${API_URL}${response.data.tts_url}`);
        }
      } else if (response.data.final_report) {
        // Interview completed
        setChatHistory(prev => [
          ...prev,
          { type: 'bot', text: response.data.final_report }
        ]);
        setTimeout(() => {
          navigate('/dashboard');
        }, 5000);
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
      setWarning('Failed to submit answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Format time
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="interview-container">
      {/* Header */}
      <header className="interview-header glass-card">
        <div className="header-content">
          <h2>AI Interview Session</h2>
          <button onClick={() => navigate('/dashboard')} className="btn btn-secondary btn-sm">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 12H5M5 12L12 19M5 12L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Back to Dashboard
          </button>
        </div>
      </header>

      {/* Warning Banner */}
      {warning && (
        <div className="warning-banner slide-in-right">
          {warning}
        </div>
      )}

      {/* Main Content */}
      <main className="interview-main">
        <div className="interview-layout">
          {/* Video Section */}
          <div className="video-section">
            <div className="video-grid">
              {/* User Video */}
              <div className="video-pane glass-card">
                <div className="video-wrapper">
                  <video ref={videoRef} autoPlay muted playsInline />
                  <canvas ref={canvasRef} />
                  <div className="face-count-badge">
                    Faces: {faceCount}
                  </div>
                </div>
                <div className="video-label">You</div>
              </div>

              {/* Bot Video */}
              <div className="video-pane glass-card">
                <div className="video-wrapper bot-video">
                  <div className="bot-avatar">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="4" y="8" width="16" height="12" rx="2" stroke="url(#gradient-bot)" strokeWidth="2"/>
                      <path d="M9 16H9.01M15 16H15.01M9 12H15" stroke="url(#gradient-bot)" strokeWidth="2" strokeLinecap="round"/>
                      <path d="M8 8V6C8 4.89543 8.89543 4 10 4H14C15.1046 4 16 4.89543 16 6V8" stroke="url(#gradient-bot)" strokeWidth="2"/>
                      <defs>
                        <linearGradient id="gradient-bot" x1="4" y1="4" x2="20" y2="20">
                          <stop offset="0%" stopColor="#667eea"/>
                          <stop offset="100%" stopColor="#764ba2"/>
                        </linearGradient>
                      </defs>
                    </svg>
                  </div>
                  {botAudioUrl && <audio src={botAudioUrl} autoPlay />}
                </div>
                <div className="video-label">AI Interviewer</div>
              </div>
            </div>

            {/* Controls */}
            <div className="controls-section glass-card">
              {!interviewStarted ? (
                <button
                  onClick={startInterview}
                  className="btn btn-primary btn-lg"
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <div className="spinner-small"></div>
                      Starting...
                    </>
                  ) : (
                    <>
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <polygon points="5 3 19 12 5 21 5 3" fill="currentColor"/>
                      </svg>
                      Start Interview
                    </>
                  )}
                </button>
              ) : (
                <div className="recording-controls">
                  {!isRecording ? (
                    <button
                      onClick={startRecording}
                      className="btn btn-success btn-lg"
                      disabled={loading}
                    >
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <circle cx="12" cy="12" r="9" fill="currentColor"/>
                      </svg>
                      Record Answer
                    </button>
                  ) : (
                    <button
                      onClick={stopRecording}
                      className="btn btn-danger btn-lg"
                    >
                      <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect x="6" y="6" width="12" height="12" fill="currentColor"/>
                      </svg>
                      Submit Answer
                    </button>
                  )}
                  <div className="timer">
                    {isRecording && '🔴 '}
                    {formatTime(recordingTime)}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Chat Section */}
          <div className="chat-section glass-card">
            <h3>Interview Transcript</h3>
            <div className="chat-messages">
              {chatHistory.length === 0 ? (
                <div className="empty-state">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  <p>Start the interview to begin</p>
                </div>
              ) : (
                chatHistory.map((message, index) => (
                  <div
                    key={index}
                    className={`chat-message ${message.type} fade-in`}
                    style={{ animationDelay: `${index * 0.1}s` }}
                  >
                    <div className="message-avatar">
                      {message.type === 'bot' ? '🤖' : '👤'}
                    </div>
                    <div className="message-content">
                      <div className="message-header">
                        {message.type === 'bot' ? 'AI Interviewer' : 'You'}
                      </div>
                      <div className="message-text">{message.text}</div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default Interview;
