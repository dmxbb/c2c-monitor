#!/usr/bin/env python3
"""
Gate.com C2C 法币借贷监控脚本
- 每次运行抓取第一页借入/借出挂单
- 配合 GitHub Actions 每5分钟运行一次

依赖: pip install requests
"""

import os
import smtplib
import urllib3
import requests
from datetime import datetime
from email.mime.text import MIMEText
from email.header import Header

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ── 配置区（从环境变量读取） ──────────────────────────────────────────────────

QQ_EMAIL     = os.environ["QQ_EMAIL"]
QQ_AUTH_CODE = os.environ["QQ_AUTH_CODE"]

BASE_URL = "https://www.gate.com/json_svr/query_c2cloan"
HEADERS  = {
    "accept":          "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9",
    "content-type":    "application/x-www-form-urlencoded",
    "origin":          "https://www.gate.com",
    "referer":         "https://www.gate.com/zh/c2cloan/cny",
}

PAY_TYPE_MAP = {0: "微信", 1: "支付宝", 2: "银行卡"}


# ── 抓取 ──────────────────────────────────────────────────────────────────────

def fetch_first_page(list_type: str, limit: int = 20) -> list:
    payload = {
        "type":       list_type,
        "amount_seq": 0,
        "period":     0,
        "paytype":    0,
        "page":       1,
        "limit":      limit,
    }
    try:
        resp = requests.post(
            BASE_URL, headers=HEADERS, data=payload,
            verify=False, timeout=30,
        )
        resp.raise_for_status()
        return resp.json().get("data", {}).get("list", [])
    except Exception as e:
        print(f"⚠️  抓取失败 [{list_type}]: {e}")
        return []


# ── 格式化邮件正文 ────────────────────────────────────────────────────────────

def format_order_email(order: dict) -> str:
    rate        = order["rate"]
    period      = order["period"]
    amount      = order["initial_amount"]
    annual_rate = rate * 365
    interest    = amount * (rate / 100) * period
    pay_types   = "、".join(PAY_TYPE_MAP.get(p, str(p)) for p in order.get("pay_type_num", []))
    loan_type   = "借入" if order.get("is_borrow") == 1 else "借出"
    sell_out    = "已售罄" if order.get("is_sell_out") == 1 else "可借"
    renew       = "支持" if order.get("renew") == 1 else "不支持"

    return f"""【Gate.com C2C 法币借贷挂单通知】

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


# ── 发送邮件 ──────────────────────────────────────────────────────────────────

def send_email(subject: str, body: str) -> None:
    message = MIMEText(body, "plain", "utf-8")
    message["From"]    = QQ_EMAIL
    message["To"]      = "379473407@qq.com"
    message["Subject"] = Header(subject, "utf-8")

    try:
        smtp_obj = smtplib.SMTP_SSL("smtp.qq.com", 465)
        smtp_obj.login(QQ_EMAIL, QQ_AUTH_CODE)
        smtp_obj.sendmail(QQ_EMAIL, ["379473407@qq.com"], message.as_string())
        print(f"  ✅ 邮件已发送：{subject}")
    except smtplib.SMTPException as e:
        print(f"  ❌ 邮件发送失败：{e}")
    finally:
        smtp_obj.quit()


# ── 主流程 ────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*50}\n  {now}\n{'='*50}")

    for list_type, label in [
        ("market_borrow_list", "借入"),
    ]:
        print(f"\n[{label}] 抓取中...")
        orders = fetch_first_page(list_type)
        print(f"  共 {len(orders)} 条")

        for order in orders:
            oid = order.get("orderid")

            # 跳过已售罄的挂单（按需注释掉这行）
            if order.get("is_sell_out") == 0:
                continue

            print(f"  发送邮件：#{oid}...")
            body = format_order_email(order)
            send_email(
                subject=f"【Gate C2C {label}】 #{oid} ¥{order['initial_amount']:,.0f} 日息{order['rate']*365}%",
                body=body,
            )
            break

    print("\n本次运行完成")


if __name__ == "__main__":
    main()