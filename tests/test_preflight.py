"""No DeepSeek requests, no CUDA inference, no Docker required."""
from pathlib import Path
import json
import sys
import wave

from tools.preflight_4090 import collect, env_flags, check_wav


def test_only_key_presence_is_recorded(tmp_path):
    key = "sk-VERY_PRIVATE_TEST_KEY_123"
    env = tmp_path / ".env"
    env.write_text(f"DEEPSEEK_API_KEY={key}\nTTS_SIZE=0.6\nSTT_DEVICE=cpu\n", encoding="utf-8")
    flags = env_flags(env)
    assert flags["has_api_key"] == "yes"
    assert key not in str(flags)
    assert flags["tts_size"] == "0.6"


def test_wav_structure(tmp_path):
    p = tmp_path / "test.wav"
    with wave.open(str(p), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x00\x00" * (16000 * 4))
    ok, detail = check_wav(p)
    assert ok and "4.0s" in detail
    with wave.open(str(tmp_path / "bad.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(44100)
        w.writeframes(b"\x00\x00" * 100)
    assert check_wav(tmp_path / "bad.wav")[0] is False


def test_collect_text_mode_no_secret(tmp_path):
    (tmp_path / "backend").mkdir()
    (tmp_path / "web").mkdir()
    (tmp_path / "backend" / "main.py").write_text("# stub", encoding="utf-8")
    (tmp_path / "web" / "app.js").write_text("// stub", encoding="utf-8")
    key="sk-private-for-test-123"
    (tmp_path / ".env").write_text(f"DEEPSEEK_API_KEY={key}", encoding="utf-8")
    report = collect(root=tmp_path, mode="text")
    assert report["ready_for_next_stage"] == (sys.version_info[:2] == (3, 11))
    assert key not in json.dumps(report)
    assert all(c["id"] not in ("docker", "gpu") for c in report["checks"])


def test_existing_dh_state_not_reset_on_reconfiguration():
    source = (Path(__file__).resolve().parents[1] / "tools" / "configure_upstream.py").read_text(encoding="utf-8")
    assert "elif os.getenv('VC_RESET_DH_ON_CONFIG', '').strip() == '1':" in source
    assert "# Otherwise preserve existing cfg['digital_human']['enabled']" in source
