# 小雅 · 成年御姐形象 × 甜美轻柔高音（V1.3）

## 这次已直接包含的文件

- `voices/xiaoya/ref_audio.wav`：已生成**实际 WAV 文件**（16kHz、单声道、16 位），可作基础接口联调。
- `voices/xiaoya/ref_text.txt`：参考语音逐字稿。
- `voices/xiaoya/ref_source.json`：音频来源及质量说明。
- `assets/portraits/xiaoya.png`：已经生成的成年女性全身造型图片。
- `web/index.html` + `web/style.css` + `backend/main.py`：启动聊天网页即可显示小雅静态肖像。
- `tools/generate_xiaoya_voice.py`、`GENERATE_XIAOYA_VOICE.cmd`：RTX 4090 上一键合成自然的甜美成年女性中文声线。

## 为什么还提供生成脚本？

打包环境无法下载 Qwen3-TTS 模型权重，所以压缩包中随附的试听 WAV 使用离线 eSpeak 生成，**语音明显机械，不代表最终高质量声音**。这不是静音占位文件；可播放但不推荐作为最终克隆音色。首次运行 `INSTALL.cmd` 会尝试自动从 Qwen3-TTS 0.6B CustomVoice 生成更自然的音色，并保留日常使用 0.6B Base（低显存）进行克隆。若网络或 CUDA 不可用，试听 WAV 不会丢失，稍后运行 `GENERATE_XIAOYA_VOICE.cmd` 即可重新生成。

## 重要：DUIX 视频素材与人像图片的区别

`assets/portraits/xiaoya.png` 仅用于前端静态角色图展示及后续视频制作参考；**这张 PNG 不是 DUIX 能直接合成口型的预处理数字人形象视频**。要让 DUIX 输出口型同步 MP4，仍需根据 DUIX 形象预处理要求制作 `data/duix/temp/my_avatar.mp4` 和相应依赖资产，并做 4090 实机测试。没有这些素材时仍可文字/语音聊天并显示肖像。

## 运行步骤

1. 双击 `INSTALL.cmd`（自动准备模型，并尝试升级内置机械试听音频）。
2. 在 `.env` 写入 DeepSeek API Key。
3. 双击 `CONFIGURE_VOICE.cmd`，再双击 `START.cmd`。
4. 运行 `SMOKE_TTS.cmd` 试声。若音色仍机械，运行 `GENERATE_XIAOYA_VOICE.cmd`。
5. 若要动态口型视频，再准备 DUIX 形象视频、运行 `START_DUIX.cmd`。
