"""Offline structure validation; never claims a GPU was run."""
from pathlib import Path
import json
import ast

ROOT=Path(__file__).resolve().parents[1]

def test_notebook_is_valid_json_and_has_gpu_inference():
    nb=json.loads((ROOT/"kaggle"/"xiaoya_t4_gpu_test.ipynb").read_text(encoding="utf-8"))
    assert nb["nbformat"]==4
    assert len(nb["cells"])>=6
    code="\n".join("".join(c["source"]) if isinstance(c["source"],list) else c["source"] for c in nb["cells"] if c["cell_type"]=="code")
    assert "generate_custom_voice" in code
    assert "generate_voice_clone" in code
    assert "gpu_report.json" in code
    assert "torch.cuda.is_available()" in code
    for cell in nb["cells"]:
        if cell["cell_type"]!="code": continue
        src="".join(cell["source"]) if isinstance(cell["source"],list) else cell["source"]
        if src.lstrip().startswith("%"): continue
        ast.parse(src)

def test_workflow_requires_secret_not_hardcoded():
    wf=(ROOT/".github"/"workflows"/"kaggle-xiaoya.yml").read_text(encoding="utf-8")
    assert "KAGGLE_API_TOKEN" in wf and "workflow_dispatch" in wf
    assert "NvidiaTeslaT4" in wf
    assert "secrets.KAGGLE_API_TOKEN" in wf
