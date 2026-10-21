"""Use Qwen3-TTS 0.6B CustomVoice on the user's NVIDIA GPU to render a cute,
bright *adult* Chinese female character voice. Once generated, the normal
Qwen3-TTS 0.6B Base model clones this local WAV. Independent of DSH.

This is intentionally an offline-at-inference script: model download is the
only network step, and no voice impersonation sample is used.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
VOICE_DIR=ROOT/'voices'/'xiaoya'
MODEL_ID='Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice'
REF_TEXT='你好呀，我是小雅。今天终于见到你啦！想聊什么都可以告诉我，我会认真听着呢。'
INSTRUCTION='一位二十多岁的成年女性，嗓音明亮清甜、轻盈偏高，俏皮可爱，略带撒娇感，普通话清楚自然。轻快温柔，像年轻女生开心地和熟悉的朋友聊天，不要刻意尖叫、哭腔或气声，情绪真实。'

def needs_generation(force: bool) -> bool:
    if force:return True
    ref=VOICE_DIR/'ref_audio.wav'
    if not ref.exists():return True
    meta=VOICE_DIR/'ref_source.json'
    if not meta.exists():return False  # never overwrite user-supplied voices
    try:
        data=json.loads(meta.read_text(encoding='utf-8'))
        return data.get('quality') == 'preview_replace_with_qwen_generated_voice'
    except (OSError,ValueError):return False

def main() -> int:
    p=argparse.ArgumentParser(description='生成并安装小雅甜美成年女性中文音色')
    p.add_argument('--auto',action='store_true',help='仅将内置机械合成试听样音升级为神经 TTS')
    p.add_argument('--force',action='store_true',help='明确覆盖现有小雅音色文件')
    args=p.parse_args()
    if args.auto and not needs_generation(False):
        print('[SKIP] 已有非试听版音色，不覆盖。');return 0
    if not args.auto and not args.force and not needs_generation(False):
        print('[SKIP] 已有非试听版音色；要覆盖请加 --force。');return 0
    try:
        import numpy as np
        import torch
        import soundfile as sf
        from scipy.signal import resample_poly
        from modelscope import snapshot_download
        from qwen_tts import Qwen3TTSModel
    except ImportError as e:
        print('[ERROR] 语音合成依赖尚未安装：',e,file=sys.stderr)
        print('请先执行 INSTALL.cmd，或 pip install qwen-tts modelscope soundfile scipy',file=sys.stderr)
        return 2
    if not torch.cuda.is_available():
        print('[ERROR] 检测不到 CUDA GPU；请先检查 4090 驱动和 PyTorch。',file=sys.stderr)
        return 3
    VOICE_DIR.mkdir(parents=True,exist_ok=True)
    local=ROOT/'models'/'Qwen3-TTS-12Hz-0.6B-CustomVoice'
    local.mkdir(parents=True,exist_ok=True)
    print('[1/3] 准备 Qwen3-TTS 0.6B CustomVoice 模型（首次需联网下载）。',flush=True)
    snapshot_download(MODEL_ID,local_dir=str(local))
    print('[2/3] 4090 正在合成小雅声线。',flush=True)
    dtype=torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    # Eager avoids the need for a separate compiled flash-attn package.
    model=Qwen3TTSModel.from_pretrained(str(local),device_map='cuda:0',dtype=dtype,attn_implementation='eager')
    wavs,sr=model.generate_custom_voice(text=REF_TEXT,language='Chinese',speaker='Vivian',instruct=INSTRUCTION,max_new_tokens=2048)
    arr=np.asarray(wavs[0],dtype=np.float32).reshape(-1)
    if not len(arr) or not np.isfinite(arr).all() or np.max(np.abs(arr))<0.001:
        raise RuntimeError('模型未生成有效音频')
    if sr!=16000:
        from math import gcd
        d=gcd(int(sr),16000)
        arr=resample_poly(arr,16000//d,int(sr)//d)
    duration=len(arr)/16000
    if not 3<=duration<=35:
        raise RuntimeError(f'参考声音长度不合理: {duration:.2f}s，请检查生成结果')
    arr=np.clip(arr,-.99,.99)
    fade=min(240,len(arr)//4)
    arr[:fade]*=np.linspace(0,1,fade,dtype=np.float32)
    arr[-fade:]*=np.linspace(1,0,fade,dtype=np.float32)
    temp=VOICE_DIR/'ref_audio.new.wav'
    sf.write(temp,arr,16000,subtype='PCM_16')
    try:
        samples,fs=sf.read(temp)
        assert fs==16000 and 3 <= len(samples)/fs <= 35
        # Preserve original WAV until the new output is known-good.
        temp.replace(VOICE_DIR/'ref_audio.wav')
        (VOICE_DIR/'ref_text.txt').write_text(REF_TEXT+'\n',encoding='utf-8')
        (VOICE_DIR/'ref_source.json').write_text(json.dumps({
            'source_type':'qwen3_tts_custom_voice_synthetic',
            'quality':'neural_voice_generated_on_local_gpu',
            'model_id':MODEL_ID,'speaker':'Vivian',
            'instruction':INSTRUCTION,'transcript':REF_TEXT,
            'sample_rate':16000,'channels':1,'duration_sec':round(duration,2)
        },ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    finally:
        if temp.exists():temp.unlink()
    print('[3/3] 已生成：',VOICE_DIR/'ref_audio.wav',f'{duration:.2f}s')
    print('请运行 CONFIGURE_VOICE.cmd，然后 START.cmd / SMOKE_TTS.cmd。')
    return 0

if __name__=='__main__':raise SystemExit(main())
