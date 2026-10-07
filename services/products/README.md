# Products Microservice

Мікросервіс каталогу товарів та управління залишками на складі.

## Ендпоінти
- `GET /health` — перевірка працездатності
- `GET /ready` — перевірка з'єднання з БД
- `GET /api/v1/products` — список товарів
- `POST /api/v1/products` — створення товару
- `GET /api/v1/products/{id}` — отримання товару за ID
- `PUT /api/v1/products/{id}` — оновлення товару
- `DELETE /api/v1/products/{id}` — видалення товару
- `POST /api/v1/products/{id}/reserve` — резервування та списання залишку для замовлення
- `POST /api/v1/products/{id}/release` — повернення залишку на склад при скасуванні
