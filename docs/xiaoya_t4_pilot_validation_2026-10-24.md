# Xiaoya T4 SadTalker pilot — verified artifact and incident record (2026-10-24)

## Scope and acceptance criteria
This is a SadTalker single-image talking-head **inference** pilot on Kaggle T4, not training and not DUIX. Accept only a real `xiaoya_talking_pilot.mp4` with both video and audio tracks and duration 5–15 seconds. A green Kaggle submission alone is not acceptance.

## Reproducible result
- Source commit: `300a8d4e35e50d4154a0b1e3e03788452a86c7d9`.
- Source test run: https://github.com/mjw3177109/xunigirl/actions/runs/40065793661 (success).
- Kaggle submission run: https://github.com/mjw3177109/xunigirl/actions/runs/40065793495 (success, submission only).
- Collector run: https://github.com/mjw3177109/xunigirl/actions/runs/40065813578 (failure in *collector*, not Kaggle inference).
- Original Kaggle result artifact: https://github.com/mjw3177109/xunigirl/actions/runs/40065813578/artifacts/12549540827 (retained until 2026-11-08 UTC per GitHub API).
- The artifact includes `xiaoya_video_results/xiaoya_talking_pilot.mp4`, `video_report.json`, Kaggle logs and inference logs.
- Locally downloaded this exact GitHub artifact and ran `ffprobe` on its extracted MP4 on 2026-10-24 UTC.
- **ffprobe**: H.264 video, 256x256; AAC audio, 16,000 Hz; duration **8.240000 seconds**; MP4 size **169847 bytes**; SHA-256 `df17edc9aac73ba68f447958ab29c59d4e85dacf71b7b42cd63308862f1474be`.
- `ffmpeg -v error -i xiaoya_talking_pilot.mp4 -f null -` completed with exit status 0.
- Kaggle `video_report.json`: `status=actual_mp4_generated`, elapsed inference `130.56` seconds. This is a proof-of-generation and technical integrity check, not a subjective lip-sync/visual-quality rating.

## Defect → root cause → minimal repair → verification
1. Previous failures: facexlib missing, face-crop OpenCV empty image, NumPy 2 mixed-shape `trans_params`, and `np` missing in the notebook compatibility cell. They were fixed in earlier commits; don't repeat them.
2. New collector failure in run `40065813578`: `FileNotFoundError: [Errno 2] No such file or directory: 'ffprobe'` during the acceptance step. The real MP4 **was** downloaded; the CI runner lacked the ffprobe executable.
3. Minimal fix in commit `5ef53b1683b19b57e42bcdf3c5dbdcc2dd2d69ed`: install `ffmpeg` (provides `ffprobe`) in the collector and add a collector-only `push` trigger on changes to its own workflow file. The Kaggle submission workflow does not watch the collector file, avoiding a new GPU run for this CI-only problem.
4. Collector-only verification run: https://github.com/mjw3177109/xunigirl/actions/runs/40069628527. Check this run for final independent CI acceptance; local ffprobe has already confirmed the original artifact.

## Follow-up quality notes
- Renderer log warns that 256x250 source frames were resized to 256x256 for macroblock compatibility. This is a quality consideration, **not** an acceptance failure.
- Next optimization should compare facial fidelity, lip sync and framing using the actual video; keep a baseline artifact and do not launch a new GPU job until a measurable change is proposed.
- Record each new failure only once, and distinguish GPU inference, collector verification, and perceptual quality.
