from pathlib import Path
import json
import soundfile as sf
from fastapi.testclient import TestClient
from backend import main
from tools.generate_xiaoya_voice import needs_generation

ROOT = Path(__file__).resolve().parents[1]


def test_bundled_voice_is_valid_and_transcribed():
    d=ROOT/'voices'/'xiaoya'
    wav=d/'ref_audio.wav'
    sig, sr=sf.read(wav)
    assert sr==16000
    assert sig.ndim==1
    assert 5<=len(sig)/sr<=25
    assert float(abs(sig).max())>.05
    text=(d/'ref_text.txt').read_text(encoding='utf-8').strip()
    assert text.startswith('你好呀，我是小雅')
    assert json.loads((d/'ref_source.json').read_text(encoding='utf-8'))['quality']=='preview_replace_with_qwen_generated_voice'
    assert needs_generation(False)


def test_character_image_served_by_standalone_api():
    with TestClient(main.app) as client:
        r=client.get('/portraits/xiaoya.png')
        assert r.status_code==200
        assert r.headers['content-type']=='image/png'
        assert r.content[:8]==b'\x89PNG\r\n\x1a\n'
        page=client.get('/').text
        assert '/portraits/xiaoya.png' in page
