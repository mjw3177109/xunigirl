"""Packaging and browser wiring tests without real CUDA, DeepSeek or microphone."""
import re
from pathlib import Path
from tools.configure_upstream import patch_once

ROOT=Path(__file__).resolve().parents[1]


def test_browser_controls_are_present():
    source=(ROOT/'web'/'app.js').read_text(encoding='utf-8')
    page=(ROOT/'web'/'index.html').read_text(encoding='utf-8')
    selectors=set(re.findall(r"\$\('([^']+)'\)", source))
    ids=set(re.findall(r'id="([^"]+)"', page))
    assert selectors <= ids, 'Missing elements: '+repr(sorted(selectors-ids))
    assert 'api/vad' in source and 'voice-worklet' in (ROOT/'web'/'worklet.js').read_text()
    assert 'qq_message' in source and 'api/qq/ws' in source
    assert 'playDhNext()' in source and 'v.muted=false;v.loop=false' in source


def test_voice_config_upstream_patcher_is_idempotent():
    original='VOICES_DIR = Path("D:/speech-to-speech/voices")'
    new='VOICES_DIR = Path(__file__).resolve().parents[2] / "voices"'
    patched,msg=patch_once(original,original,new,'voices')
    assert patched==new and msg.startswith('patched:')
    patched,msg=patch_once(patched,original,new,'voices')
    assert patched==new and msg.startswith('already:')


def test_distribution_files_prepared():
    for name in [
        'START.cmd','STOP.cmd','CHECK.cmd','INSTALL.cmd',
        'INSTALL_TEXT_ONLY.cmd','CONFIGURE_VOICE.cmd','CONFIGURE_QQ.cmd',
        'SMOKE_TTS.cmd','SELF_TEST.cmd','START_DUIX.cmd','STOP_DUIX.cmd',
        'docker/compose-4090.yml','tools/smoke_tts.py','.env.example',
        'backend/main.py','backend/store.py','README.md'
    ]:
        assert (ROOT/name).is_file(), name
