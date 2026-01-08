# Usage & Examples

This doc provides common workflows and curl examples to interact with the backend endpoints.

## Start a session

```bash
curl -X POST "http://localhost:7860/start" -H "Content-Type: application/json" -d '{"track":"Python"}'
```
Response includes `session_id` and the first question.

## Submit a text answer

```bash
curl -X POST "http://localhost:7860/answer" -H "Content-Type: application/json" -d '{"session_id":"<session_id>", "answer":"My answer here"}'
```

## Submit a media answer (WebM)

```bash
curl -X POST "http://localhost:7860/answer" -F "session_id=<session_id>" -F "media=@/path/to/answer.webm"
```

If the server transcribes the file successfully, the `answer` text will be populated using STT and the response will include `media_path` and scoring/feedback fields.

## Get transcript

```bash
curl "http://localhost:7860/transcript/<session_id>"
```

## TTS

```bash
curl -X POST "http://localhost:7860/tts" -H "Content-Type: application/json" -d '{"text":"Next question...", "session_id":"<session_id>"}'
```

## Frontend
Open http://localhost:7860/ in a browser. The UI supports recording and uploading WebM answers. If you encounter mic/camera permission issues, use the text input option.
