# Eco Monitoring FastAPI Service

FastAPI-сервис для:
- регистрации пользователя по email;
- авторизации по email и паролю;
- выдачи JWT bearer-токена;
- получения постов мониторинга, доступных устройств и часовых рядов датчиков.

## Подготовка

```powershell
cd eco_monitoring_fastapi_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Заполните `.env`:

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

## Запуск

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

## API

### Регистрация

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com"
}
```

### Логин

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password_from_email"
}
```

Ответ:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### Посты мониторинга

```http
GET /api/v1/monitoring_posts
```

### Доступные устройства поста

```http
GET /api/v1/device_state/available?monitoring_post_id=<id>
```

В ответ попадают только устройства, у которых в истории есть хотя бы одно состояние с `ping != 'BAD'` или `ping IS NULL`.

### Часовые данные газа

```http
GET /api/v1/gas_sensors/hourly?monitoring_post_id=<id>&date=YYYY-MM-DD
```

### Последнее состояние газового устройства

```http
GET /api/v1/gas_state/latest?monitoring_post_id=<id>
```

### Часовые данные пыли

```http
GET /api/v1/dust_state/hourly?monitoring_post_id=<id>&date=YYYY-MM-DD
```

### Часовые данные метео

```http
GET /api/v1/meteo_state/hourly?monitoring_post_id=<id>&date=YYYY-MM-DD
```

### Часовые данные ИВТМ

```http
GET /api/v1/ivtm_state/hourly?monitoring_post_id=<id>&date=YYYY-MM-DD
```

Публичные endpoint-ы авторизацию не требуют.
