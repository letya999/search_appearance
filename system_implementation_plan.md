# Полный план реализации сервиса Visual Dating Search (Twinby Feature)

Этот документ описывает полную архитектуру и план внедрения функции поиска партнеров по внешности ("Visual Search") на основе Vision-Language Models (VLM).

---

## 1. Общее описание системы

### Цель
Позволить пользователям загрузить 5 "позитивных" (кто нравится) и 5 "негативных" (кто не нравится) фото, чтобы найти наиболее подходящих партнеров в базе Twinby.

### Ключевая технология
Использование **VLM (Vision-Language Models)**, таких как **Qwen2.5-VL** или **Llava-NeXT**, для извлечения детальных атрибутов (цвет глаз, стиль, фон, лайфстайл) вместо простых векторных эмбеддингов. Это дает интерпретируемость ("почему этот человек подошел?") и контроль (фильтрация).

### Архитектура (High-Level)
1.  **Ingestion Service**: Обработка фото при загрузке пользователя (асинхронно).
2.  **VLM Annotator**: GPU-сервис, который "смотрит" на фото и выдает JSON с атрибутами.
3.  **Vector/Attribute DB**: Хранилище профилей (PostgreSQL + JSONB или Qdrant).
4.  **Search API**: Эндпоинт, который принимает 10 фото, строит "профиль предпочтений" и возвращает кандидатов.

---

## 2. Глубокое исследование (Deep Research)

Если вы хотите найти готовые решения перед стартом, используйте этот промпт для поиска.

### Промпт для Deep Research (Copy-Paste)
> "Act as a Senior Computer Vision Engineer. I need to build a 'Visual Search for Dating' system where users upload 5 positive and 5 negative anchor images to find similar profiles.
> Key requirements:
> 1. Use Vision-Language Models (like Qwen-VL, Llava) to extract semantic attributes (hair color, body type, style, background objects) with confidence scores.
> 2. Fuzzy matching logic: 'Light brown hair' should be close to 'Blonde', independent 'background' signals.
> 3. Tech stack: Python.
>
> Please perform a deep search on GitHub and Arxiv for:
> - Open source projects implementing 'Attribute-based Visual Search' or 'Feedback-driven Image Retrieval'.
> - Methods for 'Negative Relevance Feedback' in visual search.
> - Best practices for prompting VLMs to output structured JSON attributes for people analysis.
> - Specific repos related to 'Fashion attribute recognition' or 'Person re-identification with attributes' that can be adapted.
>
> List top 5 GitHub repositories, 3 relevant papers, and a proposed architectural stack."

---

## 3. Техническая реализация (Step-by-Step)

### Этап 1: Инфраструктура и VLM Service
Нам нужен сервис, который дешево и быстро размечает миллионы фото.

*   **Модель**: `Qwen2.5-VL-7B-Instruct` (Отличный баланс качество/скорость).
*   **Хостинг**:
    *   *Вариант А (Простой)*: OpenRouter API / Replicate (плата за токен/секунду).
    *   *Вариант Б (Собственный)*: RunPod / LambdaLabs с `vLLM` или `SGLang` (дешевле на объеме).
*   **Очереди**: Celery + RabbitMQ/Redis. Фото пользователей не должны тормозить API, разметка идет в фоне.
*   **Промпт инжиниринг**:
    Написать системный промпт, возвращающий **только JSON**.
    ```text
    SYSTEM: You are a visual dating assistant. Analyze the image and extract attributes in JSON format with confidence (0.0-1.0).
    Schema: {
      "appearance": {"hair_color": ..., "body_type": ...},
      "style": {"clothing": ..., "vibe": ...},
      "context": {"objects": ["car", "gym"], "setting": "beach"}
    }
    ```

### Этап 2: База данных и схема (Hybrid Search)
Для лучшего качества используем комбинацию:
1.  **Атрибутивный поиск (Hard/Fuzzy Filter)**: "Хочу брюнетку, не курящую".
2.  **Векторный поиск (Visual Similarity)**: Общее визуальное сходство (эмбеддинги CLIP/SigLIP).

**Стек**:
*   **PostgreSQL (с pgvector)**:
    *   Таблица `users_photos`: поля `id`, `user_id`, `url`.
    *   Column `attributes` (JSONB): `{hair: {brown: 0.9}, ...}` — для фильтрации.
    *   Column `embedding` (vector): CLIP embedding фото (опционально, для общего стиля).

### Этап 3: Алгоритм поиска (Search Engine)
Самая важная часть — обработка 5+ и 5- фото.

1.  **Profile Aggregation**:
    *   Получаем 10 фото → прогоняем через VLM → получаем 10 JSON-ов.
    *   Строим **Target Profile**:
        *   `Target_Hair = Avg(Positive_Hair) - Coeff * Avg(Negative_Hair)`
        *   Если у 4/5 позитивных "Спортзал", а у негативных нет → `Sport_Interest = High`.
2.  **Query Execution**:
    *   Сначала быстрый отсев по жестким критериям (Gender, Age).
    *   Затем скоринг по Fuzzy Attributes (как описано в `implementation_plan.md` - матрицы расстояний).
    *   (Опционально) Reranking с помощью CLIP-эмбеддингов позитивных фото.

### Этап 4: API и Интеграция
**FastAPI Service**:
*   `POST /v1/photos/process_batch`: Принимает ID фото, отправляет в VLM (для фоновой обработки новых юзеров).
*   `POST /v1/search/visual`:
    *   Input: `{"positive_photo_ids": [...], "negative_photo_ids": [...]}`
    *   Output: `{"matched_users": [{user_id, match_score, explanation: "Similar hair color and vibe"}]}`

---

## 4. План разработки (Roadmap)

| Неделя | Задача | Результат |
|--------|--------|-----------|
| **1** | **R&D и VLM Setup** | Скрипт на Python, который берет фото и выдает идеальный JSON атрибутов через Qwen2.5. Настройка категорий (20 классов). |
| **2** | **Data Ingestion** | Pipeline для прогона текущей базы фото (или семпла 10к) через VLM. Сохранение в Postgres. |
| **3** | **Search Core** | Реализация математики "Агрегация профиля" и "Fuzzy Matching". Unit-тесты на примерах. |
| **4** | **API & UI Demo** | FastAPI обертка. Простой Streamlit/Gradio интерфейс для загрузки 10 фото и просмотра выдачи. |
| **5** | **Optimization** | Тюнинг весов, ускорение SQL запросов, кеширование популярных атрибутов. |

## 5. Оценка стоимости MVP (Cloud)
*   **VLM Inference**: ~0.005$ за фото (OpenRouter). На 100,000 фото = $500.
    *   *Дешевле*: Арендовать A100 на RunPod ($2/час). За час можно обработать ~5000 фото. 100к фото = 20 часов = $40.
*   **Hosting**: Hetzner/AWS EC2 (CPU для API) ~ $20-50/мес.
*   **DB**: Managed Postgres ~ $20/мес.

**Итого MVP Infrastructure**: ~$100-200.

---

## Что делать прямо сейчас?
1.  Я могу создать структуру проекта для **MVP** (папки `api`, `core`, `vlm`).
2.  Я могу написать скрипт **VLM Annotator** прямо сейчас, если вы дадите API ключ (или будем использовать моки пока).
3.  Оформить список из 20 атрибутов в виде Pydantic моделей (код) для фиксации контракта данных.
