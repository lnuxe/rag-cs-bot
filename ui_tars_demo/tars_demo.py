"""
UI-TARS 式浏览器客服自动化 - Playwright 最小 Demo
=================================================
功能：用浏览器自动化模拟"机器人客服"：
  1. 打开一个模拟的客服消息页面（demo_msg.html）
  2. 读取页面消息框中客户发来的消息
  3. 把消息发给 Dify 知识库客服 API（走 cs_web 代理，隐藏 Key）
  4. 把生成的回复自动填入并发送到消息框

这演示了"浏览器自动化 + Dify RAG 客服"的全链路，可作为
接入 TikTok Shop 店铺对话框自动回复的可行性原型。

用法：
  python3 tars_demo.py [--headful]
  --headful  有头模式（能看到浏览器操作过程），默认无头

依赖：playwright
  安装：pip install playwright && playwright install chromium
"""
import os
import sys
import json
import time
import argparse
import urllib.request

from playwright.sync_api import sync_playwright

# Dify 客服代理（cs_web 的 Flask 服务，把 /api/chat 转发到 Dify 并隐藏 Key）
CS_WEB_URL = os.environ.get("CS_WEB_URL", "http://localhost:8000")
# 模拟客服消息页（本地文件）
MSG_PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_msg.html")


def get_reply(query: str) -> str:
    """调用 cs_web 代理 → Dify 知识库，获取客服回复"""
    body = json.dumps({"query": query, "user": "tars-bot"}).encode("utf-8")
    req = urllib.request.Request(
        f"{CS_WEB_URL}/api/chat",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("answer", "")


def run(headful: bool):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headful)
        page = browser.new_page(viewport={"width": 900, "height": 700})

        # 1. 打开模拟客服消息页
        page.goto(f"file://{MSG_PAGE}")
        print("[1] 已打开模拟客服消息页")

        # 2. 读取客户最新消息（页面上的 .msg 消息框）
        customer_msg = page.locator("#customer-msg").inner_text().strip()
        print(f"[2] 读取到客户消息: 「{customer_msg}」")

        # 3. 调用 Dify 知识库客服获取回复
        print("[3] 正在调用 Dify 知识库客服...")
        reply = get_reply(customer_msg)
        print(f"[4] 客服生成回复: 「{reply[:80]}...」" if len(reply) > 80 else f"[4] 客服生成回复: 「{reply}」")

        # 4. 把回复填入输入框并发送
        page.locator("#reply-box").fill(reply)
        page.locator("#send-btn").click()
        print("[5] 回复已自动填入并发送")
        page.wait_for_timeout(500)

        # 5. 验证发送结果（看页面是否出现发送者消息）
        sent = page.locator(".sent-message").last.inner_text()
        print(f"[6] 页面已发送回复: 「{sent[:60]}...」" if len(sent) > 60 else f"[6] 页面已发送回复: 「{sent}」")

        browser.close()
        print("\n✅ Demo 全链路跑通：读取消息 → Dify 回复 → 回填发送")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headful", action="store_true", help="有头模式")
    args = parser.parse_args()
    run(headful=args.headful)