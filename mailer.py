# -*- coding: utf-8 -*-
"""이메일 발송.

카카오톡 '나에게 보내기'는 카카오가 "내가 나에게 쓴 메모"로 취급해서
푸시 알림이 뜨지 않습니다. 알림 설정을 모두 켜도 마찬가지였습니다.
사고 알림이 조용히 쌓이기만 하면 시스템 의미가 없으므로 이메일을 함께 씁니다.

이메일은 휴대폰 메일 앱이 확실히 알림을 띄우고, 여러 명에게 한 번에 갑니다.

필요한 환경변수 (GitHub Secrets)
  GMAIL_ADDRESS       보내는 계정 (예: myhoony.seol@gmail.com)
  GMAIL_APP_PASSWORD  구글 '앱 비밀번호' 16자리 (계정 비밀번호가 아닙니다)
  EMAIL_TO            받는 주소. 콤마나 줄바꿈으로 여러 명

셋 중 하나라도 없으면 이메일은 조용히 건너뜁니다(카카오톡은 그대로 갑니다).
"""
import os
import re
import smtplib
import sys
from email.header import Header
from email.mime.text import MIMEText

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465          # SSL


def recipients():
    raw = os.environ.get("EMAIL_TO", "")
    return [a.strip() for a in re.split(r"[,\n;]+", raw) if a.strip()]


def enabled(cfg) -> bool:
    if not getattr(cfg, "EMAIL_ENABLED", True):
        return False
    return bool(os.environ.get("GMAIL_ADDRESS")
                and os.environ.get("GMAIL_APP_PASSWORD")
                and recipients())


def send(subject: str, body: str, cfg) -> int:
    """받는 사람 전원에게 한 통씩 보냅니다. 보낸 수를 돌려줍니다."""
    if not enabled(cfg):
        return 0

    sender = os.environ["GMAIL_ADDRESS"].strip()
    password = os.environ["GMAIL_APP_PASSWORD"].strip().replace(" ", "")
    to_list = recipients()

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = Header(subject[:120], "utf-8")
    msg["From"] = sender
    msg["To"] = ", ".join(to_list)

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            smtp.login(sender, password)
            smtp.sendmail(sender, to_list, msg.as_string())
    except smtplib.SMTPAuthenticationError:
        print("[mail] 로그인 실패 — 구글 '앱 비밀번호'가 맞는지 확인하세요.",
              file=sys.stderr)
        print("       (계정 비밀번호가 아니라 16자리 앱 비밀번호입니다)",
              file=sys.stderr)
        return 0
    except Exception as e:                              # noqa: BLE001
        # 이메일이 실패해도 카카오톡은 이미 갔으므로 전체를 중단하지 않습니다.
        print(f"[mail] 발송 실패: {e}", file=sys.stderr)
        return 0

    print(f"[mail] {len(to_list)}명에게 발송 — {', '.join(to_list)}")
    return len(to_list)
