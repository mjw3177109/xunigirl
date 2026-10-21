"""Offline regression tests for the RTX 4090 video-profile patch."""
from pathlib import Path
from tools.apply_digital_profile import PRESETS, apply_profile

ROOT = Path(__file__).resolve().parents[1]


def test_min_profile_preserves_key():
    env = 'DEEPSEEK_API_KEY=sk-test-secret\nTTS_SIZE=1.7\nSTT_DEVICE=cuda\nEXTRA=yes\n'
    patched = apply_profile(env, 'min')
    assert 'DEEPSEEK_API_KEY=sk-test-secret' in patched
    assert 'EXTRA=yes' in patched
    for key, value in PRESETS['min'].items():
        assert patched.count(f'{key}={value}') == 1


def test_profile_idempotent():
    once = apply_profile('DIGITAL_HUMAN_ENABLED=1\nTTS_SIZE=1.7\n', 'min')
    assert apply_profile(once, 'min') == once
    assert 'DIGITAL_HUMAN_ENABLED=0' in once


def test_quality_switch():
    value = apply_profile('TTS_SIZE=0.6\nSTT_DEVICE=cuda\n', 'quality')
    assert 'TTS_SIZE=1.7' in value
    assert 'STT_DEVICE=cpu' in value


def test_multi_segment_wait_logic_present():
    src = (ROOT / 'web' / 'app.js').read_text(encoding='utf-8')
    assert 'if(state.dhFinished&&!state.dhPlaying&&!state.videoQueue.length)finishDh()' in src
    assert "$('videoState').textContent='等待下一段数字人视频…'" in src
    assert 'v.muted=false;v.loop=false;' in src


def test_docker_remains_video_only():
    compose = (ROOT / 'docker' / 'compose-4090.yml').read_text(encoding='utf-8')
    assert 'duix-avatar-gen-video' in compose
    assert 'fish-speech' not in compose
    assert 'fun-asr' not in compose
