# SDUI Enhanced Resolver - Руководство по использованию

## Обзор

SDUI Enhanced Resolver - это улучшенная версия инструмента для работы с SDUI (Server-Driven UI) схемами. Добавлены новые функции для интеграции с агентами, валидации, расчета метрик надежности и обработки StateAware паттернов.

## Ключевые улучшения по сравнению с оригиналом

### 1. Truth Score Метрика
- **Детерминистическая оценка надежности** контракта (0.0 - 1.0)
- Минимальный порог 0.95 для production
- Учитывает валидацию, web release статус, StateAware паттерны

### 2. Валидация против метасхемы
- Проверка required полей
- Валидация типов данных
- Обнаружение лишних полей
- Совместимость с strict_unversioned.json

### 3. StateAware паттерны
- Автоматическое обнаружение Control<T>, Focus<T>, Selection<T>
- Извлечение и индексация StateAware компонентов
- Адаптивные лимиты дублирования для StateAware

### 4. API для агентов
- JSON-RPC интерфейс
- Batch обработка контрактов
- Метрики производительности
- Расширенное логирование

## Установка и настройка

```bash
# Установка зависимостей (стандартная библиотека Python)
python3 --version  # Требуется Python 3.8+

# Проверка работы
python3 sdui_resolver_enhanced.py --help
```

## Основные классы и компоненты

### ResolverConfig
Конфигурация резолвера с параметрами:
```python
config = ResolverConfig(
    base_path="/path/to/SDUI",
    metaschema_path="/path/to/strict_unversioned.json",
    web_only=True,  # Фильтрация только web компонентов
    max_depth=50,    # Максимальная глубина рекурсии
    truth_score_threshold=0.95,  # Минимальный Truth Score
    enable_api=True,  # Включить API режим
    verbose=True     # Детальное логирование
)
```

### ComponentMetrics
Метрики компонента для расчета Truth Score:
- `occurrences` - количество вхождений
- `validation_errors` - ошибки валидации
- `missing_fields` - отсутствующие required поля
- `stateaware_patterns` - найденные StateAware паттерны

### SDUIEnhancedResolver
Основной класс с новыми методами:

#### validate_against_metaschema()
```python
def validate_against_metaschema(contract: Dict, metaschema_path: Optional[Path]) -> Dict
```
Валидация контракта против метасхемы. Возвращает:
```python
{
    "valid": bool,
    "errors": List[str],
    "warnings": List[str],
    "checked_at": str  # ISO timestamp
}
```

#### calculate_truth_score()
```python
def calculate_truth_score(contract: Dict, schema: Optional[Dict]) -> float
```
Расчет детерминистической метрики надежности (0.0-1.0).
Факторы влияющие на score:
- Наличие обязательных полей (-0.1 за каждое отсутствующее)
- Ошибки валидации (-0.05 за каждую)
- Web release статус (-0.15 если не released)
- StateAware паттерны (+0.05 за каждый, макс 3)
- Количество заглушек (-0.02 за каждую)

#### check_web_released_status()
```python
def check_web_released_status(component: Dict) -> bool
```
Проверка готовности компонента для web платформы.
Поддерживает форматы:
- `"released"` - полный релиз
- `"1.0.0"` - версионированный релиз
- `"beta"`, `"alpha"`, `"rc"` - pre-release версии

#### extract_stateaware_patterns()
```python
def extract_stateaware_patterns(contract: Dict) -> List[Dict]
```
Извлечение StateAware паттернов из контракта.
Обнаруживает:
- Control<T> - контроль состояния
- Focus<T> - фокус элементов
- Selection<T> - выбор элементов
- StateRef<T> - ссылки на состояние
- Binding<T> - привязка данных

#### generate_component_map()
```python
def generate_component_map(contract: Dict) -> Dict
```
Генерация карты компонентов с их взаимосвязями:
```python
{
    "components": {...},     # Все компоненты
    "references": [...],     # Связи между компонентами
    "hierarchy": {...},      # Иерархия вложенности
    "statistics": {...}      # Статистика
}
```

#### validate_required_fields()
```python
def validate_required_fields(contract: Dict, schema: Dict) -> Dict
```
Детальная валидация required полей:
```python
{
    "valid": bool,
    "missing_fields": List[str],
    "type_mismatches": List[Dict],
    "extra_fields": List[str]
}
```

## API интерфейс для агентов

### SDUIResolverAPI
Класс для интеграции с агентами через JSON-RPC или REST.

#### Доступные действия:
- `resolve` - разрешение схемы
- `validate` - валидация контракта
- `calculate_score` - расчет Truth Score
- `extract_patterns` - извлечение StateAware паттернов
- `batch` - пакетная обработка

#### Формат запроса:
```json
{
    "action": "resolve",
    "file_path": "/path/to/schema.json"
}
```

#### Формат ответа:
```json
{
    "success": true,
    "data": {...},
    "truth_score": 0.97
}
```

## Использование из командной строки

### Базовое использование:
```bash
python3 sdui_resolver_enhanced.py input.json -o output.json
```

### С валидацией против метасхемы:
```bash
python3 sdui_resolver_enhanced.py input.json \
    --metaschema /path/to/strict_unversioned.json \
    --validate \
    --score
```

### Фильтрация только web компонентов:
```bash
python3 sdui_resolver_enhanced.py input.json \
    --web-only \
    --verbose
```

### Извлечение StateAware паттернов:
```bash
python3 sdui_resolver_enhanced.py input.json \
    --patterns \
    --pretty
```

### Запуск в API режиме:
```bash
python3 sdui_resolver_enhanced.py input.json \
    --api \
    --api-port 8080
```

## Интеграция в Python код

### Минимальный пример:
```python
from sdui_resolver_enhanced import SDUIEnhancedResolver, ResolverConfig

config = ResolverConfig(
    base_path="/path/to/SDUI",
    web_only=True
)
resolver = SDUIEnhancedResolver(config)
resolved = resolver.resolve_file("schema.json")
print(f"Truth Score: {resolved['_metadata']['truth_score']}")
```

### Пример с валидацией:
```python
# Загрузка с валидацией
config = ResolverConfig(
    base_path="/path/to/SDUI",
    metaschema_path="/path/to/strict_unversioned.json"
)
resolver = SDUIEnhancedResolver(config)

# Разрешение с проверками
resolved = resolver.resolve_file("schema.json")
validation = resolver.validate_against_metaschema(resolved)

if not validation["valid"]:
    print("Validation errors:")
    for error in validation["errors"]:
        print(f"  - {error}")
```

### Пример batch обработки:
```python
files = ["screen1.json", "screen2.json", "screen3.json"]
results = resolver.batch_resolve(files)

for result in results:
    if result["success"]:
        print(f"{result['file']}: Score {result['data']['_metadata']['truth_score']}")
    else:
        print(f"{result['file']}: Error - {result['error']}")
```

## Метаданные в результате

Каждая разрешенная схема содержит расширенные метаданные в поле `_metadata`:

```json
{
    "_metadata": {
        "original_file": "path/to/file.json",
        "processing_time": 0.234,
        "truth_score": 0.97,
        "total_resolutions": 42,
        "total_stubs": 3,
        "unique_components": 15,
        "component_stats": {
            "Button": 5,
            "Text": 12
        },
        "stateaware_components": ["ControlledInput", "SelectableList"],
        "stateaware_patterns": [...],
        "validation_errors": [],
        "validation_result": {...},
        "component_map": {...},
        "navigation_index": {...},
        "performance": {
            "cache_hits": 28,
            "processing_time_ms": 234
        }
    }
}
```

## Рекомендации по использованию

### 1. Для production контрактов:
- Всегда проверяйте Truth Score >= 0.95
- Используйте валидацию против метасхемы
- Включайте web-only фильтрацию

### 2. Для отладки:
- Используйте verbose режим
- Анализируйте validation_errors
- Проверяйте component_map для понимания связей

### 3. Для интеграции с агентами:
- Используйте API интерфейс
- Включайте batch обработку для множества файлов
- Логируйте performance метрики

### 4. Для оптимизации производительности:
- Используйте кеширование (автоматически)
- Ограничивайте max_depth при глубокой вложенности
- Применяйте batch обработку вместо последовательной

## Обработка ошибок

Резолвер предоставляет детальную информацию об ошибках:

```python
try:
    resolved = resolver.resolve_file("schema.json")
except Exception as e:
    # Проверяем логи
    if resolver.errors:
        print("Errors during resolution:")
        for error in resolver.errors:
            print(f"  - {error}")
    
    # Проверяем предупреждения
    if resolver.warnings:
        print("Warnings:")
        for warning in resolver.warnings:
            print(f"  - {warning}")
```

## Совместимость

- **Python**: 3.8+
- **Обратная совместимость**: Полная с sdui_resolver_final.py
- **Платформы**: Windows, macOS, Linux
- **Схемы**: SDUI v1, v2, strict_unversioned

## Поддержка и контакты

Для вопросов по использованию обращайтесь к документации SDUI схем в:
- `/Users/username/Documents/front-middle-schema/SDUI/`
- Метасхемы в `/Users/username/Documents/front-middle-schema/metaschemas/`

## Лицензия

Внутренний инструмент для работы с SDUI схемами.