# API Examples - Summary и Test

## Course API

### Создание курса (Methodist only)

Методист может создать курс двумя способами:

#### Вариант 1: С текстом
```bash
POST /api/v1/courses
Authorization: Bearer <methodist_token>
Content-Type: application/json

{
  "title": "Уголовный кодекс РК",
  "description": "Основы уголовного права",
  "original_text": "Полный текст курса..."
}
```

#### Вариант 2: С файлом (URL из Supabase)
```bash
POST /api/v1/courses
Authorization: Bearer <methodist_token>
Content-Type: application/json

{
  "title": "Уголовный кодекс РК",
  "description": "Основы уголовного права",
  "file_url": "https://your-supabase-url.com/storage/v1/object/public/files/course.pdf"
}
```

**Важно:**
- Хотя бы одно из полей (`original_text` или `file_url`) должно быть заполнено
- Можно заполнить оба поля одновременно
- Если не заполнено ни одно поле, вернется ошибка 422

### Удаление курса (Methodist only)
```bash
DELETE /api/v1/courses/1
Authorization: Bearer <methodist_token>
```

**Важно:** Удалить курс может только его создатель

---

## Summary API

### 1. Создать summary (Methodist only)
```bash
POST /api/v1/summaries
Authorization: Bearer <methodist_token>
Content-Type: application/json

{
  "course_id": 1,
  "content": "Это краткое содержание курса..."
}
```

### 2. Получить summary для курса
```bash
GET /api/v1/summaries/course/1
Authorization: Bearer <token>
```

### 3. Обновить summary (Methodist only)
```bash
PATCH /api/v1/summaries/1
Authorization: Bearer <methodist_token>
Content-Type: application/json

{
  "content": "Обновленное содержание..."
}
```

### 4. Удалить summary (Methodist only)
```bash
DELETE /api/v1/summaries/1
Authorization: Bearer <methodist_token>
```

---

## Test API

### ВАЖНО: Формат правильных ответов
В поле `correct_answer` записывается **ПОЛНЫЙ ТЕКСТ** правильного ответа, а не буква!

### 1. Создать тест (Methodist only)
```bash
POST /api/v1/tests/create
Authorization: Bearer <methodist_token>
Content-Type: application/json

{
  "course_id": 1,
  "questions": [
    {
      "question": "Какое количество преступлений было зарегистрировано на территории Алматинской области за октябрь 2025 года?",
      "options": [
        "847",
        "900",
        "750",
        "800"
      ],
      "correct_answer": "847"
    },
    {
      "question": "В каком году был принят УК РК?",
      "options": [
        "2014 год",
        "2015 год",
        "2016 год",
        "2017 год"
      ],
      "correct_answer": "2014 год"
    }
  ]
}
```

### 2. Получить тест для курса (студент, без правильных ответов)
```bash
GET /api/v1/tests/course/1
Authorization: Bearer <student_token>
```

**Ответ:**
```json
{
  "id": 1,
  "course_id": 1,
  "questions": [
    {
      "id": 0,
      "question": "Какое количество преступлений было зарегистрировано на территории Алматинской области за октябрь 2025 года?",
      "options": [
        "847",
        "900",
        "750",
        "800"
      ]
    }
  ],
  "created_at": "2025-11-15T10:30:00Z"
}
```

### 2.1. Получить тест по ID (студент, без правильных ответов)
```bash
GET /api/v1/tests/1
Authorization: Bearer <student_token>
```

### 3. Получить тест с правильными ответами (Methodist only)
```bash
GET /api/v1/tests/1/full
Authorization: Bearer <methodist_token>
```

### 4. Отправить ответы студента
```bash
POST /api/v1/tests/1/submit
Authorization: Bearer <student_token>
Content-Type: application/json

{
  "answers": [
    {
      "question_id": 0,
      "selected_answer": "847"
    },
    {
      "question_id": 1,
      "selected_answer": "2014 год"
    }
  ]
}
```

**Ответ:**
```json
{
  "score": 2,
  "total": 2,
  "passed": true,
  "percentage": 100.0
}
```

**Важно:** После отправки теста, результаты сохраняются с флагом `is_correct` для каждого ответа, чтобы студент мог позже посмотреть, какие ответы были правильными.

### 5. Обновить тест (Methodist only)
```bash
PATCH /api/v1/tests/1
Authorization: Bearer <methodist_token>
Content-Type: application/json

{
  "questions": [
    {
      "question": "Обновленный вопрос?",
      "options": [
        "Вариант 1",
        "Вариант 2",
        "Вариант 3",
        "Вариант 4"
      ],
      "correct_answer": "Вариант 1"
    }
  ]
}
```

### 6. Удалить тест (Methodist only)
```bash
DELETE /api/v1/tests/1
Authorization: Bearer <methodist_token>
```

### 7. Генерация теста с помощью AI (Methodist only)
```bash
POST /api/v1/ai/generate-test
Authorization: Bearer <methodist_token>
Content-Type: application/json

{
  "course_id": 1
}
```

---

## Results API

### 1. Получить все свои результаты (студент) - с полной информацией
```bash
GET /api/v1/results/my
Authorization: Bearer <student_token>
```

**Ответ:** (включает полную информацию о тесте и студенте)
```json
[
  {
    "id": 1,
    "test_id": 1,
    "student_id": 5,
    "answers": [
      {
        "question_id": 0,
        "selected_answer": "847",
        "is_correct": true
      },
      {
        "question_id": 1,
        "selected_answer": "2014 год",
        "is_correct": true
      }
    ],
    "score": 2,
    "total_questions": 2,
    "submitted_at": "2025-11-16T10:30:00Z",
    "test": {
      "id": 1,
      "course_id": 1,
      "created_at": "2025-11-15T10:00:00Z"
    },
    "student": {
      "id": 5,
      "email": "student@example.com",
      "full_name": "Иван Иванов",
      "role": "student"
    }
  }
]
```

### 2. Получить результаты по курсу (студент) - с полной детализацией
```bash
GET /api/v1/results/my/course/1
Authorization: Bearer <student_token>
```

**Ответ:** (включает полную информацию о вопросах, вариантах ответов и правильных ответах)
```json
[
  {
    "id": 1,
    "test_id": 1,
    "student_id": 5,
    "answers": [
      {
        "question_id": 0,
        "question": "Какое количество преступлений было зарегистрировано на территории Алматинской области за октябрь 2025 года?",
        "options": [
          "847",
          "900",
          "750",
          "800"
        ],
        "selected_answer": "847",
        "correct_answer": "847",
        "is_correct": true
      },
      {
        "question_id": 1,
        "question": "В каком году был принят УК РК?",
        "options": [
          "2014 год",
          "2015 год",
          "2016 год",
          "2017 год"
        ],
        "selected_answer": "2015 год",
        "correct_answer": "2014 год",
        "is_correct": false
      }
    ],
    "score": 1,
    "total_questions": 2,
    "submitted_at": "2025-11-16T11:45:00Z",
    "percentage": 50.0,
    "passed": false
  }
]
```

**Примечание:**
- Если студент повторно сдает тест, результат перезаписывается (обновляется существующая запись), а время `submitted_at` обновляется на текущее
- Ответ включает полную детализацию для показа на фронтенде: текст вопроса, все варианты, выбранный ответ, правильный ответ, флаг правильности

### 3. Получить все результаты (методист)
```bash
# Все результаты
GET /api/v1/results
Authorization: Bearer <methodist_token>

# Результаты только для конкретного курса
GET /api/v1/results?course_id=1
Authorization: Bearer <methodist_token>

# С пагинацией
GET /api/v1/results?skip=0&limit=20&course_id=1
Authorization: Bearer <methodist_token>
```

**Ответ:** (включает полную информацию о тесте и студенте)
```json
[
  {
    "id": 1,
    "test_id": 1,
    "student_id": 5,
    "answers": [
      {
        "question_id": 0,
        "selected_answer": "847",
        "is_correct": true
      }
    ],
    "score": 2,
    "total_questions": 2,
    "submitted_at": "2025-11-16T10:30:00Z",
    "test": {
      "id": 1,
      "course_id": 1,
      "created_at": "2025-11-15T10:00:00Z"
    },
    "student": {
      "id": 5,
      "email": "student@example.com",
      "full_name": "Иван Иванов",
      "role": "student"
    }
  }
]
```

### 4. Экспорт результатов в CSV (методист)
```bash
# Экспорт всех результатов (по умолчанию с разделителем ";")
GET /api/v1/results/export
Authorization: Bearer <methodist_token>

# Экспорт результатов только для конкретного курса
GET /api/v1/results/export?course_id=1
Authorization: Bearer <methodist_token>

# Экспорт с запятой как разделителем (для US локали)
GET /api/v1/results/export?delimiter=,
Authorization: Bearer <methodist_token>
```

**Ответ:** CSV файл с результатами тестов

**Примечание о разделителе:**
- По умолчанию используется точка с запятой (`;`) как разделитель - это стандарт для Excel в странах СНГ и Европе
- Если ваш Excel не распознает колонки правильно, попробуйте параметр `delimiter=,`
- Файл всегда сохраняется в кодировке UTF-8 с BOM для корректного отображения русских символов

---

## Важные замечания

1. **Формат правильных ответов**: `correct_answer` должен содержать ПОЛНЫЙ ТЕКСТ правильного ответа (например, "847"), а не букву (не "A")

2. **Отправка ответов студентом**: В `selected_answer` студент отправляет ПОЛНЫЙ ТЕКСТ выбранного ответа

3. **Валидация**: При создании/обновлении теста система проверяет, что `correct_answer` находится в списке `options`

4. **Права доступа**:
   - Студенты видят тесты БЕЗ правильных ответов
   - Методисты видят тесты С правильными ответами
   - Только создатель курса может редактировать/удалять его тесты и summaries
