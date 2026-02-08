# Production Deployment

## Environment configuration

- **ENVIRONMENT**: Set to `production` for production and `development` for local/dev.
- **DEBUG**: Set to `false` in production (disables `/docs`, `/redoc`, and verbose errors).
- **Database**: With `ENVIRONMENT=production` the app uses **MySQL**; with `ENVIRONMENT=development` it uses **PostgreSQL**.

## Production checklist

1. **Copy and configure .env**
   - Copy `.env.example` to `.env`.
   - Set `ENVIRONMENT=production` and `DEBUG=false`.

2. **Database (MySQL)**
   - Set `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_SERVER`, `MYSQL_PORT` (default 3306), `MYSQL_DB`.
   - Create the database and run migrations: `alembic upgrade head`.
   - Install driver: `aiomysql` is in `requirements.txt`.

3. **Security**
   - Set a strong `SECRET_KEY` (random, long string).
   - Set `COOKIE_SECURE=true` when using HTTPS.
   - Set `CORS_ORIGINS` to your frontend URL(s) only (comma-separated), e.g. `https://yourdomain.com`.

4. **URLs**
   - Set `FRONTEND_URL` and `API_URL` to your production URLs (used in emails and links).
   - Set `API_URL` to the public base URL of this API (e.g. `https://api.yourdomain.com`).

5. **Optional**
   - `LOG_LEVEL`: e.g. `INFO` or `WARNING` in production.
   - Use a process manager (e.g. Gunicorn with uvicorn workers) and reverse proxy (e.g. Nginx) in front of the app.

## Development (default)

- Set `ENVIRONMENT=development` (or leave unset).
- Set `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_SERVER`, `POSTGRES_DB` (and optionally `POSTGRES_PORT`).
- `DEBUG=true` is typical for local development.
