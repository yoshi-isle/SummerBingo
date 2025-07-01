# Dockerfile for discord_bot
FROM python:3.11

WORKDIR /app


COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "bot.py"]
