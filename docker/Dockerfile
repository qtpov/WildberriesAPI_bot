# Используем официальный Python образ
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости системы и Python-пакеты в одном слое, чтобы сократить количество слоев
RUN apt-get update && apt-get install -y \
    gcc libpq-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


# Копируем весь проект в контейнер
COPY . .

# Открываем порт для FastAPI
EXPOSE 8000

# Устанавливаем переменную окружения для корректной работы Python
ENV PYTHONUNBUFFERED=1

# Команда для запуска FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
