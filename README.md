# PostTrack — Backend

## Запуск

```bash
# 1. Встановити залежності
pip install -r requirements.txt

# 2. Копіювати .env
cp .env.example .env

# 3. Міграції
python manage.py migrate

# 4. Тестові дані
python manage.py seed_data

# 5. Запуск (Daphne — підтримує WebSocket)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Або для розробки без Redis (чат не працює):
python manage.py runserver
```

## Redis (для чату)
```bash
# Docker
docker run -d -p 6379:6379 redis:alpine

# або локально
redis-server
```

## Тестові акаунти (пароль: adminadmin)
| Логін       | Роль                |
|-------------|---------------------|
| admin       | Адміністратор       |
| PWorker1-10 | Працівник пошти     |
| SWorker1-10 | Працівник складу    |
| LWorker1-5  | Логіст              |
| DWorker1-10 | Водій               |
| HWorker1-3  | HR                  |
| CWorker1-10 | Клієнт              |

## API Endpoints

### Accounts
| Метод | URL | Опис |
|-------|-----|------|
| POST | /api/accounts/login/ | Вхід |
| POST | /api/accounts/token/refresh/ | Оновити токен |
| POST | /api/accounts/logout/ | Вихід |
| GET/PATCH | /api/accounts/me/ | Профіль |
| POST | /api/accounts/register/ | Реєстрація клієнта |
| GET/POST | /api/accounts/workers/ | HR: список/додати |
| GET/PATCH/DELETE | /api/accounts/workers/<id>/ | HR: деталі |

### Locations
| Метод | URL | Опис |
|-------|-----|------|
| GET | /api/locations/ | Всі локації (?type=post_office) |
| GET | /api/locations/<id>/ | Деталі локації |

### Shipments
| Метод | URL | Опис |
|-------|-----|------|
| GET | /api/shipments/ | Список посилок |
| POST | /api/shipments/ | Створити посилку |
| GET | /api/shipments/<id>/ | Деталі посилки |
| POST | /api/shipments/<id>/update_status/ | Змінити статус |
| POST | /api/shipments/<id>/cancel/ | Скасувати |
| POST | /api/shipments/<id>/confirm_delivery/ | Підтвердити доставку |
| POST | /api/shipments/<id>/confirm_payment/ | Підтвердити оплату |

### Tracking
| Метод | URL | Опис |
|-------|-----|------|
| GET | /api/tracking/public/<tracking_number>/ | Публічний трекінг |
| GET | /api/tracking/events/?shipment=<id> | Події посилки |

### Dispatch
| Метод | URL | Опис |
|-------|-----|------|
| GET/POST | /api/dispatch/groups/ | Список/створити групи |
| GET | /api/dispatch/groups/<id>/ | Деталі групи |
| POST | /api/dispatch/groups/<id>/add_shipment/ | Додати посилку |
| POST | /api/dispatch/groups/<id>/remove_shipment/ | Видалити посилку |
| POST | /api/dispatch/groups/<id>/mark_ready/ | Готово до відправки |
| POST | /api/dispatch/groups/<id>/depart/ | Водій забрав |
| POST | /api/dispatch/groups/<id>/arrive/ | Прибули |

### Logistics
| Метод | URL | Опис |
|-------|-----|------|
| GET/POST | /api/logistics/routes/ | Список/створити маршрути |
| GET | /api/logistics/routes/<id>/ | Деталі маршруту |
| POST | /api/logistics/routes/<id>/confirm/ | Підтвердити |
| POST | /api/logistics/routes/<id>/start/ | Почати виконання |
| POST | /api/logistics/routes/<id>/complete/ | Завершити |

### Chat
| Метод | URL | Опис |
|-------|-----|------|
| GET | /api/chat/rooms/ | Список кімнат |
| POST | /api/chat/rooms/create/ | Створити кімнату |
| GET | /api/chat/rooms/<id>/messages/ | Повідомлення |
| WS | ws://localhost:8000/ws/chat/<id>/?token=<jwt> | WebSocket |

### Reports (PDF)
| Метод | URL | Опис |
|-------|-----|------|
| GET | /api/reports/shipment/<id>/receipt/ | Квитанція |
| GET | /api/reports/shipment/<id>/delivery/ | Доставка |
| GET | /api/reports/shipment/<id>/payment/ | Оплата |
| GET | /api/reports/dispatch/<id>/depart/ | Передача групи |
| GET | /api/reports/dispatch/<id>/arrive/ | Прийом групи |
| GET | /api/reports/location/ | Звіт локації (?date_from=&date_to=) |
