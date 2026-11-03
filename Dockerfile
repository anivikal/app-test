FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app
COPY app.py .
COPY static ./static

RUN useradd --system --uid 10001 app
USER app

EXPOSE 8000
CMD ["python", "app.py"]
