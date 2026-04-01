#!/usr/bin/env python3

import os
import sys
import time
import json

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from get_gate_c2c_data import _load_cache, _save_cache, _text_hash, MIN_RESEND_SECONDS

# 测试缓存功能
print("测试缓存功能...")

# 缓存文件路径
cache_file = os.path.join(os.path.dirname(__file__), 'src', 'send_cache.json')

# 1. 确保缓存文件不存在
print("1. 确保缓存文件不存在")
if os.path.exists(cache_file):
    os.remove(cache_file)
    print("   已删除缓存文件")
else:
    print("   缓存文件不存在")

# 2. 导入并使用模块中的 _send_cache
print("2. 导入并使用模块中的 _send_cache")
import get_gate_c2c_data
print(f"   初始缓存内容: {get_gate_c2c_data._send_cache}")

# 3. 模拟发送一条消息
print("3. 模拟发送一条消息")
text = "测试消息 1"
key = _text_hash(text)
now = time.time()
get_gate_c2c_data._send_cache[key] = now
print(f"   发送时间: {now}")
print(f"   缓存内容: {get_gate_c2c_data._send_cache}")

# 4. 保存缓存
print("4. 保存缓存")
_save_cache()

# 5. 检查缓存文件是否存在
print(f"5. 检查缓存文件: {os.path.exists(cache_file)}")
if os.path.exists(cache_file):
    with open(cache_file, 'r', encoding='utf-8') as f:
        cached_data = json.load(f)
    print(f"   缓存文件内容: {cached_data}")

# 6. 模拟脚本重新运行，加载缓存
print("6. 模拟脚本重新运行，加载缓存")
# 重新导入模块
import importlib
importlib.reload(get_gate_c2c_data)
print(f"   重新导入后缓存内容: {get_gate_c2c_data._send_cache}")

# 7. 加载缓存
print("7. 加载缓存")
get_gate_c2c_data._load_cache()
print(f"   加载后缓存内容: {get_gate_c2c_data._send_cache}")

# 8. 检查是否在重发间隔内
print("8. 检查是否在重发间隔内")
last_sent = get_gate_c2c_data._send_cache.get(key)
if last_sent is not None:
    elapsed = time.time() - last_sent
    if elapsed < MIN_RESEND_SECONDS:
        remaining = int((MIN_RESEND_SECONDS - elapsed) / 60)
        print(f"   相同内容 {MIN_RESEND_SECONDS // 3600} 小时内已发过，还需等待 {remaining} 分钟")
    else:
        print("   可以重新发送")

print("\n测试完成")