"""Tests for verified neural voice promotion: no live Kaggle/GPU required."""
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import wave
import zipfile

import pytest
from scripts.promote_xiaoya_voice import promote, validate_wav


def pcm_wav(seconds=4):
    frames=int(16000*seconds)
    stream=io.BytesIO()
    with wave.open(stream, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"".join(
            struct.pack("<h", round(3200*math.sin(2*math.pi*440*i/16000)))
            for i in range(frames)
        ))
    return stream.getvalue()


def make_artifact(path: Path, *, corrupt_hash=False):
    ref=pcm_wav(8)
    clone=pcm_wav(6)
    txt="你好呀，我是小雅。今天终于见到你啦！\n".encode("utf-8")
    sha={n:hashlib.sha256(b).hexdigest() for n,b in [
        ("ref_audio.wav",ref),("ref_text.txt",txt),("clone_test.wav",clone)]}
    if corrupt_hash:sha["ref_audio.wav"]="0"*64
    report={"status":"gpu_inference_completed","gpu":"Tesla T4","sha256":sha,
        "stages":[{"name":"custom_reference","elapsed_sec":44},
                  {"name":"base_voice_clone","elapsed_sec":50}]}
    with zipfile.ZipFile(path,"w") as z:
        for n,b in [("ref_audio.wav",ref),("ref_text.txt",txt),
                    ("clone_test.wav",clone),("gpu_report.json",json.dumps(report).encode())]:
            z.writestr("xiaoya_results/"+n,b)
    return ref,clone


def test_promote_and_preserve_preview_backup(tmp_path):
    root=tmp_path/"checkout"
    voice=root/"voices"/"xiaoya"
    voice.mkdir(parents=True)
    original=pcm_wav(5)
    (voice/"ref_audio.wav").write_bytes(original)
    (voice/"ref_source.json").write_text(json.dumps({
        "quality":"preview_replace_with_qwen_generated_voice"}),encoding="utf-8")
    archive=tmp_path/"artifact.zip"
    reference, clone=make_artifact(archive)
    outcome=promote(archive,root)
    assert (voice/"ref_audio.wav").read_bytes()==reference
    assert (root/"assets"/"voice-samples"/"xiaoya_clone_test.wav").read_bytes()==clone
    assert (root/"assets"/"voice-archive"/"xiaoya_mechanical_preview.wav").read_bytes()==original
    assert outcome["quality"]=="neural_voice_generated_on_kaggle_t4"
    # Promotion can safely rerun without overwriting another custom voice.
    promote(archive,root)
    assert validate_wav((voice/"ref_audio.wav").read_bytes())==8


def test_reject_fake_hash_before_touching_existing_voice(tmp_path):
    root=tmp_path/"checkout"
    voice=root/"voices"/"xiaoya"
    voice.mkdir(parents=True)
    old=pcm_wav(5)
    (voice/"ref_audio.wav").write_bytes(old)
    z=tmp_path/"fake.zip"
    make_artifact(z,corrupt_hash=True)
    with pytest.raises(AssertionError,match="Hash mismatch"):
        promote(z,root)
    assert (voice/"ref_audio.wav").read_bytes()==old
