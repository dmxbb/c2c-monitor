# c2c-monitor

监控挂单信息，符合条件时通过飞书机器人发送通知。

## 功能

- 定时抓取 C2C 借贷挂单数据
- 过滤已售罄挂单，只推送可借的挂单
- 通过飞书机器人发送详细挂单通知，包含利率、期限、抵押信息等

## 触发方式

- **定时触发**：每 1 分钟自动运行一次
- **手动触发**：在 GitHub Actions 页面点击 `Run workflow`
- **API 触发**：

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  https://api.github.com/repos/dmxbb/c2c-monitor/actions/workflows/monitor.yml/dispatches \
  -d '{"ref":"main"}'
```

## 环境变量配置

在 GitHub 仓库 `Settings → Secrets and variables → Actions` 中添加以下 Secrets：

| Secret | 说明 |
|--------|------|
| `FEISHU_WEBHOOK` | 飞书机器人 Webhook 地址 |
| `FEISHU_SECRET` | 飞书机器人签名密钥 |
| `QQ_EMAIL` | QQ 邮箱（暂未使用，预留） |
| `QQ_AUTH_CODE` | QQ 邮箱授权码（暂未使用，预留） |

## 本地运行

```bash
# 创建并激活虚拟环境
conda create -n c2c-monitor python=3.10
conda activate c2c-monitor

# 安装依赖
pip install requests

# 配置环境变量
export FEISHU_WEBHOOK="your_webhook_url"
export FEISHU_SECRET="your_secret"

# 运行脚本
python get_gate_c2c_data.py
```

## 通知示例

```
【C2C 法币借贷挂单通知】

挂单类型：借入
──────────────────────────────
用户信息
  昵称：xxx
  等级：V3
  最后上线：5 分钟前

借贷条件
  挂单金额：¥100,000
  可借范围：¥1,000 ~ ¥100,000
  日息：0.05%
  年化利率：18.25%
  期限：30 天
  预计总利息：¥1,500.00
  续借：支持
  状态：可借
──────────────────────────────
```
