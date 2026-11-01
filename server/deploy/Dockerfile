# 排行榜服务的容器镜像（只用 Python 标准库，不装第三方包）
# 构建：docker build -t tankbattle-lb -f server/deploy/Dockerfile server
# 运行：docker run -d -p 8787:8787 -v lb-data:/data tankbattle-lb
# 用 docker compose 加上 HTTPS（Caddy）见 compose.yml 和 server/README.md 的“部署”一节
FROM python:3.12-slim
WORKDIR /app
COPY leaderboard.py .
RUN useradd --system --uid 10001 lb && mkdir /data && chown lb /data
USER lb
VOLUME /data
EXPOSE 8787
# 服务收到 SIGINT 会正常关闭（sqlite 写完再退出）；docker stop 默认发 SIGTERM，改成 SIGINT
STOPSIGNAL SIGINT
HEALTHCHECK --interval=30s --timeout=3s CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8787/v1/health', timeout=2)"
# --trust-proxy：前面有 Caddy 反向代理，按 X-Forwarded-For 限频。直接对公网开放端口时去掉它（否则客户端能伪造 IP）
CMD ["python3", "leaderboard.py", "--host", "0.0.0.0", "--port", "8787", "--db", "/data/lb.sqlite", "--trust-proxy"]
