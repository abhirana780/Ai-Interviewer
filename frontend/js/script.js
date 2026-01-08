let sessionId = null;
const chatEl = document.getElementById("chat");
const startBtn = document.getElementById("start");
const userCam = document.getElementById("userCam");
const recordBtn = document.getElementById("record");
const stopBtn = document.getElementById("stop");
const timerEl = document.getElementById("timer");
const botVoice = document.getElementById("botVoice");
const faceCountEl = document.getElementById("face-count-display");

let isRecording = false;
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
        } catch (_) { }
    };
    recognition.onerror = () => { };
    recognition.onend = () => { };
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

    try { recognition && recognition.start(); } catch (_) { }
}
function stopRecognition() {
    try { recognition && recognition.stop(); } catch (_) { }

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

        // Start face detection once camera is running
        userCam.addEventListener('play', () => {
            initFaceDetection();
        });
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

    // Create audio-only stream for recording to save bandwidth/space
    const audioStream = new MediaStream(mediaStream.getAudioTracks());

    const options = { mimeType: "audio/webm;codecs=opus" };
    let rec;
    try {
        rec = new MediaRecorder(audioStream, options);
    } catch (e) {
        try {
            // Fallback options
            rec = new MediaRecorder(audioStream);
        } catch (err) {
            return null;
        }
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
    try { stopRecognition(); } catch (_) { }
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
        // Score is now stored but not displayed during interview
        const score = typeof data.score !== "undefined" ? data.score : null;
        const feedback = data.feedback || "";
        // Scores are stored in the database and will be sent after interview completion
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


function setupModalListeners() {
    const btns = document.querySelectorAll('.tech-btn');
    const customInput = document.getElementById('custom-tech');
    let selectedTech = "Software Engineer";

    btns.forEach(btn => {
        btn.onclick = () => {
            btns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            selectedTech = btn.dataset.value;
            if (customInput) customInput.value = '';
        };
    });

    if (customInput) {
        customInput.addEventListener('input', () => {
            if (customInput.value.trim().length > 0) {
                btns.forEach(b => b.classList.remove('active'));
                selectedTech = customInput.value.trim();
            }
        });
    }

    const startBtn = document.getElementById('start-interview-btn');
    if (startBtn) {
        startBtn.onclick = () => {
            if (customInput && customInput.value.trim()) {
                selectedTech = customInput.value.trim();
            } else {
                const activeBtn = document.querySelector('.tech-btn.active');
                if (activeBtn) selectedTech = activeBtn.dataset.value;
            }

            addMsg(`System: Starting interview for ${selectedTech}...`, "system");
            startInterview(selectedTech);
        };
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
    } else {
        // No session ID in URL, show technology selection modal
        const modal = document.getElementById('tech-modal');
        if (modal) {
            modal.style.display = 'flex';
            setupModalListeners();
        } else {
            addMsg("System: Starting new interview session...", "system");
            setTimeout(() => {
                startInterview();
            }, 500);
        }
    }

    initCamera();

    // Setup tab switching detection
    setupTabSwitchDetection();
});
// Function to start the interview (used both by button click and direct call)
async function startInterview(trackName) {
    setDisabled(startBtn, true);
    setDisabled(recordBtn, true);

    // Hide modal if open
    const modal = document.getElementById('tech-modal');
    if (modal) modal.style.display = 'none';

    // For registered users coming from registration, we already have a session ID
    // and the track is stored in the database, so we don't need to send track info
    try {
        const requestBody = sessionId ? { session_id: sessionId } : { track: trackName || "Software Engineer" };
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
        }
    } catch (e) {
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

            // Cancel test if 3 warnings have been issued
            if (tabSwitchCount >= 3) {
                cancelTestForTabSwitching();
                return;
            }

            showTabSwitchWarning();
        }
    }
}

function showTabSwitchWarning() {
    // Create instruction overlay
    const warningOverlay = document.createElement('div');
    warningOverlay.id = 'tab-switch-warning';
    warningOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.6);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        backdrop-filter: blur(5px);
    `;

    warningOverlay.innerHTML = `
        <div style="
            background: white;
            color: #1f2937;
            padding: 30px;
            border-radius: 16px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            max-width: 450px;
            width: 90%;
            border: 1px solid #e5e7eb;
            animation: fadeIn 0.3s ease-out;
        ">
            <div style="
                width: 60px;
                height: 60px;
                background: #eff6ff;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 20px;
            ">
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="16" x2="12" y2="12"></line>
                    <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
            </div>
            <h2 style="font-size: 24px; font-weight: 600; margin-bottom: 12px; color: #111827;">Please Maintain Focus</h2>
            <p style="font-size: 16px; color: #4b5563; margin-bottom: 24px; line-height: 1.5;">
                To ensure a fair interview process, please keep this tab active and visible on your screen.
            </p>
            <div style="
                font-size: 13px;
                color: #9ca3af;
                border-top: 1px solid #f3f4f6;
                padding-top: 15px;
            ">
                Switching tabs is monitored
            </div>
        </div>
        <style>
            @keyframes fadeIn {
                from { opacity: 0; transform: scale(0.95); }
                to { opacity: 1; transform: scale(1); }
            }
        </style>
    `;

    document.body.appendChild(warningOverlay);

    // Play a gentle notification sound instead of warning beep if possible, 
    // but reusing existing sound function for now as it's what we have available.
    // We can modify playWarningSound later if needed.
    playWarningSound();

    // Remove warning after 3.5 seconds
    setTimeout(() => {
        if (warningOverlay.parentNode) {
            warningOverlay.parentNode.removeChild(warningOverlay);
        }
    }, 3500);
}

function cancelTestForTabSwitching() {
    // Create cancellation overlay
    const cancelOverlay = document.createElement('div');
    cancelOverlay.id = 'test-cancelled';
    cancelOverlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.95);
        color: white;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        z-index: 10000;
        font-family: Arial, sans-serif;
        text-align: center;
    `;

    cancelOverlay.innerHTML = `
        <h1 style="font-size: 48px; margin-bottom: 20px; color: #ff4444;">❌ TEST TERMINATED</h1>
        <h2 style="font-size: 32px; margin-bottom: 20px;">Multiple Tab Switching Violations Detected</h2>
        <p style="font-size: 24px; margin-bottom: 30px; max-width: 800px; line-height: 1.5;">Your interview has been automatically cancelled due to repeated tab switching violations. This incident will be recorded and reported to the administration.</p>
        <p style="font-size: 18px; color: #ffaaaa;">Please contact the recruitment team if you believe this was an error.</p>
    `;

    document.body.appendChild(cancelOverlay);

    // Disable all controls
    setDisabled(startBtn, true);
    setDisabled(recordBtn, true);
    setDisabled(stopBtn, true);

    // Add message to chat
    addMsg("System: ⚠️ Interview terminated due to multiple tab switching violations.", "system");

    // Play cancellation sound
    playCancellationSound();

    // Note: We don't remove this overlay as it's a permanent cancellation message
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

function playCancellationSound() {
    try {
        // Try Web Audio API first
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.type = 'sawtooth';
        oscillator.frequency.setValueAtTime(200, audioContext.currentTime);
        oscillator.frequency.setValueAtTime(100, audioContext.currentTime + 0.5);
        gainNode.gain.setValueAtTime(0.5, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 1.0);

        oscillator.start();
        setTimeout(() => {
            oscillator.stop();
        }, 1000);
    } catch (e) {
        console.warn('Web Audio API not available for cancellation sound');
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

// --- Face Detection Logic ---

let isFaceLoopRunning = false;
let isFaceModelLoaded = false;
let faceWarningState = null; // null, 'multiple', 'none', 'away'
let lastWarningSoundTime = 0;

async function initFaceDetection() {
    if (!faceCountEl || isFaceLoopRunning) return;
    isFaceLoopRunning = true; // Prevent double init

    // Load models if not already loaded
    if (!isFaceModelLoaded) {
        try {
            addMsg("System: Loading Proctoring AI...", "system");
            const modelUrl = 'https://justadudewhohacks.github.io/face-api.js/models';
            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri(modelUrl),
                faceapi.nets.faceLandmark68TinyNet.loadFromUri(modelUrl)
            ]);
            isFaceModelLoaded = true;
            addMsg("System: Proctoring active.", "system");
        } catch (e) {
            console.error("Failed to load face models", e);
            addMsg("System: AI Load Failed.", "system");
            isFaceLoopRunning = false;
            return;
        }
    }

    // Start the detection loop
    detectFaceLoop();
}

async function detectFaceLoop() {
    if (userCam.paused || userCam.ended) {
        // If camera stops, wait a bit and retry
        setTimeout(detectFaceLoop, 1000);
        return;
    }

    try {
        // Use Tiny options BUT with higher input size for better accuracy
        // Input size 320 or 416 is better than 224 for distance/accuracy
        const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.4 });

        // Detect faces with landmarks
        const detections = await faceapi.detectAllFaces(userCam, options).withFaceLandmarks(true);
        const count = detections.length;

        // Update UI Count
        if (faceCountEl) {
            faceCountEl.textContent = `Faces: ${count}`;
            if (count === 0) {
                faceCountEl.style.backgroundColor = "rgba(255, 165, 0, 0.7)"; // Orange for no face
            } else if (count === 1) {
                faceCountEl.style.backgroundColor = "rgba(40, 167, 69, 0.7)"; // Green for good
            } else {
                faceCountEl.style.backgroundColor = "rgba(220, 53, 69, 0.7)"; // Red for multiple
            }
        }

        // --- Logic Checks ---
        let currentViolation = null; // null means OK

        if (count === 0) {
            currentViolation = 'no_face'; // Face not visible
        } else if (count > 1) {
            currentViolation = 'multiple_faces'; // Multiple people
        } else {
            // Count is 1, check gaze/pose
            const face = detections[0];
            const landmarks = face.landmarks;
            const jaw = landmarks.getJawOutline();
            const nose = landmarks.getNose();

            // Simple Yaw Check: Nose normalized horizontal position
            // Jaw 0 is left ear, Jaw 16 is right ear
            const leftJawX = jaw[0].x;
            const rightJawX = jaw[16].x;
            const noseX = nose[3].x; // Tip of nose

            const faceWidth = rightJawX - leftJawX;
            if (faceWidth > 0) {
                const distToLeft = noseX - leftJawX;
                const ratio = distToLeft / faceWidth;

                // Ratio ~0.5 is center. Relaxed bounds: 0.3 to 0.7
                if (ratio < 0.3 || ratio > 0.7) {
                    currentViolation = 'looking_away';
                }
            }
        }

        handleViolation(currentViolation);

    } catch (e) {
        console.warn("Face detection error:", e);
    }

    // Loop ASAP using requestAnimationFrame for smooth UI, but throttle slightly if needed
    // standard loop
    window.requestAnimationFrame(detectFaceLoop);
}

function handleViolation(violation) {
    if (!violation) {
        // All good
        if (faceWarningState !== null) {
            removeWarningOverlay();
            faceWarningState = null;
        }
        return;
    }

    const now = Date.now();

    // Play sound if new violation or persistent every 4 seconds
    const isNewState = (faceWarningState !== violation);
    if (isNewState || (now - lastWarningSoundTime > 4000)) {
        playWarningSound();
        lastWarningSoundTime = now;
    }

    faceWarningState = violation;

    let message = "";
    if (violation === 'no_face') message = "Face not detected!<br><span style='font-size:16px'>Please look at the screen</span>";
    if (violation === 'multiple_faces') message = "Multiple people detected!";
    if (violation === 'looking_away') message = "Focus on the screen!";

    showPersistentWarning(message);
}

function showPersistentWarning(htmlContent) {
    let overlay = document.getElementById('proctor-warning-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'proctor-warning-overlay';
        overlay.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(220, 0, 0, 0.9);
            color: white;
            padding: 20px 30px;
            border-radius: 12px;
            z-index: 2000;
            text-align: center;
            width: 85%;
            max-width: 450px;
            box-shadow: 0 0 25px rgba(255,0,0,0.6);
            border: 2px solid rgba(255,255,255,0.8);
            backdrop-filter: blur(4px);
            font-family: sans-serif;
            pointer-events: none;
            transition: all 0.2s ease;
        `;

        const videoParent = userCam.parentElement;
        if (videoParent) {
            videoParent.appendChild(overlay);
        } else {
            document.body.appendChild(overlay);
        }
    }

    overlay.innerHTML = `
        <h2 style="margin:0 0 10px; font-size:26px; text-transform:uppercase; letter-spacing:1px;">⚠️ Warning</h2>
        <p style="margin:0; font-size:22px; font-weight:600;">${htmlContent}</p>
    `;
}

function removeWarningOverlay() {
    const overlay = document.getElementById('proctor-warning-overlay');
    if (overlay) overlay.remove();
}
