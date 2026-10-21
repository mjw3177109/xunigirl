# 小雅音色 / Voice reference

`voices/xiaoya/ref_audio.wav` **已经随 ZIP 提供**，`ref_text.txt` 为该音频逐字对应的中文台词。 该内置 WAV 是**轻量离线合成试听版**（eSpeak），音色偏机械，仅用于让程序找到真实的 16kHz 单声道 PCM WAV 文件，并验证克隆链路；它不是高质量神经声音。

运行 `INSTALL.cmd` 时会尝试使用 **Qwen3-TTS 0.6B-CustomVoice** 在本机 RTX 4090 上自动生成更自然、明亮偏高音的成年女性中文声线，并替换 `ref_audio.wav`。整个过程不需要授权真人声音，也无需 DSH、ComfyUI。

也可以双击 `GENERATE_XIAOYA_VOICE.cmd` 手动重新生成（此命令会明确覆盖小雅音色），然后运行 `CONFIGURE_VOICE.cmd` 与 `SMOKE_TTS.cmd`。此步骤首次需要联网下载 CustomVoice 权重；日常回复继续使用低显存的 0.6B **Base** 克隆模型，无须让 CustomVoice 常驻显存。

生成结果会在 `ref_source.json` 中标记来源。`ref_text.txt` 内容不可与录音不符，变更文字后须重新生成音频。

如果希望使用有授权的真人参考录音，请创建另一个 `voices/<自定义音色名>/` 目录，放 `ref_audio.wav` + `ref_text.txt`，避免改写预设样音。
