"""Safely configure optional NapCat OneBot QQ bridge; only one QQ ID allowed."""
from __future__ import annotations
import getpass
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
CFG=ROOT/'upstream'/'bridge'/'bridge-config.json'


def main():
    if not CFG.exists():
        print('[ERROR] 请先运行 INSTALL.cmd 安装原项目语音桥接。')
        return 1
    print('仅适合本人授权的 QQ 小号和私聊；不需要 QQ 功能直接退出。')
    enable=input('启用 QQ 联动？(y/N): ').strip().lower()=='y'
    cfg=json.loads(CFG.read_text(encoding='utf-8-sig'))
    qq=cfg.setdefault('qq', {})
    if enable:
        user=input('允许访问的 QQ 号（必须与 NapCat 对应目标一致）：').strip()
        if not user.isdigit() or int(user)<=0:
            print('[FAIL] QQ 号必须是正整数')
            return 1
        token=getpass.getpass('NapCat OneBot Access Token（输入不回显）：').strip()
        if not token:
            print('[FAIL] 未输入 Token')
            return 1
        qq.update({'enabled':True,'target_qq':int(user),
                   'napcat_base':'http://127.0.0.1:3000','napcat_token':token})
    else:
        qq['enabled']=False
    CFG.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('[OK] QQ 配置保存成功；请重启 START.cmd，使配置生效。')
    return 0


if __name__=='__main__':
    sys.exit(main())
