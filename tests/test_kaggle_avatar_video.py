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
    assert "np.exceptions.VisibleDeprecationWarning" in source
    assert "Image.Resampling.LANCZOS" in source
    assert "patch_counts" in source
    assert "facexlib==0.3.0" in source
    assert "Dependency install failed" in source
    assert "GFPGAN" in source

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


def test_avatar_face_crop_bounds_and_sadtalker_bbox_fix():
    notebook=json.loads((ROOT/"kaggle/xiaoya_t4_avatar_video_pilot.ipynb").read_text(encoding="utf-8"))
    src="\n".join("".join(c.get("source",[])) for c in notebook["cells"])
    assert "side=max(256,int(min(w,h)*0.40))" in src
    assert "input_preflight.json" in src
    assert "x1 = max(0, min(width, int(np.floor(det[0]))))" in src
    assert "y1 = max(0, min(height, int(np.floor(det[1]))))" in src
    assert "img = img_np[y1:y2, x1:x2, :]" in src
    assert "lm[:,0] += x1" in src and "lm[:,1] += y1" in src
    assert "if x2 <= x1 or y2 <= y1" in src
    assert "detect_faces(img_np, 0.85)" in src
    assert "video_report.json" in src
