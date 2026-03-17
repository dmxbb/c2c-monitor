#!/usr/bin/env python3

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ── 配置区（从环境变量读取） ──────────────────────────────────────────────────

# 飞书机器人 Webhook 地址和签名密钥
FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")
FEISHU_SECRET = os.environ.get("FEISHU_SECRET", "")

# 邮件配置（暂时保留，不使用）
# QQ_EMAIL     = os.environ["QQ_EMAIL"]
# QQ_AUTH_CODE = os.environ["QQ_AUTH_CODE"]

BASE_URL = "https://www.gate.com/json_svr/query_c2cloan"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.gate.com",
    "referer": "https://www.gate.com/zh/c2cloan/cny",
}

PAY_TYPE_MAP = {0: "微信", 1: "支付宝", 2: "银行卡"}


# ── 抓取 ──────────────────────────────────────────────────────────────────────


def fetch_first_page(list_type: str, limit: int = 20) -> list:
    payload = {
        "type": list_type,
        "amount_seq": 0,
        "period": 0,
        "paytype": 0,
        "page": 1,
        "limit": limit,
    }
    try:
        resp = requests.post(
            BASE_URL,
            headers=HEADERS,
            data=payload,
            verify=False,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("list", [])
    except Exception as e:
        print(f"⚠️  抓取失败 [{list_type}]: {e}")
        return []


# ── 格式化消息正文 ────────────────────────────────────────────────────────────


def format_order_text(order: dict) -> str:
    rate = order["rate"]
    period = order["period"]
    amount = order["initial_amount"]
    annual_rate = rate * 365
    interest = amount * (rate / 100) * period
    pay_types = "、".join(
        PAY_TYPE_MAP.get(p, str(p)) for p in order.get("pay_type_num", [])
    )
    loan_type = "借入" if order.get("is_borrow") == 1 else "借出"
    sell_out = "已售罄" if order.get("is_sell_out") == 1 else "可借"
    renew = "支持" if order.get("renew") == 1 else "不支持"

    return f"""【C2C 法币借贷挂单通知】

挂单类型：{loan_type}
──────────────────────────────
用户信息
  昵称：{order.get("nick")}
  姓名：{order.get("username")}
  等级：V{order.get("tier")}
  最后上线：{order.get("online_status")} 分钟前

借贷条件
  挂单金额：¥{amount:,.0f}
  可借范围：¥{order.get("min_amount"):,.0f} ~ ¥{order.get("max_amount"):,.0f}
  日息：{rate}%
  年化利率：{annual_rate:.2f}%
  期限：{period} 天
  预计总利息：¥{interest:,.2f}
  续借：{renew}
  状态：{sell_out}

抵押信息
  抵押币种：{order.get("pledge_type")}
  抵押数量：{order.get("pledge_amount")}

支付方式：{pay_types}
挂单时间：{order.get("time")}
挂单编号：{order.get("orderid")}
──────────────────────────────"""


# ── 生成飞书签名 ──────────────────────────────────────────────────────────────


def gen_feishu_sign(secret: str, timestamp: int) -> str:
    string_to_sign = f"{timestamp}\n{secret}"
    hmac_code = hmac.new(
        string_to_sign.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    return base64.b64encode(hmac_code).decode("utf-8")


# ── 发送飞书机器人消息 ────────────────────────────────────────────────────────


_send_cache: dict[str, float] = {}

CACHE_TTL_SECONDS = 2 * 3600  # 缓存 TTL：2 小时
MIN_RESEND_SECONDS = 1 * 3600  # 相同内容最短重发间隔：1 小时


def _text_hash(text: str) -> str:
    """取消息内容的 MD5 作为缓存 key。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _clean_expired_cache() -> None:
    now = time.time()
    expired = [k for k, v in _send_cache.items() if now - v > CACHE_TTL_SECONDS]
    for k in expired:
        del _send_cache[k]


def send_feishu(text: str) -> None:
    if not FEISHU_WEBHOOK:
        print("  ⚠️  未配置 FEISHU_WEBHOOK，跳过发送")
        return

    _clean_expired_cache()

    now = time.time()
    key = _text_hash(text)
    last_sent = _send_cache.get(key)

    if last_sent is not None:
        elapsed = now - last_sent
        if elapsed < MIN_RESEND_SECONDS:
            remaining = int((MIN_RESEND_SECONDS - elapsed) / 60)
            print(
                f"  ⏭️  相同内容 {MIN_RESEND_SECONDS // 3600} 小时内已发过，还需等待 {remaining} 分钟"
            )
            return

    timestamp = int(now)
    sign = gen_feishu_sign(FEISHU_SECRET, timestamp)
    payload = {
        "timestamp": str(timestamp),
        "sign": sign,
        "msg_type": "text",
        "content": {"text": text},
    }
    try:
        resp = requests.post(
            FEISHU_WEBHOOK,
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=10,
        )
        result = resp.json()
        if result.get("StatusCode") == 0 or result.get("code") == 0:
            print("  ✅ 飞书消息已发送")
            _send_cache[key] = now  # 发送成功才写缓存
        else:
            print(f"  ❌ 飞书发送失败：{result}")
    except Exception as e:
        print(f"  ❌ 飞书发送异常：{e}")


# ── 发送邮件（暂时保留，不使用） ──────────────────────────────────────────────

# def send_email(subject: str, body: str) -> None:
#     message = MIMEText(body, "plain", "utf-8")
#     message["From"]    = QQ_EMAIL
#     message["To"]      = "379473407@qq.com"
#     message["Subject"] = Header(subject, "utf-8")
#
#     try:
#         smtp_obj = smtplib.SMTP_SSL("smtp.qq.com", 465)
#         smtp_obj.login(QQ_EMAIL, QQ_AUTH_CODE)
#         smtp_obj.sendmail(QQ_EMAIL, ["379473407@qq.com"], message.as_string())
#         print(f"  ✅ 邮件已发送：{subject}")
#     except smtplib.SMTPException as e:
#         print(f"  ❌ 邮件发送失败：{e}")
#     finally:
#         smtp_obj.quit()


# ── 主流程 ────────────────────────────────────────────────────────────────────


def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'=' * 50}\n  {now}\n{'=' * 50}")

    for list_type, label in [
        ("market_borrow_list", "借入"),
    ]:
        print(f"\n[{label}] 抓取中...")
        orders = fetch_first_page(list_type)
        print(f"  共 {len(orders)} 条")

        for order in orders:
            oid = order.get("orderid")

            # 跳过已售罄的挂单（按需注释掉这行）
            if order.get("is_sell_out") == 1:
                continue

            print(f"  发送飞书通知：#{oid}...")
            text = format_order_text(order)
            send_feishu(text)
            break

    print("\n本次运行完成")


if __name__ == "__main__":
    # 每分钟运行一次
    main()
