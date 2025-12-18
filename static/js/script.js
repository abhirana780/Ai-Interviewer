let sessionId = null;
const chatEl = document.getElementById("chat");
const startBtn = document.getElementById("start");
const trackSel = document.getElementById("track");
const userCam = document.getElementById("userCam");
const recordBtn = document.getElementById("record");
const stopBtn = document.getElementById("stop");
const timerEl = document.getElementById("timer");
const botVoice = document.getElementById("botVoice");let isRecording = false;
let isUploading = false;

// Tab switching detection variables
let tabSwitchCount = 0;

// Make sessionId globally accessible
window.sessionId = sessionId;

// Get session ID from URL if present
function getSessionIdFromURL() {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get('session_id');
}

function addMsg(text, type, isHtml = false) {
    if (!text) return;
    const div = document.createElement("div");
    div.className = "msg " + type;
    if (isHtml) {
        div.innerHTML = text;
    } else {
        div.textContent = text;
    }
    chatEl.appendChild(div);
    chatEl.scrollTop = chatEl.scrollHeight;
}

function setDisabled(el, disabled) {
    if (el) el.disabled = !!disabled;
}

// Bot assets function removed as bot view was simplified

let mediaStream = null;
let mediaRecorder = null;
let recordedChunks = [];
let timerInterval = null;
let recordingStart = 0;

let recognition = null;
let transcriptBuffer = "";
let liveTranscriptDiv = null;

function initRecognition() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { return null; }
    recognition = new SR();
    recognition.lang = "en-US";
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.onresult = (event) => {
        try {
            let interim = "";
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const r = event.results[i];
                if (r.isFinal && r[0] && r[0].transcript) {
                    const t = r[0].transcript.trim();
                    if (t) transcriptBuffer += (transcriptBuffer ? " " : "") + t;
                } else if (r[0] && r[0].transcript) {
                    interim += r[0].transcript;
                }
            }
            // Update live display
            if (liveTranscriptDiv) {
                const finalText = transcriptBuffer ? transcriptBuffer : "";
                const interimText = interim ? " <span style='color:#888'>" + interim + "</span>" : "";
                liveTranscriptDiv.innerHTML = "<strong>Your answer:</strong> " + finalText + interimText;
            }
        } catch (_) {}
    };
    recognition.onerror = () => {};
    recognition.onend = () => {};
    return recognition;
}
function startRecognition() {
    if (!recognition) initRecognition();
    transcriptBuffer = "";
    
    // Create live transcript display
    if (!liveTranscriptDiv) {
        liveTranscriptDiv = document.createElement("div");
        liveTranscriptDiv.style.cssText = "background:#f0f9ff;border:1px solid #bae6fd;padding:10px;margin:10px 0;border-radius:6px;min-height:40px;font-size:14px;";
        chatEl.appendChild(liveTranscriptDiv);
    }
    liveTranscriptDiv.innerHTML = "<strong>Listening...</strong> <span style='color:#888'>Speak your answer</span>";
    
    try { recognition && recognition.start(); } catch (_) {}
}
function stopRecognition() {
    try { recognition && recognition.stop(); } catch (_) {}
    
    // Remove live display after recording
    if (liveTranscriptDiv && liveTranscriptDiv.parentNode) {
        setTimeout(() => {
            liveTranscriptDiv.remove();
            liveTranscriptDiv = null;
        }, 500);
    }
}


async function initCamera() {
    try {
        mediaStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        userCam.srcObject = mediaStream;
    } catch (_) {
        addMsg("System: Camera/mic unavailable.", "system");
    }
}

// Proctoring functionality completely removed

function formatTime(ms) {
    const total = Math.floor(ms / 1000);
    const m = String(Math.floor(total / 60)).padStart(2, "0");
    const s = String(total % 60).padStart(2, "0");
    return m + ":" + s;
}

function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    recordingStart = Date.now();
    timerEl.textContent = "00:00";
    timerEl.classList.add("on");
    timerInterval = setInterval(() => {
        timerEl.textContent = formatTime(Date.now() - recordingStart);
    }, 500);
}

function stopTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;
    timerEl.classList.remove("on");
    timerEl.textContent = "00:00";
}

function createRecorder() {
    if (!mediaStream) return null;
    const options = { mimeType: "video/webm;codecs=vp8,opus" };
    let rec;
    try {
        rec = new MediaRecorder(mediaStream, options);
    } catch (e) {
        try { rec = new MediaRecorder(mediaStream); } catch (err) { return null; }
    }
    return rec;
}

async function startRecording() {
    if (!sessionId) {
        addMsg("System: Please start the interview first.", "system");
        return;
    }
    if (isUploading) {
        addMsg("System: Please wait, uploading previous answer.", "system");
        return;
    }
    if (isRecording) {
        return;
    }
    if (!mediaStream) await initCamera();
    mediaRecorder = createRecorder();
    if (!mediaRecorder) {
        addMsg("System: Recording not supported in this browser.", "system");
        return;
    }
    recordedChunks = [];
    isRecording = true;
    mediaRecorder.ondataavailable = (e) => { if (e.data && e.data.size > 0) recordedChunks.push(e.data); };
    mediaRecorder.onstop = () => { isRecording = false; finalizeUpload(); };
    mediaRecorder.onerror = () => { addMsg("System: Recorder error.", "system"); isRecording = false; };
    setDisabled(recordBtn, true);
    setDisabled(stopBtn, true);
    startTimer();
    setTimeout(() => { setDisabled(stopBtn, false); }, 1000);
    addMsg("System: Recording started. Speak your answer.", "system");
    startRecognition();
    try { mediaRecorder.start(1000); } catch (_) { mediaRecorder.start(); }
}

function stopRecording() {
    try { stopRecognition(); } catch (_) {}
    setDisabled(stopBtn, true);
    stopTimer();
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
        try { mediaRecorder.stop(); } catch (_) {
            addMsg("System: Recorder stop failed, uploading...", "system");
            finalizeUpload();
        }
        setTimeout(() => {
            if (!isUploading && isRecording) {
                finalizeUpload();
            }
        }, 1000);
    } else {
        finalizeUpload();
    }
}

async function finalizeUpload() {
    if (isUploading) return;
    stopTimer();
    isUploading = true;
    const blob = new Blob(recordedChunks, { type: "video/webm" });
    recordedChunks = [];
    const form = new FormData();
    form.append("session_id", sessionId);
    if (blob && blob.size > 0) { form.append("media", blob, "answer.webm"); }
    const answerText = ((transcriptBuffer || "").trim()) || "[video_answer]";
    form.append("answer", answerText);
    
    // Show what user said
    if (answerText && answerText !== "[video_answer]") {
        addMsg("You: " + answerText, "me");
    } else {
        addMsg("You: [Recording uploaded - processing...]", "me");
    }
    
    addMsg("System: Uploading your answer...", "system");
    try {
        const res = await fetch("/answer", { method: "POST", body: form });
        if (res.status === 400) {
            addMsg("System: session_id missing. Start again.", "system");
            setDisabled(recordBtn, false);
            isUploading = false;
            return;
        }
        const data = await res.json();
        const score = typeof data.score !== "undefined" ? data.score : null;
        const feedback = data.feedback || "";

        if (score !== null) {
            // Create beautiful score display
            const scorePercent = Math.round((score / 5) * 100);
            let scoreColor = "#e53935"; // red for low scores
            let scoreBg = "#ffebee";
            let scoreLabel = "Needs Improvement";
            
            if (scorePercent >= 80) {
                scoreColor = "#1e8e3e";
                scoreBg = "#e6f4ea";
                scoreLabel = "Excellent";
            } else if (scorePercent >= 60) {
                scoreColor = "#f9ab00";
                scoreBg = "#fef7e0";
                scoreLabel = "Good";
            } else if (scorePercent >= 40) {
                scoreColor = "#e37400";
                scoreBg = "#feefc3";
                scoreLabel = "Fair";
            }
            
            const scoreHtml = `
                <div style="display:flex;align-items:center;gap:12px;padding:8px 0;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div style="font-size:32px;font-weight:700;color:${scoreColor};line-height:1;">${score}/5</div>
                        <div style="flex:1;">
                            <div style="font-weight:600;color:${scoreColor};font-size:14px;">${scoreLabel}</div>
                            <div style="background:${scoreBg};color:${scoreColor};font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;display:inline-block;margin-top:2px;">${scorePercent}%</div>
                        </div>
                    </div>
                </div>
                ${feedback ? `<div style="margin-top:8px;padding:8px 12px;background:#f8f9fa;border-left:3px solid ${scoreColor};border-radius:4px;font-size:13px;line-height:1.5;color:#495057;"><strong>Feedback:</strong> ${feedback}</div>` : ""}
            `;
            addMsg(scoreHtml, "score", true);
        }
        const nextQ = data.next_question || null;
        if (nextQ) {
            addMsg("Interviewer: " + nextQ, "bot");
            // Play TTS audio for next question if available
            if (data.tts_url && botVoice) {
                botVoice.src = data.tts_url;
                // Handle autoplay policies by attempting to play after user interaction
                const playPromise = botVoice.play();
                if (playPromise !== undefined) {
                    playPromise.catch(e => {
                        console.log("Audio play failed:", e);
                        // Try to play after a small delay
                        setTimeout(() => {
                            botVoice.play().catch(e2 => {
                                console.log("Audio play failed on retry:", e2);
                                // Show a message to the user that audio is not available
                                addMsg("System: Audio playback failed. Please check your browser settings or click anywhere to enable audio.", "system");
                            });
                        }, 100);
                    });
                }
            }
            setDisabled(recordBtn, false);
        } else {
            addMsg("System: Interview complete.", "system");
            setDisabled(recordBtn, true);
        }
    } catch (e) {
        addMsg("System: Error uploading answer.", "system");
        setDisabled(recordBtn, false);
    } finally {
        isUploading = false;
    }
}

document.addEventListener("DOMContentLoaded", () => {
    addMsg("System: Connected to interviewer.", "system");
    setDisabled(recordBtn, true);
    setDisabled(stopBtn, true);
    
    // Add user interaction listeners to handle autoplay policies
    document.addEventListener('click', handleUserInteraction);
    document.addEventListener('touchstart', handleUserInteraction);
    document.addEventListener('keydown', handleUserInteraction);
    
    // Check if session ID is in URL (from registration)
    const urlSessionId = getSessionIdFromURL();
    if (urlSessionId) {
        sessionId = urlSessionId;
        window.sessionId = sessionId; // Update global reference
        addMsg("System: Registration successful. Starting interview...", "system");
        // Auto-start interview
        setTimeout(() => {
            if (startBtn) {
                startBtn.click();
            } else {
                // Fallback: directly call the start function
                startInterview();
            }
        }, 500);
    }
    
    initCamera();
    
    // Setup tab switching detection
    setupTabSwitchDetection();
});
// Function to start the interview (used both by button click and direct call)
async function startInterview() {
    setDisabled(startBtn, true);
    setDisabled(recordBtn, true);

    // For registered users coming from registration, we already have a session ID
    // and the track is stored in the database, so we don't need to send track info
    try {
        const requestBody = sessionId ? { session_id: sessionId } : {};
        const res = await fetch("/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody)
        });
        const data = await res.json();
        sessionId = data.session_id || null;
        window.sessionId = sessionId; // Update global reference

        if (!sessionId) {
            addMsg("System: Failed to start session.", "system");
            setDisabled(startBtn, false);
            return;
        }

        // Camera and interview started

        // Bot assets playback removed as bot view was simplified

        const q = data.question || "";
        if (q) {
            addMsg("Interviewer: " + q, "bot");
            // Play TTS audio if available
            if (data.tts_url && botVoice) {
                botVoice.src = data.tts_url;
                // Handle autoplay policies by attempting to play after user interaction
                const playPromise = botVoice.play();
                if (playPromise !== undefined) {
                    playPromise.catch(e => {
                        console.log("Audio play failed:", e);
                        // Try to play after a small delay
                        setTimeout(() => {
                            botVoice.play().catch(e2 => {
                                console.log("Audio play failed on retry:", e2);
                                // Show a message to the user that audio is not available
                                addMsg("System: Audio playback failed. Please check your browser settings or click anywhere to enable audio.", "system");
                            });
                        }, 100);
                    });
                }
            }
            setDisabled(recordBtn, false);
        } else {
            addMsg("System: No question received.", "system");
            setDisabled(recordBtn, false);
        }    } catch (e) {
        addMsg("System: Error starting interview.", "system");
        setDisabled(startBtn, false);
    }
}
startBtn.onclick = async () => {
    startInterview();
};
recordBtn.onclick = () => {
    startRecording();
};

stopBtn.onclick = () => {
    stopRecording();
    setDisabled(recordBtn, true);
};

// Tab switching detection functions
function setupTabSwitchDetection() {
    // Listen for visibility changes (tab switching)
    document.addEventListener('visibilitychange', handleVisibilityChange);
}

function handleVisibilityChange() {
    // Only trigger warning if interview has started
    if (sessionId) {
        if (document.hidden) {
            tabSwitchCount++;
            showTabSwitchWarning();
        }
    }
}

function showTabSwitchWarning() {
    // Create warning overlay
    const warningOverlay = document.createElement('div');
    warningOverlay.id = 'tab-switch-warning';
    warningOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255, 0, 0, 0.9);
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        font-family: Arial, sans-serif;
        text-align: center;
    `;
    
    warningOverlay.innerHTML = `
        <h1 style="font-size: 48px; margin-bottom: 20px;">⚠️ WARNING</h1>
        <h2 style="font-size: 32px; margin-bottom: 20px;">Tab Switching Detected!</h2>
        <p style="font-size: 24px; margin-bottom: 30px;">Please return to the interview tab immediately.</p>
        <p style="font-size: 18px;">This incident will be recorded.</p>
    `;
    
    document.body.appendChild(warningOverlay);
    
    // Play warning sound
    playWarningSound();
    
    // Remove warning after 3 seconds
    setTimeout(() => {
        if (warningOverlay.parentNode) {
            warningOverlay.parentNode.removeChild(warningOverlay);
        }
    }, 3000);
}

function playWarningSound() {
    try {
        // Try Web Audio API first
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        
        oscillator.type = 'sine';
        oscillator.frequency.value = 800;
        gainNode.gain.value = 0.3;
        
        oscillator.start();
        setTimeout(() => {
            oscillator.stop();
        }, 1000);
    } catch (e) {
        // Fallback: try to play a beep sound
        console.warn('Web Audio API not available for warning sound');
        try {
            const audio = new Audio();
            audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFd2xqZ2VjXl1bWVhXVlVUU1JRUFFQUVJTVFVWV1hZWltcXF5fYGFiY2RlZmdoaWprbG1ub3BxcnN0dXZ3eHl6e3x9fn+AgYKDhIWGh4iJiouMjY6PkJGSk5SVlpeYmZqbnJ2en6ChoqOkpaanqKmqq6ytrq+wsbKztLW2t7i5uru8vb6/wMHCw8TFxsfIycrLzM3Oz9DR0tPU1dbX2Nna29zd3t/g4eLj5OXm5+jp6uvs7e7v8PHy8/T19vf4+fr7/P3+/w==';
            audio.play();
        } catch (e2) {
            console.warn('Fallback audio also failed');
        }
    }
}

// Variable to track if user has interacted with the page
let userInteracted = false;

// Function to handle user interaction for audio autoplay
function handleUserInteraction() {
    if (!userInteracted) {
        userInteracted = true;
        // Try to resume audio context if needed
        if (botVoice) {
            botVoice.muted = false;
        }
        // Remove event listeners after first interaction
        document.removeEventListener('click', handleUserInteraction);
        document.removeEventListener('touchstart', handleUserInteraction);
        document.removeEventListener('keydown', handleUserInteraction);
    }
}

// All proctoring functionality has been completely removed to eliminate false positives