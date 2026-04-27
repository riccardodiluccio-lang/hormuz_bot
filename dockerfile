FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir requests python-telegram-bot apscheduler

COPY main.py .

CMD ["python", "main.py"]
