"""Real local GPU smoke test: synthesizes one short wav (NO DeepSeek API usage)."""
from __future__ import annotations
from pathlib import Path
import sys

import httpx

ROOT = Path(__file__).resolve().parents[1]
URL = "http://127.0.0.1:8765/voice/api/tts"
OUTPUT = ROOT / "data" / "smoke_tts.wav"


def main():
    print("[SMOKE] TTS test on local GPU; the first run may need to load large models")
    try:
        with httpx.Client(timeout=180) as c:
            h = c.get("http://127.0.0.1:8765/voice/api/health")
            h.raise_for_status()
            print("[HEALTH]", h.json())
            response = c.post(URL, json={"text": "你好，我是小雅。这是四零九零本地语音测试。"})
            if response.status_code != 200:
                print("[FAIL]", response.status_code, response.text[:900])
                return 1
            if not response.content.startswith(b"RIFF"):
                print("[FAIL] Expected WAV header, got", response.content[:50])
                return 1
            OUTPUT.parent.mkdir(exist_ok=True)
            OUTPUT.write_bytes(response.content)
            print("[OK] Saved audio:", OUTPUT)
            return 0
    except httpx.HTTPError as exc:
        print("[FAIL] TTS HTTP error:", type(exc).__name__, str(exc)[:400])
        return 1


if __name__ == "__main__":
    sys.exit(main())
