# GitHub 完整同步说明

当前 GitHub 仓库 `mjw3177109/xunigirl` 已包含基础配置和核心 Python 后端。

**完整 V1.3 包含 60 个代码、脚本和资源文件，部分文件尚需从下载的完整 ZIP 导入。** 不能只用现在的仓库文件作为可运行完整版本。

下载 ChatGPT 提供的 `VoiceCompanion_V1.3_GitHub发布版.zip`，解压到本地，双击 `PUBLISH_GITHUB.cmd` 即可将全部源文件、小雅 PNG 和参考 WAV 同步到 main。

脚本将通过 GitHub Credential Manager 使用你登录的 GitHub 账号，正常提交，不强制推送，不上传 `.env`、`.venv`、模型权重、聊天数据库等私有数据。

完成后检查：
- `backend/main.py`
- `web/app.js`
- `assets/portraits/xiaoya.png`
- `voices/xiaoya/ref_audio.wav`
