import os
import numpy as np

class WhisperSTT:
    def __init__(self, model_name=None, hf_token=None, device=None):
        self.model = None
        self.processor = None
        self.forced_decoder_ids = None
        self.device = device or ("cuda" if self._cuda_available() else "cpu")
        self.model_name = model_name or "AventIQ-AI/whisper-audio-to-text"
        self._init_model(hf_token)

    def _cuda_available(self):
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def _init_model(self, hf_token):
        try:
            from transformers import WhisperProcessor, WhisperForConditionalGeneration
            import torch
            auth = hf_token or os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
            self.model = WhisperForConditionalGeneration.from_pretrained(self.model_name, use_auth_token=auth)
            self.model = self.model.to(self.device)
            self.processor = WhisperProcessor.from_pretrained(self.model_name, use_auth_token=auth)
            self.forced_decoder_ids = self.processor.get_decoder_prompt_ids(language="en", task="transcribe")
        except Exception:
            self.model = None
            self.processor = None
            self.forced_decoder_ids = None

    def _load_audio(self, path, target_sr=16000):
        arr = None
        sr = None
        try:
            import torchaudio
            waveform, sample_rate = torchaudio.load(path)
            if waveform.shape[0] > 1:
                waveform = waveform.mean(dim=0, keepdim=True)
            if sample_rate != target_sr:
                resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=target_sr)
                waveform = resampler(waveform)
            arr = waveform.squeeze(0).numpy()
            sr = target_sr
            return arr, sr
        except Exception:
            pass

        try:
            import av, resampy
            container = av.open(path)
            stream = next((s for s in container.streams if s.type == 'audio'), None)
            if stream is None:
                raise RuntimeError('no audio stream')
            frames = []
            for frame in container.decode(stream):
                samples = frame.to_ndarray()
                if samples.ndim == 2:
                    samples = samples.mean(axis=0)
                if samples.dtype.kind in 'iu':
                    samples = samples.astype(np.float32) / np.iinfo(samples.dtype).max
                else:
                    samples = samples.astype(np.float32)
                frames.append(samples)
            container.close()
            if frames:
                data = np.concatenate(frames)
                if stream.rate and stream.rate != target_sr:
                    data = resampy.resample(data, stream.rate, target_sr)
                arr = data
                sr = target_sr
                return arr, sr
        except Exception:
            pass

        try:
            import soundfile as sf, resampy
            data, sample_rate = sf.read(path, always_2d=False)
            if isinstance(data, np.ndarray) and data.ndim == 2:
                data = data.mean(axis=1)
            if sample_rate != target_sr:
                try:
                    data = resampy.resample(data, sample_rate, target_sr)
                except Exception:
                    pass
            arr = np.asarray(data, dtype=np.float32)
            sr = target_sr
            return arr, sr
        except Exception:
            pass

        try:
            from moviepy.editor import AudioFileClip
            import tempfile
            clip = AudioFileClip(path)
            tmpwav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            clip.write_audiofile(tmpwav.name, fps=target_sr, nbytes=2, verbose=False, logger=None)
            clip.close()
            import soundfile as sf
            data, sample_rate = sf.read(tmpwav.name, always_2d=False)
            if isinstance(data, np.ndarray) and data.ndim == 2:
                data = data.mean(axis=1)
            arr = np.asarray(data, dtype=np.float32)
            sr = sample_rate
            try:
                os.remove(tmpwav.name)
            except Exception:
                pass
            return arr, sr
        except Exception:
            pass

        try:
            import subprocess, tempfile
            d = tempfile.mkdtemp()
            tmp = os.path.join(d, "audio.wav")
            subprocess.run(["ffmpeg", "-y", "-i", path, "-ar", str(target_sr), "-ac", "1", tmp],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
            import soundfile as sf
            data, sample_rate = sf.read(tmp, always_2d=False)
            if isinstance(data, np.ndarray) and data.ndim == 2:
                data = data.mean(axis=1)
            arr = np.asarray(data, dtype=np.float32)
            sr = sample_rate
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            return arr, sr
        except Exception:
            pass

        return None, None

    def transcribe_file(self, path):
        if not self.model or not self.processor:
            return None
        audio, sr = self._load_audio(path, target_sr=16000)
        if audio is None:
            return None
        try:
            import torch
            audio = np.asarray(audio, dtype=np.float32)
            audio = audio / (np.max(np.abs(audio)) + 1e-8)
            frame = int(0.02 * sr)
            if frame <= 0:
                frame = 320
            rms = []
            for i in range(0, len(audio), frame):
                seg = audio[i:i+frame]
                if len(seg) == 0:
                    rms.append(0.0)
                else:
                    rms.append(float(np.sqrt(np.mean(seg*seg))))
            thr = float(np.percentile(rms, 20))
            mask = []
            for i in range(len(rms)):
                mask.append(1 if rms[i] >= max(0.01, thr) else 0)
            cleaned = []
            for i in range(len(mask)):
                if mask[i] == 1:
                    s = i*frame
                    e = min((i+1)*frame, len(audio))
                    cleaned.append(audio[s:e])
            if cleaned:
                audio = np.concatenate(cleaned)
            chunk_len = int(30 * sr)
            texts = []
            for j in range(0, len(audio), chunk_len):
                chunk = audio[j:j+chunk_len]
                if len(chunk) == 0:
                    continue
                feats = self.processor(chunk, sampling_rate=16000, return_tensors="pt").input_features
                feats = feats.to(self.device)
                with torch.no_grad():
                    ids = self.model.generate(feats, forced_decoder_ids=self.forced_decoder_ids)
                out = self.processor.batch_decode(ids, skip_special_tokens=True)
                txt = (out[0] or "").strip() if out else ""
                if txt:
                    texts.append(txt)
            res = " ".join(texts).strip()
            return res if res else None
        except Exception:
            return None
