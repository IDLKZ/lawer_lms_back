# LMS для правоохранительной академии

MVP системы обучения (LMS) с автоматической генерацией конспектов и тестов с использованием OpenAI API.

## Особенности

- 🔐 Аутентификация с JWT токенами
- 👥 Две роли пользователей: методист и студент
- 📝 Загрузка учебных материалов (текст, DOCX, PDF)
- 🤖 Автоматическая генерация конспектов через OpenAI
- ✅ Автоматическая генерация тестов (5 вопросов с вариантами ответа)
- 🎓 Система прохождения тестов для студентов
- 📊 Отслеживание результатов и экспорт в CSV

## Технологический стек

- **Backend**: FastAPI
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **AI**: OpenAI API (GPT-3.5-turbo)
- **Authentication**: JWT tokens (python-jose)
- **Password hashing**: bcrypt (passlib)

## Установка и настройка

### 1. Клонирование репозитория

```bash
cd backend
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

Скопируйте файл `.env.example` в `.env` и заполните необходимые значения:

```bash
cp .env.example .env
```

Пример `.env`:
```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres
OPENAI_API_KEY=your_openai_api_key
SECRET_KEY=your_secret_key_for_jwt
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 5. Создание миграций базы данных

```bash
# Создать первую миграцию
alembic revision --autogenerate -m "Initial migration"

# Применить миграции
alembic upgrade head
```

### 6. Запуск сервера

```bash
# Режим разработки (с автоперезагрузкой)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Или через Python
python -m app.main
```

Сервер будет доступен по адресу: http://localhost:8000

API документация (Swagger UI): http://localhost:8000/docs

## Структура проекта

```
backend/
├── alembic/                # Миграции базы данных
│   ├── versions/          # Файлы миграций
│   ├── env.py            # Конфигурация Alembic
│   └── script.py.mako    # Шаблон миграций
├── app/
│   ├── api/              # API endpoints
│   │   ├── auth.py       # Аутентификация
│   │   ├── courses.py    # Управление курсами
│   │   ├── ai.py         # AI генерация
│   │   ├── tests.py      # Тесты для студентов
│   │   └── results.py    # Результаты тестов
│   ├── core/             # Основные модули
│   │   ├── config.py     # Настройки приложения
│   │   └── database.py   # Подключение к БД
│   ├── crud/             # CRUD операции
│   ├── models/           # SQLAlchemy модели
│   ├── schemas/          # Pydantic схемы
│   ├── services/         # Бизнес-логика
│   │   ├── auth_service.py  # JWT утилиты
│   │   └── llm_service.py   # OpenAI интеграция
│   └── main.py           # FastAPI приложение
├── .env                  # Переменные окружения
├── requirements.txt      # Зависимости
└── README.md            # Документация
```

## API Endpoints

### Аутентификация

#### Регистрация пользователя
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "methodist@example.com",
  "password": "securepassword",
  "full_name": "Иван Иванов",
  "role": "methodist"  # или "student"
}
```

#### Вход в систему
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "methodist@example.com",
  "password": "securepassword"
}

# Ответ:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Получить информацию о текущем пользователе
```bash
GET /api/auth/me
Authorization: Bearer {access_token}
```

### Курсы (только для методистов)

#### Создать курс
```bash
POST /api/courses
Authorization: Bearer {methodist_token}
Content-Type: application/json

{
  "title": "Основы уголовного права",
  "description": "Вводный курс по уголовному праву",
  "original_text": "Текст лекции или протокола..."
}
```

#### Получить список курсов
```bash
GET /api/courses
Authorization: Bearer {token}

# Методист видит все курсы
# Студент видит только опубликованные
```

#### Получить курс по ID
```bash
GET /api/courses/{course_id}
Authorization: Bearer {token}
```

#### Обновить курс
```bash
PATCH /api/courses/{course_id}
Authorization: Bearer {methodist_token}
Content-Type: application/json

{
  "title": "Обновленное название",
  "description": "Новое описание"
}
```

#### Опубликовать курс
```bash
PATCH /api/courses/{course_id}/publish
Authorization: Bearer {methodist_token}
```

### AI Генерация (только для методистов)

#### Сгенерировать конспект
```bash
POST /api/ai/generate-summary
Authorization: Bearer {methodist_token}
Content-Type: application/json

{
  "course_id": 1
}

# Ответ:
{
  "id": 1,
  "course_id": 1,
  "content": "Краткий конспект лекции...",
  "created_at": "2024-01-15T10:30:00"
}
```

#### Сгенерировать тест
```bash
POST /api/ai/generate-test
Authorization: Bearer {methodist_token}
Content-Type: application/json

{
  "course_id": 1
}

# Ответ:
{
  "id": 1,
  "course_id": 1,
  "questions": [
    {
      "question": "Что такое уголовное право?",
      "options": ["Вариант A", "Вариант B", "Вариант C", "Вариант D"],
      "correct_answer": "A"
    }
  ],
  "created_at": "2024-01-15T10:35:00"
}
```

### Тесты (только для студентов)

#### Получить список доступных тестов
```bash
GET /api/tests
Authorization: Bearer {student_token}

# Возвращает тесты БЕЗ правильных ответов
```

#### Получить вопросы теста
```bash
GET /api/tests/{test_id}
Authorization: Bearer {student_token}

# Ответ (БЕЗ правильных ответов):
{
  "id": 1,
  "course_id": 1,
  "questions": [
    {
      "id": 0,
      "question": "Что такое уголовное право?",
      "options": ["Вариант A", "Вариант B", "Вариант C", "Вариант D"]
    }
  ],
  "created_at": "2024-01-15T10:35:00"
}
```

#### Сдать тест
```bash
POST /api/tests/{test_id}/submit
Authorization: Bearer {student_token}
Content-Type: application/json

{
  "answers": [
    {
      "question_id": 0,
      "selected_answer": "A"
    },
    {
      "question_id": 1,
      "selected_answer": "B"
    }
  ]
}

# Ответ:
{
  "score": 4,
  "total": 5,
  "passed": true,
  "percentage": 80.0
}
```

### Результаты (только для методистов)

#### Получить все результаты
```bash
GET /api/results
Authorization: Bearer {methodist_token}
```

#### Экспортировать результаты в CSV
```bash
GET /api/results/export
Authorization: Bearer {methodist_token}

# Скачает файл test_results.csv
```

## Полный пример использования (тестирование API)

### 1. Регистрация методиста
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "methodist@academy.com",
    "password": "methodist123",
    "full_name": "Петр Методистов",
    "role": "methodist"
  }'
```

### 2. Вход методиста
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "methodist@academy.com",
    "password": "methodist123"
  }'

# Сохраните полученный access_token
```

### 3. Создание курса
```bash
curl -X POST http://localhost:8000/api/courses \
  -H "Authorization: Bearer {methodist_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Основы криминалистики",
    "description": "Вводный курс по криминалистике",
    "original_text": "Криминалистика - это наука о раскрытии преступлений. Она включает в себя методы сбора, анализа и использования доказательств..."
  }'
```

### 4. Генерация конспекта
```bash
curl -X POST http://localhost:8000/api/ai/generate-summary \
  -H "Authorization: Bearer {methodist_token}" \
  -H "Content-Type: application/json" \
  -d '{"course_id": 1}'
```

### 5. Генерация теста
```bash
curl -X POST http://localhost:8000/api/ai/generate-test \
  -H "Authorization: Bearer {methodist_token}" \
  -H "Content-Type: application/json" \
  -d '{"course_id": 1}'
```

### 6. Публикация курса
```bash
curl -X PATCH http://localhost:8000/api/courses/1/publish \
  -H "Authorization: Bearer {methodist_token}"
```

### 7. Регистрация студента
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@academy.com",
    "password": "student123",
    "full_name": "Анна Студентова",
    "role": "student"
  }'
```

### 8. Вход студента
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student@academy.com",
    "password": "student123"
  }'
```

### 9. Получение доступных тестов (студент)
```bash
curl -X GET http://localhost:8000/api/tests \
  -H "Authorization: Bearer {student_token}"
```

### 10. Сдача теста
```bash
curl -X POST http://localhost:8000/api/tests/1/submit \
  -H "Authorization: Bearer {student_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "answers": [
      {"question_id": 0, "selected_answer": "A"},
      {"question_id": 1, "selected_answer": "B"},
      {"question_id": 2, "selected_answer": "C"},
      {"question_id": 3, "selected_answer": "D"},
      {"question_id": 4, "selected_answer": "A"}
    ]
  }'
```

### 11. Просмотр результатов (методист)
```bash
curl -X GET http://localhost:8000/api/results \
  -H "Authorization: Bearer {methodist_token}"
```

## Безопасность

- ✅ Правильные ответы **НИКОГДА** не отправляются студентам
- ✅ Все вычисления баллов происходят на backend
- ✅ JWT токены для аутентификации
- ✅ Пароли хешируются с использованием bcrypt
- ✅ Role-based access control (RBAC)
- ✅ Валидация всех входных данных через Pydantic

## Критерии приёмки

- ✅ Alembic миграции применяются успешно
- ✅ Регистрация и логин работают (JWT токены)
- ✅ Методист может загрузить текст
- ✅ Генерация конспекта через OpenAI работает
- ✅ Генерация 5 вопросов теста работает
- ✅ Студент видит только published курсы
- ✅ Студент может пройти тест
- ✅ Подсчёт баллов на backend (правильные ответы не утекают)
- ✅ Результаты сохраняются в БД
- ✅ Методист видит таблицу результатов
- ✅ API документация доступна на /docs

## Разработка

### Создание новой миграции
```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Откат миграции
```bash
alembic downgrade -1  # Откатить на одну версию назад
```

### Просмотр истории миграций
```bash
alembic history
alembic current
```

## Устранение неполадок

### Проблема: "ModuleNotFoundError: No module named 'app'"
**Решение**: Убедитесь, что вы запускаете команды из директории `backend/`

### Проблема: "Could not connect to database"
**Решение**: Проверьте правильность DATABASE_URL в файле `.env`

### Проблема: "OpenAI API Error"
**Решение**: Проверьте корректность OPENAI_API_KEY и наличие средств на счёте

## Лицензия

Этот проект создан для образовательных целей.

## Поддержка

По вопросам и предложениям обращайтесь к команде разработки.
