"""Download STT, TTS and Silero resources into explicit known local directories."""
from pathlib import Path
from urllib.request import urlretrieve
import sys
import os
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[1]

def main():
    from modelscope import snapshot_download
    load_dotenv(ROOT / '.env')
    size=os.getenv('TTS_SIZE','1.7').strip()
    if size not in ('0.6','1.7'):
        raise SystemExit('TTS_SIZE must be 0.6 or 1.7')
    tts_id=f'Qwen/Qwen3-TTS-12Hz-{size}B-Base'
    targets=[
        ('iic/speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch',
         ROOT/'upstream'/'models'/'funasr'/'speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch'),
        (tts_id,ROOT/'models'/f'Qwen3-TTS-12Hz-{size}B-Base'),
    ]
    for ident,dest in targets:
        dest.mkdir(parents=True,exist_ok=True)
        print('[DOWNLOAD] ',ident,'->',dest,flush=True)
        snapshot_download(ident, local_dir=str(dest))
    target=ROOT/'upstream'/'models'/'silero-vad'/'silero_vad_v4.jit'
    if not target.is_file():
        target.parent.mkdir(parents=True,exist_ok=True)
        print('[DOWNLOAD] Silero VAD v4',flush=True)
        try:
            urlretrieve('https://raw.githubusercontent.com/snakers4/silero-vad/v4.0/files/silero_vad.jit',str(target))
        except Exception:
            if target.exists():target.unlink()
            print('[WARN] Silero 自动下载失败。可从 https://github.com/snakers4/silero-vad/tree/v4.0/files 手动取 silero_vad.jit 保存到',target)
    print('[DONE] 模型准备结束。请用 CONFIGURE_VOICE.cmd 重新写入最新模型和音色路径。')

if __name__=='__main__':main()
