FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN useradd --system --uid 1001 appuser && chown -R appuser /app
USER appuser
EXPOSE 8000
CMD ["gunicorn", "-b", "0.0.0.0:8000", "-w", "2", "config.wsgi:application"]
