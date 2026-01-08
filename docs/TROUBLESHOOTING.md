# Troubleshooting

Common issues and how to resolve them.

1) ffmpeg / av errors
- Symptoms: `imageio-ffmpeg` or `av` raises missing executable error.
- Fix: Ensure `ffmpeg` is installed in the system or Docker image. On Debian-based systems: `apt-get install ffmpeg`.

2) pyttsx3 TTS produces no audio
- Symptoms: `pyttsx3` completes but no .wav or no playback in container.
- Fix: Install system speech engine (`espeak` or `espeak-ng`) or use external cloud TTS; ensure `pyttsx3` dependencies are available in your image.

3) Torch installation problems
- Symptoms: long pip installs or binary incompatibility errors.
- Fix: Pin a compatible `torch` wheel in `backend/requirements.txt`, or use official PyTorch instructions for your Python version and platform. Consider using a base image that matches wheel platform for reproducibility.

4) Windows Docker volume mount path issues
- Use `-v ${PWD}\backend\database:/app/backend/database` in PowerShell and ensure Docker Desktop has shared drives enabled.

5) Missing `session_id` errors when submitting answers
- Ensure you pass `session_id` either in form data, headers, or JSON body. If you uploaded a media file, confirm the server returned a `session_id` when you started the session or from a previous response.

6) Database file not persisted
- Persist `backend/database` as a Docker volume or bind mount to ensure `interviews.db` remains across container restarts.

If an issue is unclear, capture logs (`docker logs` or server output) and open an issue with reproduction steps.
