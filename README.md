# Eco Monitoring FastAPI Service

FastAPI сервис с:
- регистрацией пользователя по email (пароль генерируется и отправляется на email),
- авторизацией по email+паролю,
- вечным JWT bearer-токеном (без `exp`),
- endpoint для получения уникальных `serial` из `plc_state`.

## Подготовка

```powershell
cd eco_monitoring_fastapi_service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Заполните `.env`:
- `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM` (обычно `HS256`)
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_USE_TLS`

## Запуск

```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Swagger:
- `http://127.0.0.1:8000/docs`

## API

1. Регистрация:

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com"
}
```

2. Логин:

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "пароль_из_email"
}
```

Ответ:

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

3. Получение устройств:

```http
GET /api/v1/monitoring_posts
```

Endpoint публичный, авторизация не требуется.
