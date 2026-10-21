"""Non-destructive deployment preflight. Never calls the paid DeepSeek API.

Usage: python tools/preflight_4090.py [--mode text|voice|digital] [--strict]
Creates data/preflight_4090.json. Does not include secrets or user messages.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import wave
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def env_flags(path: Path) -> dict[str, str]:
    """Read only known nonsecret flags, plus presence of API key (never value)."""
    result = {"has_api_key": "no", "tts_size": "0.6", "stt_device": "cpu", "tts_device": "cuda"}
    if not path.is_file():
        return result
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, value = [s.strip() for s in line.split("=", 1)]
        if key == "DEEPSEEK_API_KEY":
            if value and not any(x in value.lower() for x in ("请替换", "your", "replace", "example", "你的")):
                result["has_api_key"] = "yes"
        elif key == "TTS_SIZE" and value in ("0.6", "1.7"):
            result["tts_size"] = value
        elif key == "STT_DEVICE" and value in ("cpu", "cuda"):
            result["stt_device"] = value
        elif key == "TTS_DEVICE" and value in ("cpu", "cuda"):
            result["tts_device"] = value
    return result


def probe_command(cmd: list[str], timeout: float = 5.0) -> tuple[bool, str]:
    if shutil.which(cmd[0]) is None:
        return False, "command unavailable"
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        if p.returncode != 0:
            return False, "command failed"
        return True, (p.stdout or "").strip()[:300]
    except (OSError, subprocess.TimeoutExpired):
        return False, "command timeout or execution error"


def check_wav(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, "参考 WAV 缺失"
    try:
        with wave.open(str(path), "rb") as wav:
            duration = wav.getnframes() / wav.getframerate()
            if wav.getnchannels() != 1 or wav.getsampwidth() != 2 or wav.getframerate() != 16000:
                return False, "需要 16kHz 单声道 16bit PCM WAV"
            if not 3 <= duration <= 35:
                return False, "声音长度需要 3–35 秒"
        return True, f"{duration:.1f}s PCM WAV"
    except (OSError, ValueError, EOFError, wave.Error, ZeroDivisionError):
        return False, "WAV 文件损坏或编码不兼容"


def collect(root: Path = ROOT, mode: str = "digital") -> dict:
    if mode not in ("text", "voice", "digital"):
        raise ValueError("invalid mode")
    checks: list[dict] = []

    def add(code: str, ok: bool, detail: str, fix: str, relevant: bool = True, caution: bool = False):
        checks.append({"id": code, "status": "pass" if ok else ("warning" if caution or not relevant else "fail"),
                       "detail": detail, "next_action": "" if ok else fix})

    flags = env_flags(root / ".env")
    add("python", sys.version_info[:2] == (3, 11),
        f"current Python: {sys.version_info.major}.{sys.version_info.minor}", "安装 Python 3.11 后重新执行 INSTALL.cmd")
    add("core", (root / "backend" / "main.py").is_file() and (root / "web" / "app.js").is_file(),
        "独立前后端文件", "重新获取完整源码")
    add("env", (root / ".env").is_file(), ".env", "复制 .env.example 为 .env")
    add("deepseek", flags["has_api_key"] == "yes", "DeepSeek Key 非空且非示例值（未进行网络或余额检查）",
        "在 .env 配置 DEEPSEEK_API_KEY")
    if mode in ("voice", "digital"):
        up = root / "upstream" / "bridge" / "voice_bridge.py"
        add("speech_source", up.is_file(), "固定上游 Python 语音服务", "运行 INSTALL.cmd")
        model = root / "models" / f"Qwen3-TTS-12Hz-{flags['tts_size']}B-Base" / "config.json"
        add("tts_model", model.is_file(), f"Qwen3-TTS {flags['tts_size']}B Base", "运行 INSTALL.cmd 下载声音模型")
        stt = root / "upstream" / "models" / "funasr" / "speech_paraformer-large_asr_nat-zh-cn-16k-common-vocab8404-pytorch" / "configuration.json"
        add("stt_model", stt.is_file(), "FunASR 模型与配置", "运行 INSTALL.cmd 下载识别模型")
        audio = root / "voices" / "xiaoya" / "ref_audio.wav"
        ok, desc = check_wav(audio)
        add("ref_audio", ok, desc, "运行 GENERATE_XIAOYA_VOICE.cmd，或放入获授权的配对音频")
        txt = root / "voices" / "xiaoya" / "ref_text.txt"
        add("ref_text", txt.is_file() and bool(txt.read_text(encoding="utf-8").strip()) if txt.is_file() else False,
            "参考音频逐字稿", "准备与 WAV 逐字一致的 ref_text.txt")
        meta = root / "voices" / "xiaoya" / "ref_source.json"
        if meta.is_file():
            try:
                info = json.loads(meta.read_text(encoding="utf-8"))
                preview = info.get("quality") == "preview_replace_with_qwen_generated_voice"
                if preview:
                    add("preview_voice", False, "当前仍为机械合成试听音，不是最终甜美声线", "运行 GENERATE_XIAOYA_VOICE.cmd", caution=True)
            except (ValueError, OSError):
                add("voice_metadata", False, "音色来源标注无效", "检查 ref_source.json", caution=True)
        if flags["tts_device"] == "cuda" or flags["stt_device"] == "cuda" or mode == "digital":
            gpu_ok, name = probe_command(["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"])
            add("gpu", gpu_ok, (name if gpu_ok else "无法检测 NVIDIA 显卡"), "检查 NVIDIA 驱动与 nvidia-smi")
    if mode == "digital":
        docker_ok, _ = probe_command(["docker", "info", "--format", "{{.ServerVersion}}"])
        add("docker", docker_ok, "Docker Engine 是否就绪", "启动 Docker Desktop，启用 WSL2 GPU")
        if docker_ok:
            container_ok, out = probe_command(["docker", "inspect", "-f", "{{.State.Running}}", "duix-avatar-gen-video"])
            add("duix_container", container_ok and out.lower() == "true", "DUIX 容器运行状态", "运行 START_DUIX.cmd")
        else:
            add("duix_container", False, "未检查 Docker 容器", "先启动 Docker Desktop", caution=True)
        avatar = root / "data" / "duix" / "temp" / "my_avatar.mp4"
        add("avatar_video", avatar.is_file() and avatar.stat().st_size > 1024 if avatar.is_file() else False,
            "DUIX 形象视频素材（文件存在不代表已完成预处理）", "在 data/duix/temp/ 放入正确预处理的 my_avatar.mp4")
    failures = [c for c in checks if c["status"] == "fail"]
    return {"schema_version": 1, "mode": mode,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "ready_for_next_stage": len(failures) == 0,
            "pass": sum(c["status"] == "pass" for c in checks),
            "fail": len(failures),
            "warning": sum(c["status"] == "warning" for c in checks),
            "checks": checks,
            "validation_boundary": "静态环境检查；不证明已经成功运行 ASR、TTS 或 DUIX 视频生成"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("text", "voice", "digital"), default="digital")
    parser.add_argument("--strict", action="store_true", help="未通过要求时返回退出码 1")
    args = parser.parse_args(argv)
    data = collect(mode=args.mode)
    target = ROOT / "data" / "preflight_4090.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for c in data["checks"]:
        print(f"[{c['status'].upper()}] {c['id']}: {c['detail']}")
        if c["status"] != "pass":
            print("  NEXT:", c["next_action"])
    print(f"Report: data/preflight_4090.json | pass={data['pass']} fail={data['fail']} warn={data['warning']}")
    print("NOTE:", data["validation_boundary"])
    return int(args.strict and not data["ready_for_next_stage"])


if __name__ == "__main__":
    raise SystemExit(main())
