# Используем официальный Python образ
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app
# Копируем все файлы проекта в контейнер
COPY . /app
# Устанавливаем зависимости системы
RUN apt-get update && apt-get install -y \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей и устанавливаем Python-пакеты
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Открываем порт для FastAPI
EXPOSE 8000

# Команда для запуска FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
