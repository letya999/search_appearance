# 🎯 Visual Search Platform — Roadmap

## Цель
Создать универсальную платформу поиска по внешности с поддержкой любых VLM, текстовых промптов, генерации изображений и пользовательских баз данных.

---

## 📋 Этап 0: Подготовка инфраструктуры ✅

### 0.1 Конфигурация и настройки
- [x] Создать `mvp/core/config.py` — централизованная конфигурация
- [x] Создать `config/providers.yaml` — настройки провайдеров
- [x] Добавить Pydantic Settings для валидации конфига

### 0.2 Рефакторинг структуры
```
mvp/
├── providers/          # VLM провайдеры
├── generators/         # Генераторы изображений
├── text_search/        # Поиск по промпту
├── storage/            # БД и кэши
├── search/             # Поисковые стратегии
├── api/
│   └── routes/         # Разделенные роуты
└── core/               # Общие компоненты
```

---

## 📋 Этап 1: Универсальные VLM провайдеры ✅

### 1.1 Базовая архитектура
- [x] `mvp/providers/base.py` — абстрактный класс `VLMProvider`
  ```python
  class VLMProvider(ABC):
      @abstractmethod
      async def analyze_image(self, image: bytes, prompt: str) -> str: ...
      @abstractmethod 
      async def parse_text_to_profile(self, text: str) -> dict: ...
  ```

### 1.2 Реализация провайдеров
- [x] `openai_provider.py` — GPT-4o, GPT-4V
- [x] `anthropic_provider.py` — Claude 3.5 Sonnet/Opus
- [x] `gemini_provider.py` — Gemini 2.0 Flash
- [x] `ollama_provider.py` — LLaVA, Qwen-VL (локальные)
- [x] `openrouter_provider.py` — агрегатор

### 1.3 Provider Registry
- [x] `mvp/providers/registry.py`
  - Автоопределение провайдера по API ключу
  - Fallback chain при ошибках
  - Rate limiting per provider
  - Health checks

**Результат:** Поддержка 5+ VLM провайдеров с автоматическим fallback.

---

## 📋 Этап 2: Пользовательская база данных

### 2.1 Выбор хранилища
- [ ] **SQLite + LanceDB** для MVP
  - SQLite: метаданные, пользователи, сессии
  - LanceDB: векторные эмбеддинги (локальный, простой)
- [ ] Миграции через Alembic

### 2.2 Модели данных
```python
# mvp/storage/models.py
class User(SQLModel):
    id: UUID
    email: str
    api_keys: dict  # Провайдеры пользователя

class PhotoCollection(SQLModel):
    id: UUID
    user_id: UUID
    name: str
    description: str
    photo_count: int

class StoredPhoto(SQLModel):
    id: UUID
    collection_id: UUID
    image_path: str
    profile: PhotoProfile  # JSON
    embedding: bytes       # Сериализованный numpy
    created_at: datetime

class SearchSession(SQLModel):
    id: UUID
    user_id: UUID
    collection_id: UUID
    positives: List[UUID]
    negatives: List[UUID]
    started_at: datetime
    completed_at: datetime
    results: List[dict]     # JSON
```

### 2.3 API для коллекций
- [ ] `POST /collections` — создать коллекцию
- [ ] `POST /collections/{id}/photos` — добавить фото
- [ ] `GET /collections/{id}/stats` — статистика
- [ ] `DELETE /collections/{id}` — удалить

**Результат:** Пользователи могут загружать свои базы фото.

---

## 📋 Этап 3: Конструктор атрибутов (Custom Schema)

### 3.1 Dynamic Attributes
- [ ] `mvp/schema/dynamic_schema.py`
  ```python
  class CustomAttribute:
      name: str
      type: Literal["enum", "scale", "boolean", "text"]
      values: Optional[List[str]]  # Для enum
      range: Optional[Tuple[float, float]]  # Для scale
      prompt_hint: str  # Как описывать VLM
  
  class CustomSchema:
      attributes: List[CustomAttribute]
      base_prompt: str
  ```

### 3.2 UI для конструктора
- [ ] Drag-and-drop редактор атрибутов
- [ ] Предустановленные шаблоны:
  - 👤 Внешность человека (текущий)
  - 🐕 Животные
  - 🏠 Недвижимость
  - 👗 Одежда/мода

### 3.3 Автогенерация промптов
- [ ] Генерация system prompt из CustomSchema
- [ ] Валидация ответа VLM против схемы

**Результат:** Пользователи создают свои классы атрибутов.

---

## 📋 Этап 4: Поиск по текстовому промпту

### 4.1 Text → Profile Parser
- [ ] `mvp/text_search/prompt_parser.py`
  ```python
  async def parse_appearance_prompt(text: str) -> PhotoProfile:
      """
      Вход: "Высокий блондин с бородой, 30-40 лет"
      Выход: PhotoProfile с заполненными атрибутами
      """
  ```

### 4.2 Fuzzy Matching
- [ ] Синонимы атрибутов ("светлые волосы" = "blonde")
- [ ] NLP извлечение сущностей
- [ ] Confidence scoring для частичных совпадений

### 4.3 API endpoint
- [ ] `POST /search/text`
  ```json
  {
    "prompt": "Высокий спортивный мужчина с темными волосами",
    "collection_id": "uuid",
    "top_k": 20
  }
  ```

**Результат:** Поиск по описанию без загрузки фото.

---

## 📋 Этап 5: Генерация и поиск

### 5.1 Image Generators
- [ ] `mvp/generators/base.py` — базовый класс
- [ ] `dalle_generator.py` — DALL-E 3
- [ ] `stability_generator.py` — Stable Diffusion XL
- [ ] `flux_generator.py` — Flux via Replicate

### 5.2 Pipeline: Generate → Analyze → Search
```python
async def generate_and_search(prompt: str, generator: str):
    # 1. Генерируем изображение
    image = await generators[generator].generate(prompt)
    # 2. Анализируем VLM
    profile = await vlm.analyze(image)
    # 3. Ищем похожих
    results = ranker.rank(collection, profile)
    return {"generated": image, "profile": profile, "results": results}
```

### 5.3 API endpoint
- [ ] `POST /search/generate`

**Результат:** Описание → Генерация → Поиск в одном запросе.

---

## 📋 Этап 6: Real-time прогресс

### 6.1 WebSocket API
- [ ] `mvp/api/websocket.py`
  ```python
  @app.websocket("/ws/search/{session_id}")
  async def search_progress(websocket: WebSocket, session_id: str):
      # Отправляем прогресс:
      # {"stage": "analyzing", "current": 3, "total": 5, "elapsed": 2.4}
      # {"stage": "ranking", "progress": 0.45, "elapsed": 5.1}
      # {"stage": "complete", "results_count": 20, "total_time": 7.3}
  ```

### 6.2 Search Session Tracking
- [ ] `mvp/search/session.py`
  ```python
  class SearchSession:
      id: str
      started_at: datetime
      stages: List[SearchStage]
      
      def elapsed_seconds(self) -> float: ...
      def current_stage(self) -> SearchStage: ...
      def progress(self) -> float: ...  # 0.0 - 1.0
  ```

### 6.3 Frontend интеграция
- [ ] Компонент `SearchProgress.tsx`
  - Прогресс-бар по этапам
  - Таймер прошедшего времени
  - ETA до завершения
  - Анимация текущего этапа

**Результат:** Пользователь видит прогресс в реальном времени.

---

## 📋 Этап 7: Улучшения UX

### 7.1 История поисков
- [ ] Сохранение всех поисков пользователя
- [ ] Replay поиска с теми же параметрами
- [ ] Сравнение результатов разных поисков

### 7.2 Сохранение примеров
- [ ] "Избранные" фото для быстрого доступа
- [ ] Теги и категории для примеров
- [ ] Шаблоны поисков (preset + / -)

### 7.3 Batch Upload
- [ ] Drag-and-drop множества файлов
- [ ] ZIP архив с фотографиями
- [ ] Прогресс загрузки и анализа

### 7.4 Export результатов
- [ ] JSON / CSV экспорт
- [ ] PDF отчет с фотографиями
- [ ] Ссылка для sharing

---

## 📋 Этап 8: Оптимизации

### 8.1 Кэширование
- [ ] Redis для:
  - Результатов анализа (по хэшу изображения)
  - Parsed промптов
  - Горячих запросов

### 8.2 Дедупликация
- [ ] Проверка дубликатов при загрузке (уже есть!)
- [ ] Перцептивный хэш (pHash) для быстрой проверки

### 8.3 Async оптимизации
- [ ] Параллельный анализ нескольких фото
- [ ] Streaming ответов от VLM
- [ ] Background tasks для тяжелых операций

---

## 🎯 Приоритеты

| Этап | Название | Приоритет | Сложность | Ценность |
|------|----------|-----------|-----------|----------|
| 1 | VLM провайдеры | 🔴 P0 | Medium | Критично |
| 2 | Пользовательская БД | 🔴 P0 | Medium | Критично |
| 6 | Real-time прогресс | 🔴 P0 | Easy | Высокая |
| 4 | Text → Search | 🟡 P1 | Easy | Высокая |
| 3 | Custom Schema | 🟡 P1 | Hard | Высокая |
| 5 | Генерация + поиск | 🟡 P1 | Medium | Средняя |
| 7 | UX улучшения | 🟢 P2 | Easy | Средняя |
| 8 | Оптимизации | 🟢 P2 | Medium | Средняя |

---

## 📅 Примерный Timeline

```
Неделя 1-2:  Этапы 0, 1, 6 (Инфраструктура + VLM + Прогресс)
Неделя 3-4:  Этап 2 (Пользовательская БД)
Неделя 5-6:  Этапы 4, 5 (Text search + Generate)
Неделя 7-8:  Этап 3 (Custom Schema)
Неделя 9+:   Этапы 7, 8 (UX + Оптимизации)
```

---

## 🔧 Технологии

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI + SQLModel |
| Database | SQLite (metadata) + LanceDB (vectors) |
| Cache | Redis |
| Frontend | React + Vite + WebSocket |
| VLM | OpenAI, Anthropic, Gemini, Ollama |
| Generators | DALL-E 3, Stability AI, Flux |
| Embeddings | CLIP / OpenAI embeddings |

---

## ✅ Что уже готово

- [x] Базовый VLM client (OpenRouter/OpenAI)
- [x] PhotoProfile schema с 20+ атрибутами
- [x] Ranker с weighted scoring
- [x] Проверка дубликатов по эмбеддингам
- [x] React UI с glassmorphism
- [x] Docker deployment
