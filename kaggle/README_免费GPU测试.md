# V1.5：Kaggle 免费 GPU 小雅真实声音测试

这是按需运行的 **真实 GPU 推理验收**，不是把免费 Notebook 当作长期运行的服务器。Kaggle 目前免费 GPU 选择 T4 × 2；每张 T4 各 16GB 显存，不能直接合并为 32GB。

## 直接运行 Notebook

1. 登录 https://www.kaggle.com/code ，创建 Notebook 并导入仓库的 `kaggle/xiaoya_t4_gpu_test.ipynb`。
2. 在 Kaggle Settings 打开 **GPU T4 x2** 和 **Internet=On**。
3. Run All：先合成小雅成熟外形对应的甜美成年女性参考声音，再运行 0.6B Base 声音克隆。
4. 下载 Output 中 `xiaoya_results/xiaoya_gpu_results.zip`。内含 `ref_audio.wav`、`ref_text.txt`、`clone_test.wav` 和 `gpu_report.json`。
5. 先试听，确认后覆盖 Windows 项目 `voices/xiaoya/` 的同名音频与文本，运行 `CONFIGURE_VOICE.cmd`。

Notebook 不需要 DeepSeek Key，也不会把用户的私人音频上传到外部账户。模型首次下载需要联网且可能较慢。

## GitHub Actions 提交 Kaggle（可选）

GitHub 仓库 Settings → Secrets and variables → Actions 中新增：

- **Secret:** `KAGGLE_API_TOKEN`（在 https://www.kaggle.com/settings/api 创建）。绝对不要直接写进代码或聊天消息。
- 在 GitHub Actions 的工作流 `Kaggle Free GPU Xiaoya` 中输入你的 Kaggle 用户名，点击 Run workflow。

该动作只把 Notebook 提交给 Kaggle，并申请 T4；GPU 是否真正分配、是否完成推理必须查看 Kaggle 任务状态、输出和日志。没有 Secret 时会失败而不会伪报成功。

## 验收界限

- Kaggle GPU 通过只能证明 Qwen3-TTS 0.6B 在 T4 上的声音合成/克隆链路。
- 不能证明 Windows RTX 4090 的驱动、DUIX Docker 和真实数字人口播 MP4 已通过。
- DUIX 要单独找提供 GPU 容器权限和足够磁盘的环境验证；不要在无 Docker 权限的 Kaggle Notebook 中假装成功。
