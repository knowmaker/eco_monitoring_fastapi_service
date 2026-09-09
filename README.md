# Eco Monitoring FastAPI Service

Backend-сервис информационной системы экологического мониторинга. Сервис предоставляет HTTP API для фронтенда: авторизацию пользователей, управление постами мониторинга, получение агрегированных показаний датчиков, просмотр последних данных станции и экспорт агрегатов в Excel.

Сервис не принимает MQTT-сообщения напрямую. Сырые пакеты и показания приборов сохраняются отдельным ingest-сервисом, а FastAPI-сервис читает уже подготовленные данные из PostgreSQL/TimescaleDB.

## Как Работает

Основной поток данных:

1. Посты мониторинга передают телеметрию во внешний контур сбора данных.
2. Ingest-сервис сохраняет сырые MQTT-пакеты и нормализованные показания приборов в БД.
3. TimescaleDB формирует hourly/daily агрегаты.
4. FastAPI-сервис читает данные из обычных таблиц и continuous aggregates.
5. Фронтенд обращается к API для карты, графиков, профиля пользователя, админских действий и экспорта.

Код сервиса разделён по слоям:

- `app/api` - HTTP-слой: роутеры, query-параметры, зависимости авторизации.
- `app/services` - прикладные сценарии: чтение агрегатов, экспорт, авторизация, работа с постами.
- `app/models` - SQLAlchemy-модели таблиц и представлений БД.
- `app/schemas` - Pydantic-схемы запросов и ответов API.
- `app/core` - настройки, безопасность, даты и общие утилиты.
- `app/db` - подключение к БД и создание SQLAlchemy-сессий.

## Требования

- Python.
- PostgreSQL/TimescaleDB с подготовленной схемой проекта.
- Доступ к SMTP-серверу, если нужна регистрация пользователей с отправкой пароля на email.

Зависимости Python указаны в `requirements.txt`.

## Настройка

Создайте виртуальное окружение и установите зависимости:

```powershell
cd eco_monitoring_fastapi_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Создайте `.env` в директории сервиса и заполните переменные окружения:

```text
DATABASE_URL=
JWT_SECRET=
JWT_ALGORITHM=HS256
SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=
```

В README не приводятся реальные адреса, логины, пароли, токены и другие секреты. Их нужно хранить только в локальном `.env` или в защищённом хранилище окружения.

## Запуск

Локальный запуск для разработки:

```powershell
cd eco_monitoring_fastapi_service
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Проверка состояния сервиса:

```http
GET /health
```

Документация OpenAPI доступна после запуска:

```text
http://127.0.0.1:8000/docs
```

## API

Базовый префикс API:

```text
/api/v1
```

Публичные методы чтения доступны без авторизации. Методы профиля, экспорта и администрирования требуют bearer-токен.

### Авторизация

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
GET /api/v1/auth/me
PATCH /api/v1/auth/me
```

Регистрация создаёт пользователя по email и отправляет пароль через SMTP. Логин возвращает JWT access token, который используется в заголовке `Authorization: Bearer <token>`.

### Посты Мониторинга

```http
GET /api/v1/monitoring-posts
GET /api/v1/monitoring-posts/admin
PATCH /api/v1/monitoring-posts/{monitoring_post_id}
```

Публичный метод возвращает подтверждённые посты мониторинга для карты и пользовательского интерфейса. Admin-методы позволяют получить полный список постов и обновить их карточки.

### Доступные Устройства

```http
GET /api/v1/device-state/available?monitoring_post_id=<id>
```

Возвращает типы устройств, по которым есть успешные состояния для выбранного поста мониторинга.

### Графики Показаний

```http
GET /api/v1/gas-sensors/hourly?monitoring_post_id=<id>&date=YYYY-MM-DD
GET /api/v1/gas-sensors/monthly?monitoring_post_id=<id>&month=YYYY-MM

GET /api/v1/dust-state/hourly?monitoring_post_id=<id>&date=YYYY-MM-DD
GET /api/v1/dust-state/monthly?monitoring_post_id=<id>&month=YYYY-MM

GET /api/v1/meteo-state/hourly?monitoring_post_id=<id>&date=YYYY-MM-DD
GET /api/v1/meteo-state/monthly?monitoring_post_id=<id>&month=YYYY-MM

GET /api/v1/ivtm-state/hourly?monitoring_post_id=<id>&date=YYYY-MM-DD
GET /api/v1/ivtm-state/monthly?monitoring_post_id=<id>&month=YYYY-MM

GET /api/v1/profile-state/hourly?monitoring_post_id=<id>&date=YYYY-MM-DD
GET /api/v1/profile-state/monthly?monitoring_post_id=<id>&month=YYYY-MM
```

Hourly-методы возвращают точки за выбранные сутки. Monthly-методы возвращают дневные значения за выбранный месяц. Если дата или месяц не переданы, используется текущая дата в таймзоне приложения.

### Последние Показания Станции

```http
GET /api/v1/station-readings/latest-hourly?monitoring_post_id=<id>
```

Возвращает последнюю доступную hourly-сводку по станции: газовые датчики, пыль, метео, ИВТМ и температурный профиль, если соответствующие данные есть в агрегатах.

### Сырые MQTT-Пакеты

```http
GET /api/v1/raw-mqtt-payload/admin?monitoring_post_id=<id>&date=YYYY-MM-DD&limit=100
```

Admin-метод для просмотра последних сырых MQTT-пакетов по выбранному посту мониторинга. Параметр `date` необязателен.

### Экспорт Агрегатов

```http
POST /api/v1/export/aggregates
```

Формирует XLSX-файл с hourly или daily агрегатами по выбранным постам и типам устройств. Метод требует авторизации.

## Проверка После Изменений

Быстрая проверка синтаксиса:

```powershell
cd eco_monitoring_fastapi_service
.\.venv\Scripts\python.exe -m compileall app
```

Проверка, что приложение импортируется и OpenAPI собирается:

```powershell
$env:DATABASE_URL="<database-url>"
$env:JWT_SECRET="<jwt-secret>"
.\.venv\Scripts\python.exe -c "from app.main import app; print(len(app.openapi()['paths']))"
```

Для проверки реальной работы endpoint-ов нужна доступная БД с актуальной схемой и данными.
