"""Set a 4090 digital-video profile without changing user secrets or other settings.

The DUIX container remains on-demand (DIGITAL_HUMAN_ENABLED=0 at service boot).
Turn it on via the web UI after launching START_DUIX.cmd. The profile selects
which speech models run on the GPU, not a hard GPU-VRAM limit.
"""
from __future__ import annotations
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV = ROOT / ".env"
TEMPLATE = ROOT / ".env.example"
PRESETS = {
    "min": {"TTS_SIZE": "0.6", "STT_DEVICE": "cpu", "TTS_DEVICE": "cuda", "DIGITAL_HUMAN_ENABLED": "0"},
    "quality": {"TTS_SIZE": "1.7", "STT_DEVICE": "cpu", "TTS_DEVICE": "cuda", "DIGITAL_HUMAN_ENABLED": "0"},
}


def apply_profile(text: str, profile: str) -> str:
    values = PRESETS[profile]
    result: list[str] = []
    touched: set[str] = set()
    for line in text.splitlines():
        trimmed = line.strip()
        if trimmed and not trimmed.startswith("#") and "=" in line:
            key = line.split("=", 1)[0].strip()
            if key in values:
                if key not in touched:
                    result.append(f"{key}={values[key]}")
                    touched.add(key)
                continue
        result.append(line)
    for key, value in values.items():
        if key not in touched:
            result.append(f"{key}={value}")
    return "\n".join(result).rstrip("\n") + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="RTX 4090 digital human profile")
    parser.add_argument("profile", choices=sorted(PRESETS))
    args = parser.parse_args()
    if not ENV.exists() and not TEMPLATE.exists():
        raise SystemExit("找不到 .env 和 .env.example，请把补丁覆盖到原项目根目录")
    raw = (ENV if ENV.exists() else TEMPLATE).read_text(encoding="utf-8-sig")
    ENV.write_text(apply_profile(raw, args.profile), encoding="utf-8")
    print(f"[OK] 已选择 {args.profile} 数字人模式。DeepSeek Key 及其他配置保持不变。")
    print("  " + " / ".join(f"{k}={v}" for k, v in PRESETS[args.profile].items()))
    print("  注意：DUIX 按需启动。先 START_DUIX.cmd，之后在网页里启用“数字人口播”。")
    print("  第一次切换 TTS_SIZE 后，请重新运行 INSTALL.cmd + CONFIGURE_VOICE.cmd。")


if __name__ == "__main__":
    main()
