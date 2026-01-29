FROM python:3.11-slim

LABEL description="Plants vs Zombies Game Leaderboard Server"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000
ENV FLASK_DEBUG=false
ENV DATABASE_PATH=/app/data/game.db

WORKDIR /app

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

COPY server/requirements.txt ./server/
RUN pip install --no-cache-dir -r server/requirements.txt

COPY server/ ./server/
COPY start_server.py .

RUN mkdir -p /app/data && chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

CMD ["python", "start_server.py"]
