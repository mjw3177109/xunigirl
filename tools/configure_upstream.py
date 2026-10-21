"""Idempotent portability patch for pinned upstream code (not a DSH fork).
Uses the original upstream voice pipeline and only fixes machine-specific paths.
"""
from __future__ import annotations
import json
import os
from dotenv import load_dotenv
import sys
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UP=ROOT/'upstream'
FILE=UP/'bridge'/'voice_bridge.py'

def patch_once(source,old,new, label):
    if old in source: return source.replace(old,new), 'patched: '+label
    if new in source: return source,'already: '+label
    raise RuntimeError('Upstream compatibility check failed for '+label+'; source may have changed')

def main():
    load_dotenv(ROOT / '.env')
    size=os.getenv('TTS_SIZE','1.7').strip()
    if size not in ('0.6','1.7'):
        raise SystemExit('TTS_SIZE must be 0.6 or 1.7')
    stt_device = os.getenv('STT_DEVICE', 'cuda').strip().lower()
    tts_device = os.getenv('TTS_DEVICE', 'cuda').strip().lower()
    digital_human = os.getenv('DIGITAL_HUMAN_ENABLED', '').strip()
    if stt_device not in ('cpu', 'cuda'):
        raise SystemExit('STT_DEVICE must be cpu or cuda')
    if tts_device not in ('cpu', 'cuda'):
        raise SystemExit('TTS_DEVICE must be cpu or cuda')
    if digital_human not in ('', '0', '1'):
        raise SystemExit('DIGITAL_HUMAN_ENABLED must be 0, 1, or blank')
    if not FILE.exists():
        raise SystemExit('upstream/bridge/voice_bridge.py 不存在。先运行 INSTALL.cmd 下载原项目源码。')
    src=FILE.read_text(encoding='utf-8')
    patches=[
        ('if user_id and text:',
         'if user_id and text and CONFIG.get("qq", {}).get("enabled") and str(user_id) == str(CONFIG.get("qq", {}).get("target_qq", "")):', 'QQ allowlist'),
        ('VOICES_DIR = Path("D:/speech-to-speech/voices")',
         'VOICES_DIR = Path(__file__).resolve().parents[2] / "voices"', 'voices'),
        ('models_dir = HERE / "models" / "silero-vad"',
         'models_dir = HERE.parent / "models" / "silero-vad"','silero VAD'),
        ('BG_IMAGES_DIR = Path(CONFIG["media"]["bg_images_dir"])',
         'BG_IMAGES_DIR = (HERE.parent / CONFIG["media"]["bg_images_dir"]).resolve()', 'media bg'),
        ('TASK_VIDEOS_DIR = Path(CONFIG["media"]["task_videos_dir"])',
         'TASK_VIDEOS_DIR = (HERE.parent / CONFIG["media"]["task_videos_dir"]).resolve()', 'task videos'),
    ]
    messages=[]
    for old,new,name in patches:
        src,message=patch_once(src,old,new,name)
        messages.append(message)
    if FILE.read_text(encoding='utf-8')!=src:
        bak=FILE.with_suffix('.py.original')
        if not bak.exists(): shutil.copy2(FILE,bak)
        FILE.write_text(src,encoding='utf-8')
    (UP/'models'/'silero-vad').mkdir(parents=True,exist_ok=True)
    (UP/'models'/'funasr').mkdir(parents=True,exist_ok=True)
    (ROOT/'data'/'duix'/'temp').mkdir(parents=True,exist_ok=True)
    template=json.loads((UP/'bridge'/'bridge-config.example.json').read_text(encoding='utf-8-sig'))
    target=UP/'bridge'/'bridge-config.json'
    if target.exists():
        cfg=json.loads(target.read_text(encoding='utf-8-sig'))
    else: cfg=template
    cfg['cors_origins']=['http://127.0.0.1:8765','http://localhost:8765']
    cfg['stt']['model_name']=str((UP/'models'/'funasr'/'speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch').resolve())
    cfg['stt']['device']=stt_device
    cfg['stt']['torch_dtype']='float32' if stt_device == 'cpu' else 'float16'
    cfg['tts']['model_name']=str((ROOT/'models'/f'Qwen3-TTS-12Hz-{size}B-Base').resolve())
    cfg['tts']['device']=tts_device
    cfg['media']['bg_images_dir']='assets/bg-images'
    cfg['media']['task_videos_dir']='assets/task-videos'
    cfg['digital_human']['data_dir']=str((ROOT/'data'/'duix').resolve())
    cfg['digital_human']['duix_base']='http://127.0.0.1:9000'
    cfg['digital_human']['container_name']='duix-avatar-gen-video'
    if digital_human != '':
        cfg['digital_human']['enabled'] = digital_human == '1'
    elif not target.exists():
        cfg['digital_human']['enabled'] = False  # first install only
    cfg['digital_human']['stop_container_on_disable']=True
    cfg['deepseek']['api_key']='' # DeepSeek key exclusively in root .env
    cfg['omnivoice']['base']='' # no WSL / OmniVoice required in this deployment
    voices=[p for p in (ROOT/'voices').iterdir() if p.is_dir() and (p/'ref_audio.wav').exists() and (p/'ref_text.txt').exists()]
    if voices:
        selected=sorted(voices)[0]
        cfg['persona']['default_voice']=selected.name
        cfg['tts']['ref_audio']=str((selected/'ref_audio.wav').resolve())
        cfg['tts']['ref_text']=(selected/'ref_text.txt').read_text(encoding='utf-8').strip()
        print('[OK] 找到音色',selected.name)
    else:
        cfg['persona']['default_voice']=''
        cfg['tts']['ref_audio']=str((ROOT/'voices'/'请添加音色'/'ref_audio.wav').resolve())
        cfg['tts']['ref_text']=''
        print('[WARN] 尚未发现声音参考音频。请按照 voices/README.md 放入文件后再运行 CONFIGURE_VOICE.cmd')
    # do not overwrite user's bespoke settings after first install except portability paths
    target.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('\n'.join('[OK] '+x for x in messages))
    print('[OK] Upstream path portability configured:',target)

if __name__=='__main__': main()
