# GitHub 完整同步说明

当前 ChatGPT GitHub 连接已将项目说明、基础配置和核心 Python 后端直接提交至 `mjw3177109/xunigirl`。

如果网页、工具和图片/参考音频尚未出现在 GitHub，请在 **本 ZIP 解压目录** 下运行 `PUBLISH_GITHUB.cmd`。
该脚本会将本地完整 V1.3 源码与素材提交到 `https://github.com/mjw3177109/xunigirl` 的 main 分支，保留已有 GitHub 提交历史。

需要本地已安装 Git for Windows 并登录具有仓库写权限的 GitHub 账号。

## 安全

不会推送 `.env`、`.venv`、`upstream`、`models`、聊天数据库、日志或模型缓存；
会推送 `voices/xiaoya/ref_audio.wav`、参考文本以及 `assets/portraits/xiaoya.png`。
默认仅推送，没有强制推送。

推送后在仓库中核验 `backend/main.py`、`web/app.js`、`assets/portraits/xiaoya.png`、`voices/xiaoya/ref_audio.wav`。

```powershell
Get-Item .\voices\xiaoya\ref_audio.wav
Get-Item .\assets\portraits\xiaoya.png
```
