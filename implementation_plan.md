# План реализации: Архитектура атрибутов с нечёткой логикой (Fuzzy Logic Attribute Architecture)

## 1. Концепция
Переход от дискретных лейблов ("blonde") к нечётким распределениям вероятностей ("brown: 0.7, light_brown: 0.5"). Это позволяет находить семантически близкие результаты и учитывать сложные случаи (смешанные цвета, субъективные оценки).

### Основные отличия
| Было | Стало |
|------|-------|
| `hair_color = "brown"` | `hair_color = {brown: 0.7, light_brown: 0.5}` |
| `background = "outdoor"` | `background = {mountains: 0.8, water: 0.3, nature: 0.9}` |
| Exact match | Fuzzy similarity (с матрицами семантической близости) |
| Один negative = полный штраф | Градуированный штраф по степени совпадения (Lambda penalty) |

---

## 2. Модель данных

### Типы атрибутов
1.  **SINGLE** (Взаимоисключающие, но с вероятностями): Сумма значений ~1.0. Используется Distance Matrix.
    *   *Пример:* `hair_color`, `body_type`.
2.  **MULTI** (Независимые метки): Каждое значение [0.0 - 1.0]. Используется Jaccard-like similarity.
    *   *Пример:* `background_objects`, `lifestyle_signals`.
3.  **CONTINUOUS** (Числовые диапазоны, пока не используем в MVP, заменяем на SINGLE buckets).

### 20 Классов атрибутов (Dating Focused)

#### БАЗОВЫЕ ХАРАКТЕРИСТИКИ (5 классов, SINGLE)
| Класс | Варианты | Зачем |
|-------|----------|-------|
| `age_group` | 18-24, 25-30, 31-37, 38-45, 46+ | Основной фильтр |
| `ethnicity` | caucasian, asian, black, latino, middle_eastern | Частый preference |
| `height_impression` | short, below_avg, average, above_avg, tall | По пропорциям на фото |
| `body_type` | slim, fit, average, curvy, large | Ключевой preference |
| `gender_presentation` | feminine, androgynous, masculine | Фильтр |

#### ЛИЦО (6 классов, SINGLE)
| Класс | Варианты | Зачем |
|-------|----------|-------|
| `face_shape` | oval, round, square, heart, oblong | Типаж лица |
| `eye_color` | brown, blue, green, gray, hazel | Классический preference |
| `eye_shape` | round, almond, hooded, monolid, downturned | Типаж |
| `nose_type` | small, straight, aquiline, wide, button | Типаж |
| `lips_type` | thin, medium, full, very_full | Типаж |
| `jawline` | soft, defined, square, pointed, round | Маскулинность/феминность |

#### ВОЛОСЫ (3 класса, SINGLE)
| Класс | Варианты | Зачем |
|-------|----------|-------|
| `hair_color` | black, brown, blonde, red, gray | Топ preference |
| `hair_length` | bald, short, medium, long, very_long | Важно для многих |
| `hair_texture` | straight, wavy, curly, coily, shaved | Типаж |

#### ДОПОЛНИТЕЛЬНЫЕ ПРИЗНАКИ (4 класса, SINGLE)
| Класс | Варианты | Зачем |
|-------|----------|-------|
| `facial_hair` | none, stubble, short_beard, full_beard, mustache | Для М, важный preference |
| `skin_tone` | fair, light, medium, olive, dark | В рамках этничности |
| `glasses` | none, glasses, sunglasses | — |
| `tattoos_visible` | none, subtle, moderate, heavy | Lifestyle signal |

#### ОБЩЕЕ ВПЕЧАТЛЕНИЕ (2 класса, SINGLE)
| Класс | Варианты | Зачем |
|-------|----------|-------|
| `attractiveness_style` | cute, pretty, handsome, sexy, striking | Субъективный типаж |
| `vibe` | friendly, serious, mysterious, playful, intense | Первое впечатление |

---

## 3. Алгоритмы Fuzzy Matching

### Distance Matrices (для SINGLE)
Матрицы определяют семантическую близость между значениями.
*(Примеры матриц для implementation см. в `Phase 2`)*
*   **Линейные** (для age, height): Соседние значения ближе.
*   **Семантические** (для hair, ethnicity): На основе визуального сходства.

### Similarity Calculation

**1. Similarity для SINGLE атрибутов:**
```
similarity = Σ (query[i] × candidate[j] × distance_matrix[i,j])
```

**2. Similarity для MULTI атрибутов (Fuzzy Jaccard):**
```
intersection = Σ min(query[i], candidate[i])
union = Σ max(query[i], candidate[i])
similarity = intersection / union
```

**3. Итоговый скор (Query vs Candidate):**
```
positive_sim = weighted_sum(similarities по всем атрибутам)
negative_sim = weighted_sum(similarities с negative_profile)

score = positive_sim - (λ × negative_sim)
```
*где λ = 0.3-0.5 (настраиваемый штраф)*

---

## 4. План реализации (Roadmap)

### Фаза 1: Схема данных
**Задача:** Создать Pydantic модели и JSON схему.
*   [ ] Файл `mvp/schema/attributes.py`: Определение 20 Enum классов.
*   [ ] Файл `mvp/schema/models.py`: Структура `PhotoProfile` с confidence scores.

### Фаза 2: Матрицы расстояний (Distance Matrices)
**Задача:** Захардкодить матрицы близости для SINGLE атрибутов.
*   [ ] Файл `mvp/schema/distance_matrices.py`:
    *   Реализовать матрицы для `hair_color`, `body_type`, `ethnicity`, `face_shape`.
    *   Реализовать линейные матрицы для `age_group`, `height_impression`.
    *   Реализовать default identity матрицы для остальных.

### Фаза 3: VLM Аннотатор (OpenRouter + Qwen)
**Задача:** Настроить автоматическую разметку фото.
*   [ ] Файл `mvp/annotator/vlm_client.py`: Клиент к OpenRouter (Qwen-2.5-VL или аналог).
*   [ ] Файл `mvp/annotator/prompts.py`: Системный промпт с четким JSON output правилом.
*   [ ] Тест: Прогнать 1-5 фото, проверить качество JSON и заполнение полей.

### Фаза 4: Поисковый движок (Matching Engine)
**Задача:** Реализовать логику построения профиля и поиска.
*   [ ] Файл `mvp/search/profile_builder.py`: Агрегация 5-10 фото в один `QueryProfile` (weighted average).
*   [ ] Файл `mvp/search/similarity.py`: Реализация формул Fuzzy Similarity и Fuzzy Jaccard.
*   [ ] Файл `mvp/search/ranker.py`: Подсчет итогового скора с учетом весов категорий (`high_priority`, `medium_priority`).

### Фаза 5: База данных и Batch Processing
**Задача:** Разметить датасет.
*   [ ] Файл `mvp/storage/database.py`: Simple JSON storage (чтение/запись списка фото).
*   [ ] Скрипт `mvp/process_batch.py`: Проход по папке с изображениями -> аннотация -> сохранение в JSON.

### Фаза 6: Gradio UI Demo
**Задача:** Интерфейс для проверки гипотезы.
*   [ ] Вкладка "Search":
    *   Upload Positive photos (3-5 шт).
    *   Upload Negative photos (3-5 шт).
    *   Sliders: Настройка весов (Importance).
    *   Output: Галерея Top-5 найденных совпадений с Scores.
*   [ ] Вкладка "Annotator Debug": Загрузить фото -> Показать сырой JSON от VLM.

### Фаза 7: Тестирование и Метрики
*   **Smoke Test:** Загрузить 5 азиаток -> в топе должны быть азиатки.
*   **Negative Test:** Загрузить "curvy" в negative -> они должны исчезнуть из топа.
*   **Performance:** Поиск по 5000 фото < 1 сек (Python in-memory).

---

## 5. Структура проекта
```
mvp/
├── schema/
│   ├── attributes.py       # Enum классы 
│   ├── models.py           # Pydantic схемы
│   └── distance_matrices.py # Матрицы
├── annotator/
│   ├── vlm_client.py       # API Client
│   └── prompts.py          # Prompt engineering
├── search/
│   ├── profile_builder.py  # Positive/Negative aggregation
│   ├── similarity.py       # Math core
│   └── ranker.py           # Weighting & Ranking
├── storage/
│   └── database.py         # JSON operations
├── ui/
│   └── app.py              # Gradio
└── main.py                 # Entry point
```
