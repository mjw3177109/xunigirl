"""Promote a verified Kaggle GPU voice result to the repository.

Reads exact paths from the GitHub Actions result artifact ZIP. Does not trust
filenames in the ZIP and never executes files from it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import wave
import zipfile

EXPECTED_NAMES = (
    "xiaoya_results/ref_audio.wav",
    "xiaoya_results/ref_text.txt",
    "xiaoya_results/clone_test.wav",
    "xiaoya_results/gpu_report.json",
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_wav(data: bytes, *, min_duration: float = 2.0, max_duration: float = 40.0) -> float:
    import io
    with wave.open(io.BytesIO(data), "rb") as wf:
        assert wf.getnchannels() == 1, "Expected mono"
        assert wf.getsampwidth() == 2, "Expected PCM16"
        assert wf.getframerate() == 16000, "Expected 16 kHz"
        duration = wf.getnframes() / wf.getframerate()
    assert min_duration <= duration <= max_duration, f"Unexpected WAV duration: {duration}"
    return round(duration, 3)


def promote(archive: Path, root: Path) -> dict:
    with zipfile.ZipFile(archive) as zipped:
        assert zipped.testzip() is None, "Artifact zip CRC failed"
        assert all(p in zipped.namelist() for p in EXPECTED_NAMES), "Missing generated files"
        ref = zipped.read("xiaoya_results/ref_audio.wav")
        txt = zipped.read("xiaoya_results/ref_text.txt")
        clone = zipped.read("xiaoya_results/clone_test.wav")
        report = json.loads(zipped.read("xiaoya_results/gpu_report.json"))

    assert report.get("status") == "gpu_inference_completed"
    assert report.get("gpu") == "Tesla T4"
    assert [x.get("name") for x in report.get("stages", [])] == [
        "custom_reference", "base_voice_clone"
    ]
    assert report.get("sha256") == {
        "ref_audio.wav": digest(ref),
        "ref_text.txt": digest(txt),
        "clone_test.wav": digest(clone),
    }, "Hash mismatch in GPU-generated outputs"
    d1 = validate_wav(ref)
    d2 = validate_wav(clone)
    transcript = txt.decode("utf-8").strip()
    assert transcript.startswith("你好呀，我是小雅"), "Unexpected character reference text"

    voice = root / "voices" / "xiaoya"
    voice.mkdir(parents=True, exist_ok=True)
    archive_dir = root / "assets" / "voice-archive"
    sample_dir = root / "assets" / "voice-samples"
    archive_dir.mkdir(parents=True, exist_ok=True)
    sample_dir.mkdir(parents=True, exist_ok=True)

    old_meta = voice / "ref_source.json"
    meta = json.loads(old_meta.read_text(encoding="utf-8")) if old_meta.exists() else {}
    old_audio = voice / "ref_audio.wav"
    if old_audio.exists() and meta.get("quality") == "preview_replace_with_qwen_generated_voice":
        backup = archive_dir / "xiaoya_mechanical_preview.wav"
        if not backup.exists():
            shutil.copyfile(old_audio, backup)
    elif old_audio.exists() and digest(old_audio.read_bytes()) != digest(ref):
        raise RuntimeError("Refusing to replace an unrecognized/custom reference voice")

    old_audio.write_bytes(ref)
    (voice / "ref_text.txt").write_bytes(txt)
    (sample_dir / "xiaoya_clone_test.wav").write_bytes(clone)
    result = {
        "source_type": "qwen3_tts_custom_voice_synthetic",
        "quality": "neural_voice_generated_on_kaggle_t4",
        "status": "actual_gpu_inference_verified",
        "model_reference": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
        "model_clone": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        "speaker": "Vivian",
        "gpu": report["gpu"],
        "sample_rate": 16000,
        "channels": 1,
        "duration_sec": d1,
        "clone_duration_sec": d2,
        "transcript": transcript,
        "source_kaggle": "https://www.kaggle.com/code/mjw3177109/xunigirl-xiaoya-gpu-voice-benchmark",
        "source_github_artifact_run": 39545400976,
        "sha256": report["sha256"],
        "stages": report["stages"],
        "notes": "AI-generated voice, not a recording of any real person. Auditory quality is subjective; listening review is recommended.",
    }
    old_meta.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[OK] Neural reference WAV {d1}s; cloned sample {d2}s")
    print(f"[OK] SHA256 ref_audio.wav {result['sha256']['ref_audio.wav']}")
    return result


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--artifact", required=True, type=Path)
    p.add_argument("--root", default=Path(__file__).resolve().parents[1], type=Path)
    args = p.parse_args()
    promote(args.artifact, args.root)


if __name__ == "__main__":
    main()
