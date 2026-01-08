# API Reference

Base URL: http://<host>:7860/

## Endpoints

### GET /
- Serves the frontend `interviewer.html`.

### GET /health
- Returns JSON health info: `{ "status": "healthy", "time": <unix> }`

### POST /start
- Description: Start a new interview session or resume an existing one.
- JSON body options:
  - `session_id` (optional): existing session id
  - `track` or `role` (optional): interview role or track
  - `candidate_name` / `name` (optional)
- Response: `{ "session_id": "...", "question": "...", "bot_video_url": null, "bot_image_url": "/media/bot.svg", "tts_url": "/media/tts/..." }

### POST /answer
- Description: Submit an answer. Accepts form-data with `session_id`, `answer` text, and optional `media` file (webm). Also accepts JSON bodies (`session_id` and `answer`).
- Behavior:
  - If a `media` file is provided and `answer` is empty or `[video_answer]`, server attempts STT transcription.
  - Saves uploaded media under `frontend/media/answers/<session_id>/` and returns `media_path`.
- Sample response fields: `{ "next_question": "...", "score": <float>, "feedback": "...", "media_path": "/media/answers/<session_id>/file.webm", "bot_image_url": "/media/bot.svg", "tts_url": "/media/tts/..." }

### POST /tts
- Description: Synthesize provided text to TTS audio saved under `/media/tts/<session_id>/`.
- Body: `{ "text": "Hello", "session_id": "..." }`
- Response: `{ "tts_url": "/media/tts/<session_id>/tts_<timestamp>.wav" }

### GET /transcript/<session_id>
- Description: Retrieve persisted transcript for a session.
- Response: `{ "transcript": "..." }

## Errors
- 400 on missing required fields (e.g., missing `session_id` where required for `/answer`).
- 5xx on unexpected server errors (check container logs).

## Notes
- The server uses `WhisperSTT` for file transcription when media is uploaded; ensure the STT engine and model files are available if you plan to transcribe large workloads.
- Responses may include `tts_url` and `bot_video_url` depending on available assets.
