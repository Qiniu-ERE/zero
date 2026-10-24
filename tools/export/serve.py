#!/usr/bin/env python3
"""在电脑上试玩网页版：python3 play-local.py，然后浏览器打开 http://localhost:8080/
（直接双击 index.html 打不开：浏览器不允许 file:// 页面加载 wasm 和 game.zip）"""
import functools
import http.server
import os
import webbrowser

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TankBattle")
PORT = 8080


class Handler(http.server.SimpleHTTPRequestHandler):
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".wasm": "application/wasm", ".webmanifest": "application/manifest+json", ".js": "text/javascript"}


if __name__ == "__main__":
    url = f"http://localhost:{PORT}/"
    print(f"坦克大战 2026：{url}（按 Ctrl+C 结束）")
    webbrowser.open(url)
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Handler, directory=ROOT)).serve_forever()
