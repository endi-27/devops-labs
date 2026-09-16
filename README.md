# DevOps Platform — Modular Monolith Backend

Цей проєкт розроблений для лабораторних робіт та практичних завдань з курсу **DevOps**.
Він побудований за принципом **Modular Monolith (Package by Feature / Vertical Slicing)**, що забезпечує чітку ізоляцію доменів та можливість швидкого перетворення на мікросервіси на подальших етапах.

---

## 🛠 Технологічний стек

- **Мова програмування:** Python 3.12+
- **Менеджер пакетів та віртуального середовища:** [uv](https://github.com/astral-sh/uv)
- **Веб-фреймворк:** [FastAPI](https://fastapi.tiangolo.com/) + Pydantic v2
- **ORM / База даних:** [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (Asyncio) + PostgreSQL 16 (`asyncpg`)
- **Міграції:** [Alembic](https://alembic.sqlalchemy.org/) (Async)
- **Кеш / Брокер:** Redis 7
- **Логування:** [Loguru](https://github.com/Delgan/loguru) зі структурованим перехопленням системних логів
- **Лінтери та типізація:** Ruff, Mypy
- **Тестування:** Pytest (Unit, Integration, API/E2E з підтримкою асинхронності)
- **Контейнеризація:** Docker (Multi-stage build на базі `uv`) + Docker Compose

---

## 📂 Структура проєкту

```text
.
├── .vscode/
│   └── settings.json             # Налаштування Ruff, Mypy, Pylance, Pytest
├── backend/
│   ├── pyproject.toml            # Маніфест залежностей uv та конфігурація інструментів
│   ├── Dockerfile                # Multi-stage Dockerfile (builder, test, runtime)
│   ├── alembic.ini               # Конфіг міграцій Alembic
│   ├── alembic/                  # Міграції бази даних
│   │   ├── env.py
│   │   └── versions/
│   ├── src/
│   │   ├── main.py               # Фабрика FastAPI додатку, middleware, healthcheck
│   │   ├── core/                 # Спільна інфраструктура (Config, DB, Logger, Exceptions)
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   ├── base_model.py
│   │   │   ├── logger.py
│   │   │   └── exceptions.py
│   │   └── modules/              # Ізольовані доменні модулі
│   │       ├── users/            # Модуль користувачів (CRUD)
│   │       ├── products/         # Модуль товарів (CRUD)
│   │       └── orders/           # Модуль замовлень (CRUD)
│   ├── scripts/                  # Службові скрипти (seed_initial_data.py)
│   └── tests/                    # Набір тестів
│       ├── conftest.py           # Фікстури (AsyncClient, in-memory test DB)
│       ├── unit/                 # Unit-тести сервісів
│       ├── integration/          # Integration-тести репозиторіїв
│       └── api/                  # E2E API-тести ендпоінтів
├── scripts/                      # Скрипти бекапу (pg_backup_rotated.sh)
├── docker-compose.yml            # Оркестрація контейнерів (postgres, redis, migrator, backend, db_backup)
├── .env.example                  # Шаблон змінних середовища
├── .env                          # Локальний файл змінних середовища
├── .gitignore
└── README.md
```

---

## 🚀 Швидкий старт (Локальна розробка через uv)

### 1. Встановлення залежностей
```bash
cd backend
uv sync
```

### 2. Запуск перевірки коду та типів
```bash
# Лінтинг та перевірка стилю коду
uv run ruff check .
uv run ruff format --check .

# Статична перевірка типів
uv run mypy .
```

### 3. Запуск усіх тестів
```bash
uv run pytest -v --cov=src
```

### 4. Запуск локального сервера
```bash
uv run uvicorn src.main:app --reload --port 8000
```
- Swagger UI документація: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/api/v1/health`
- Readiness check: `http://localhost:8000/api/v1/ready`

---

## 🐳 Запуск через Docker Compose

```bash
# Запуск усієї інфраструктури у фоновому режимі
docker compose up -d --build

# Перегляд логів бекенду
docker compose logs -f backend

# Зупинка сервісів
docker compose down
```
