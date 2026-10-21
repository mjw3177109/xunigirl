"""Offline notebook safety/structure tests; no claim of video inference."""
import json
from pathlib import Path
import ast

ROOT=Path(__file__).resolve().parents[1]


def test_avatar_video_notebook_has_real_model_and_audio_video_validation():
    nb=json.loads((ROOT/"kaggle/xiaoya_t4_avatar_video_pilot.ipynb").read_text(encoding="utf-8"))
    assert nb["nbformat"]==4
    cells=[c for c in nb["cells"] if c["cell_type"]=="code"]
    source="\n".join("".join(c["source"]) for c in cells)
    assert "OpenTalker/SadTalker" in source
    assert "xiaoya_talking_pilot.mp4" in source
    assert "ffprobe" in source and "audio" in source and "video" in source
    assert "5017add8a805d69b97a60d4a7caf16d0f087c8dbec0cf62e636154b1ee289feb" in source
    for c in cells:
        s="".join(c["source"])
        if s.lstrip().startswith("%"):continue
        ast.parse(s)


def test_gpu_submit_and_collector_require_real_results():
    submit=(ROOT/".github/workflows/kaggle-xiaoya-avatar.yml").read_text(encoding="utf-8")
    collect=(ROOT/".github/workflows/kaggle-xiaoya-avatar-collect.yml").read_text(encoding="utf-8")
    assert "secrets.KAGGLE_API_TOKEN" in submit and "NvidiaTeslaT4" in submit
    assert "workflow_dispatch" in submit
    assert "xiaoya_talking_pilot.mp4" in collect
    assert "ffprobe" in collect
    assert "actual_mp4_generated" in collect
