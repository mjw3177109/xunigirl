"""Regenerate the placeholder Xiaoya reference WAV on GitHub Actions.
Uses open-source espeak-ng with a Chinese voice, not high-quality neural TTS.
The local INSTALL / GENERATE_XIAOYA_VOICE upgrades the preview on the RTX 4090.
"""
from pathlib import Path
import os, subprocess, tempfile, wave
ROOT=Path(__file__).resolve().parents[1]
text=(ROOT/"voices/xiaoya/ref_text.txt").read_text(encoding="utf-8").strip()
out=ROOT/"voices/xiaoya/ref_audio.wav"
out.parent.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory() as temp:
    raw=Path(temp)/"voice.wav"
    subprocess.run(["espeak-ng","-v","zh+f3","-p","72","-s","150","-w",str(raw),text],check=True)
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-i",str(raw),"-ac","1","-ar","16000","-c:a","pcm_s16le",str(out)],check=True)
with wave.open(str(out),"rb") as w:
    assert w.getnchannels()==1 and w.getsampwidth()==2 and w.getframerate()==16000 and w.getnframes()>16000
print(f"ready: {out} ({out.stat().st_size} bytes)")
