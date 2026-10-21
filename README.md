# V1.4 增量改进：4090 部署预检与数字人开关持久化

- 新增 `PRECHECK_4090.cmd`，检查 DeepSeek Key 是否配置（不会输出 Key）、声音模型、16kHz WAV、GPU、Docker 与 DUIX 形象素材。
- 检查报告保存在 `data/preflight_4090.json`；默认不调用收费 API，也不会生成视频。
- 修复 `CONFIGURE_VOICE.cmd` 重复执行时把网页开启的数字人重新设置为关闭的问题。仅首次安装采用 `.env` 的开关默认值；之后保留网页保存的开关。
- 如确实需要强制重置数字人状态，可临时设置环境变量 `VC_RESET_DH_ON_CONFIG=1` 后执行 `CONFIGURE_VOICE.cmd`。
- **验收边界**：上述检查只证明文件和服务环境的基础状态；真实声音合成和口播视频必须在 Windows + 4090 上单独测试。

---

# V1.2 · RTX 4090 数字人完整整合版（2026-10-19）

**本 ZIP 已整合 V1.1 完整源码 + V1.2 低显存数字人补丁。无需再覆盖旧补丁。**

- LLM：云端 DeepSeek API（本地 LLM 显存 0GB）
- STT：FunASR 使用 CPU；TTS：Qwen3-TTS 0.6B Base 使用 RTX 4090（默认低显存档）
- 视频：DUIX 独立容器，只有主动运行 `START_DUIX.cmd` 并在网页开启数字人后才开始生成
- 可选高音质：`SELECT_4090_VIDEO_QUALITY.cmd` 更换 1.7B 声音模型（之后需安装对应模型）
- **注意**：本包包含可执行的前后端和安装脚本，首次安装仍需要联网获取固定提交的上游语音桥接源码与模型，以及 DUIX Docker 镜像；未包含数 GB 的模型权重及个性音色/数字人素材。
- **验收边界**：离线单元测试通过，4090 CUDA / TensorRT 视频实机生成尚未完成测试。

## 首次安装（推荐次序）

1. Windows 11；安装 Python 3.11 x64、NVIDIA 驱动、Git（可选）、Docker Desktop + WSL2（启用 GPU）。
2. 解压到不含特殊权限限制的文件夹（例如 `D:\VoiceCompanion4090`）。
3. 双击 `INSTALL.cmd`（会下载语音源码、依赖、FunASR、0.6B TTS 和 VAD）。
4. 编辑根目录 `.env`，只填自己的 `DEEPSEEK_API_KEY`。不要公开这个文件。
5. 在 `voices\xiaoya\` 添加有权使用的 `ref_audio.wav` 与对应的 `ref_text.txt`，运行 `CONFIGURE_VOICE.cmd`。
6. 双击 `START.cmd`，打开 `http://127.0.0.1:8765/`，先验收文字和纯语音对话。
7. 准备 DUIX 适配过的形象视频，放到 `data\duix\temp\my_avatar.mp4`；双击 `START_DUIX.cmd`。
8. 在网页开启“数字人口播”，运行 `CHECK_DIGITAL_4090.cmd`，然后做真实视频生成验证。

如需要切换声音模型：运行 `SELECT_4090_VIDEO_MIN.cmd` 或 `SELECT_4090_VIDEO_QUALITY.cmd`，然后 `STOP.cmd` → `INSTALL.cmd` → `CONFIGURE_VOICE.cmd` → `START.cmd`。

详细的 GPU / 数字人说明参见 `docs/4090_最低数字人部署说明.md`。

---

# VoiceCompanion · DeepSeek + RTX 4090 独立版 V1.1

> **代码交付版**：项目自身的独立 API、网页、语音采集、DeepSeek 流式对话、SQLite 会话/记忆、TTS 朗读、数字人播放、音色/形象选择、打断控制、安装启动与自测脚本已经编写完成；不需要 DSH、Node.js、pnpm 或本地 DeepSeek 模型。
>
> **诚实的验证边界**：已通过离线代码/API 测试；尚未在你的 Windows + RTX 4090 上执行真实 ASR/TTS/DUIX 推理，不能把“代码已写好”说成“4090 GPU 全链路已验证”。

## 1. 首次安装（建议先文字版）

准备 Windows 10/11、Python **3.11 x64**、Git 非必需（自动下载源码 ZIP）、DeepSeek 官方 API Key。将 ZIP 解压至例如 `D:\VoiceCompanion4090` 的路径。

1. 双击 **`INSTALL_TEXT_ONLY.cmd`**，自动创建 `.venv`、安装独立服务依赖并复制 `.env`。
2. 用记事本编辑根目录 `.env`，填写 `DEEPSEEK_API_KEY=sk-...`；密钥不进入 SQLite，也不返回网页。
3. 双击 **`START.cmd`**，打开 `http://127.0.0.1:8765/`，发送文字测试。
4. 双击 **`STOP.cmd`** 关闭；双击 **`SELF_TEST.cmd`** 运行离线测试；`VERIFY_FILES.cmd` 校验包内所有源文件 SHA256。

DeepSeek API 按 Token 计费；本地 DeepSeek 模型显存占用为零。默认选择 `deepseek-flash`，可在页面改为 `deepseek-v4-pro`。流式输出只使用 final `content`，不朗读 `reasoning_content`。

## 2. 安装真正的 4090 本地语音

需要安装 NVIDIA 驱动，`nvidia-smi` 能显示 RTX 4090，留出约 20–30GB 以上磁盘空间，建议 32GB+ 内存。默认选用 1.7B 克隆音色；**更省显存可在 `.env` 里设置 `TTS_SIZE=0.6`**，重新执行 `INSTALL.cmd`、`CONFIGURE_VOICE.cmd` 后会下载并切换 0.6B-Base；两者都需要合法参考音频。

1. 关闭现有服务（`STOP.cmd`），双击 **`INSTALL.cmd`**。
2. 安装脚本自动下载原项目固定源码 `beiyege-01/dsh-voice-ai-girlfriend` 的 commit `480bbabada7335735cad591eaa55f32fe54a4214`，并仅复用其**Python 语音桥接代码**，不安装其 DSH 前端插件；自动修补硬编码路径。
3. 同一脚本安装上游 `speech-to-speech`、FunASR、ModelScope 等依赖并下载模型（依赖与模型较大，网络需访问 GitHub、PyPI、ModelScope）。
4. 在 `voices\xiaoya\` 中放入拥有合法使用权的 `ref_audio.wav` 和与录音逐字匹配的 `ref_text.txt`（建议 5–20 秒清晰人声）。音色不是代码文件，无法预先替你制作或嵌入。
5. 双击 **`CONFIGURE_VOICE.cmd`** 重新扫描音色，然后 **`START.cmd`**。
6. 双击 **`SMOKE_TTS.cmd`**，执行真正的 Qwen3-TTS 推理；成功后会生成 `data\smoke_tts.wav`。也可以打开页面，录音经 FunASR 转文字、回复使用 Qwen3-TTS。

配置完成后，项目会使用原项目提供的 `/voice/api/stt`、`/voice/api/tts`、`/voice/api/persona/*`、`/voice/api/vad` 和 `/voice/api/dh/*` 接口。语音服务未准备好时文字聊天仍能启动。

**免按键插话**：页面右侧提供单独开关（默认关闭），通过本地 Silero VAD WebSocket 检测用户说话；为了降低扬声器回声误判，建议佩戴耳机。浏览器需要授予麦克风权限。该逻辑已编写但实际降噪/打断效果有待 4090 现场验收。也支持点击“说话”手动中止回复并录音。

## 3. DUIX 本地数字人（可选）

安装并启动 Docker Desktop，确保 WSL2/NVIDIA GPU 容器工作正常。参照 DUIX 官方部署文档下载它所需的模型和素材，准备你有权使用的形象视频：`data\duix\temp\my_avatar.mp4`。

双击 `START_DUIX.cmd` 将启动 `docker/compose-4090.yml`，镜像为 **`guiji2025/duix.avatar:latest`**（通用镜像，不是 RTX 50 系 TensorRT 特制版），映射 `127.0.0.1:9000 -> 8383`。然后在网页中打开“数字人口播”，由原项目 Python 服务负责音频合成、分段提交、结果轮询和口播播放。

容器成功启动并不能保证模型已经下载完成、ONNX/TensorRT 使用 GPU 或所有生成路径可用。使用 `docker logs duix-avatar-gen-video` 与 `nvidia-smi` 核验。失败时关闭网页中的数字人开关，仍可使用普通语音。停止运行 `STOP_DUIX.cmd`。

**注意**：原项目是逐段视频生成再播放，不是逐帧低延迟数字人。本版也不擅自宣称达到实时视频聊天。

## 4. QQ 私聊联动（可选）

这个功能**需要用户自己已有的 NapCat/OneBot 服务与授权 QQ 小号**，本包只负责连接，不会自动登录 QQ 或下载 NapCat。

1. 先运行 `INSTALL.cmd` 完成 Python 语音桥接安装，再运行 **`CONFIGURE_QQ.cmd`**，输入唯一允许私聊的 QQ 号与 NapCat Access Token。配置保存到本地 `upstream/bridge/bridge-config.json`，不会上传 GitHub。
2. 配置 NapCat 的 HTTP 服务为 `http://127.0.0.1:3000`，并把 OneBot 事件上报设为 `http://127.0.0.1:8765/voice/api/qq/event`；也可以使用 WS 客户端 `ws://127.0.0.1:8765/voice/api/qq/onebot`。具体字段以你安装的 NapCat 版本为准。
3. 重启 `START.cmd`，在页面勾选“QQ 私聊联动”。仅配置的 QQ ID 的私聊会进入聊天页面，DeepSeek 回复后，原桥接会按配置将文字与语音发给该 QQ。
4. 不使用时关闭网页开关，并通过 `CONFIGURE_QQ.cmd` 选 `N` 关闭后端 QQ 联动。访问凭据只能存于本机，**不能将 NapCat 或本地语音服务暴露到公网**。

## 5. 全部代码目录

```text
VoiceCompanion_DeepSeek_4090_V1.1/
├── backend/
│   ├── main.py                 # 独立 FastAPI/LLM/SSE/会话/取消/GPU/记忆 API
│   └── store.py                # SQLite 会话 + 用户手动长期记忆
├── web/
│   ├── index.html              # 完整独立界面
│   ├── app.js                  # 录音、语音识别、TTS、Silero 插话、DUIX、历史/记忆
│   ├── style.css
│   └── worklet.js              # AudioWorklet 16k 音频输入处理
├── tools/
│   ├── configure_upstream.py   # 固定源码兼容修补
│   ├── download_models.py     # 下载 STT/TTS/VAD 模型
│   ├── smoke_tts.py           # 本地真实 TTS 试运行
│   └── check.py               # 静态与 HTTP 健康检查
├── scripts/                    # PowerShell 安装、启动和安全停止
├── docker/compose-4090.yml    # 可选 DUIX GPU 容器
├── tests/                      # 离线自动测试
├── config/persona.txt         # 人物设定
├── voices/xiaoya/              # 已放入试听 WAV + 文本；安装时尝试生成自然女声
├── data/                       # SQLite、运行日志、DUIX 输出
├── upstream/                   # INSTALL.cmd 自动拉取的第三方代码（不会安装 DSH）
├── .env.example                # DeepSeek API 配置模板
├── INSTALL_TEXT_ONLY.cmd
├── INSTALL.cmd
├── CONFIGURE_VOICE.cmd
├── START.cmd
├── STOP.cmd
├── START_DUIX.cmd
├── STOP_DUIX.cmd
├── CONFIGURE_QQ.cmd
├── SMOKE_TTS.cmd
├── SELF_TEST.cmd
├── VERIFY_FILES.cmd
└── CHECK.cmd
```

## 6. 接口及状态

| API | 功能 | 完成情况 |
| --- | --- | --- |
| `GET /api/app/status` | 运行状态/API Key 是否配置 | 已写/离线通过 |
| `GET /api/app/gpu` | 查看 NVIDIA 显存 | 已写，需 Windows 实测 |
| `POST /api/app/chat/stream` | DeepSeek 云端 SSE 流式聊天 | 已写/模拟 API 通过，真实 Key 未测试 |
| `POST /api/app/cancel` | 取消当前 LLM 回合 | 已写/离线通过 |
| `GET/POST /api/app/sessions` | 会话列表/新增 | 已写/离线通过 |
| `GET/POST/DELETE /api/app/memories` | 手动长期记忆 | 已写/离线通过 |
| `/voice/api/stt` | FunASR 语音识别 | 上游代码已接入；4090 待验收 |
| `/voice/api/tts` | Qwen3-TTS 克隆 | 上游代码已接入；4090 待验收 |
| `/voice/api/vad` | Silero 检测真人插话 | 前后端代码已写；4090 待验收 |
| `/voice/api/dh/*` | DUIX 数字人口播 | 上游代码已接入；4090 Docker 待验收 |

## 7. 故障排查

- **网页打不开**：运行 `CHECK.cmd`，查 `data\server.stderr.log`；如果端口 `8765` 被占，先检查占用进程，不要强制结束未知程序。
- **DeepSeek 报 401/402/429**：检查 API Key、余额、限额。官方地址 `https://api.deepseek.com`，本版支持 `deepseek-flash` 和 `deepseek-v4-pro`。
- **文字可用、语音不能用**：先确认 `upstream/bridge/voice_bridge.py` 和模型已自动安装，再运行 `CONFIGURE_VOICE.cmd`、`SMOKE_TTS.cmd`。
- **数字人没有输出**：先确保 `my_avatar.mp4` 和 DUIX 模型文件准备齐全，检查 `http://127.0.0.1:9000/easy/query?code=probe`、Docker 日志以及 `nvidia-smi`。
- **GPU 不足或 GPU 仍忙**：关闭数字人口播、停止 DUIX 容器，按需只启用文字+语音；当前版本**没有**自动全局 GPU 抢占调度器。
- **麦克风插话误识别**：优先使用耳机/关闭免按键插话，再使用手动麦克风按钮。
- **版本更新**：语音桥接锁定了原项目 commit；不要随意替换其源码，否则自动补丁与接口可能不兼容。

## 8. 数据与权限

本地 SQLite 保存聊天、手动记忆；聊天文本和记忆会随着聊天请求发送给云端 DeepSeek，不能宣称完全离线或所有数据只保存在本机。密钥保存在根 `.env`，不通过浏览器提交。应用仅监听 `127.0.0.1`，不能直接放到公网提供多人服务。克隆音色必须得到参考人声的授权。原项目媒体为演示素材，商用前须检查许可证和版权。

## 9. 来源

- 原语音桥接：<https://github.com/beiyege-01/dsh-voice-ai-girlfriend>
- DeepSeek 官方 API：<https://api-docs.deepseek.com/>
- Qwen3-TTS：<https://github.com/QwenLM/Qwen3-TTS>
- DUIX：<https://github.com/duixcom/Duix-Avatar>

本 ZIP 预置的是**完整自主编写代码和部署脚本**，不包含模型权重和第三方受限媒体；已内置可播放的机械合成参考 WAV 与自生成角色肖像。自然甜美女声需在用户 RTX 4090 安装时通过额外 CustomVoice 模型生成。上游语音 Python 代码由安装器按固定提交下载，不需要另外手工开发。


## 小雅角色 / 参考声音（新增 V1.3）

详见 `README_小雅角色和声音.md`。随包包含 `voices/xiaoya/ref_audio.wav`（离线机械合成试听文件、不是高质量拟人 TTS 成品）与 `assets/portraits/xiaoya.png`。完整安装时会自动尝试下载 0.6B CustomVoice 模型以生成自然甜美成年女性音色，日常仍使用 0.6B Base，安装后可 `SMOKE_TTS.cmd` 验证。
