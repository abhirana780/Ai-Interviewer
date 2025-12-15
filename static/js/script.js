let sessionId = null;
const chatEl = document.getElementById("chat");
const startBtn = document.getElementById("start");
const trackSel = document.getElementById("track");
const botVoice = document.getElementById("botVoice");
const botVideo = document.getElementById("botVideo");
const botAvatar = document.getElementById("botAvatar");
const userCam = document.getElementById("userCam");
const recordBtn = document.getElementById("record");
const stopBtn = document.getElementById("stop");
const timerEl = document.getElementById("timer");
let isRecording = false;
let isUploading = false;

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

async function playBotAssets(ttsUrl, videoUrl, imageUrl) {
    const fallback = "/static/media/bot.svg";
    const imgUrl = imageUrl || fallback;
    if (videoUrl) {
        botVideo.style.display = "block";
        if (botAvatar) botAvatar.style.display = "none";
        botVideo.poster = "";
        botVideo.src = videoUrl;
        try { await botVideo.play(); } catch (_) {}
    } else {
        try { botVideo.pause && botVideo.pause(); } catch (_) {}
        botVideo.src = "";
        try { botVideo.load(); } catch (_) {}
        botVideo.style.display = "none";
        if (botAvatar) {
            botAvatar.src = imgUrl;
            botAvatar.style.display = "block";
        }
    }
    if (ttsUrl) {
        botVoice.src = ttsUrl;
        try { await botVoice.play(); } catch (_) {}
    }
}

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
            playBotAssets(data.tts_url, data.bot_video_url, data.bot_image_url);
            setDisabled(recordBtn, false);
        } else {
            addMsg("System: Interview complete.", "system");
            playBotAssets(null, data.bot_video_url, data.bot_image_url);
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
    botVideo.src = "";
    try { botVideo.load(); } catch (_) {}
    botVideo.style.display = "none";
    if (botAvatar) {
        botAvatar.src = "/static/media/bot.svg";
        botAvatar.style.display = "block";
    }
    
    // Check if session ID is in URL (from registration)
    const urlSessionId = getSessionIdFromURL();
    if (urlSessionId) {
        sessionId = urlSessionId;
        addMsg("System: Registration successful. Starting interview...", "system");
        // Auto-start interview
        setTimeout(() => startBtn.click(), 500);
    }
    
    initCamera();
});

startBtn.onclick = async () => {
    setDisabled(startBtn, true);
    setDisabled(recordBtn, true);

    const track = trackSel ? trackSel.value : "Software Engineer";
    try {
        const requestBody = sessionId ? { session_id: sessionId } : { track };
        const res = await fetch("/start", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody)
        });
        const data = await res.json();
        sessionId = data.session_id || null;

        if (!sessionId) {
            addMsg("System: Failed to start session.", "system");
            setDisabled(startBtn, false);
            return;
        }

        if (data.bot_video_url || data.tts_url || data.bot_image_url) {
            playBotAssets(data.tts_url, data.bot_video_url, data.bot_image_url);
        }

        const q = data.question || "";
        if (q) {
            addMsg("Interviewer: " + q, "bot");
            setDisabled(recordBtn, false);
        } else {
            addMsg("System: No question received.", "system");
            setDisabled(recordBtn, false);
        }
    } catch (e) {
        addMsg("System: Error starting interview.", "system");
        setDisabled(startBtn, false);
    }
};

recordBtn.onclick = () => {
    startRecording();
};

stopBtn.onclick = () => {
    stopRecording();
    setDisabled(recordBtn, true);
};