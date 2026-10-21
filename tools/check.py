"""Fast health check, does NOT load giant GPU models or make billed API calls."""
import json
import os
from dotenv import load_dotenv
import sys
from pathlib import Path
from urllib.request import urlopen
ROOT=Path(__file__).resolve().parents[1]

def check(label,yes,details=''):
    print(f"[{'OK' if yes else 'WARN'}] {label}: {details}")

def main():
    env=ROOT/'.env'
    load_dotenv(env)
    tts_size=os.getenv('TTS_SIZE','1.7')
    check('DeepSeek 环境配置',env.exists(),'配置文件存在' if env.exists() else '需复制 .env.example -> .env')
    if env.exists():
        data=env.read_text(encoding='utf-8')
        check('API Key 已填写','DEEPSEEK_API_KEY=sk-' in data and '请替换' not in data, '绝不输出密钥内容')
    up=ROOT/'upstream'
    check('原语音项目', (up/'bridge'/'voice_bridge.py').exists(),str(up/'bridge'))
    check('FunASR 模型',(up/'models'/'funasr'/'speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch'/'configuration.json').exists(), '缺少时重新运行 INSTALL.cmd')
    check(f'Qwen3-TTS {tts_size}B 模型',(ROOT/'models'/f'Qwen3-TTS-12Hz-{tts_size}B-Base'/'config.json').exists(),'缺少时重新下载模型')
    check('VAD 模型',(up/'models'/'silero-vad'/'silero_vad_v4.jit').exists(),'可选：用来检测真人插话')
    has_voice=any((p/'ref_audio.wav').exists() and (p/'ref_text.txt').exists() for p in (ROOT/'voices').iterdir() if p.is_dir())
    check('克隆音色',has_voice,'需要 wav + 对应文稿 txt')
    check('DUIX 形象视频',(ROOT/'data'/'duix'/'temp'/'my_avatar.mp4').exists(),'数字人模式需要合法授权的视频素材')
    for name,url in [('独立网页','http://127.0.0.1:8765/api/app/status'),('DUIX','http://127.0.0.1:9000/easy/query?code=probe')]:
        try:
            with urlopen(url,timeout=2) as r:
                check(name,200<=r.status<500,'服务响应：'+str(r.status))
        except Exception as e:check(name,False,'未启动或不可达')

if __name__=='__main__':main()
