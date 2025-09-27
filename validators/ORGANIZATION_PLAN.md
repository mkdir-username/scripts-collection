# План организации Python валидаторов

## 📊 Результаты анализа

### Обнаружено валидаторов
- **Всего файлов**: 19
- **Активных валидаторов**: 13
- **Архивных версий**: 4
- **Утилит и тестов**: 2

### Версионирование

| Версия | Файл | Статус | Зависимости |
|--------|------|--------|-------------|
| **v2.0.0** | `sdui_web_validator_v2.0.0_advanced_lines.py` | 🟢 Актуальный | Автономный |
| v1.2.0 | `sdui_web_validator_with_lines.py` | 🟡 Устаревший | Автономный |
| v1.1.0 | В архиве | 🔴 Архив | Автономный |
| v1.0.0 | `sdui_web_validator.py` | 🟡 Требует sdui_index_cache | sdui_index_cache.py |
| - | `simple_validator.py` | 🟢 Стабильный | Автономный |
| - | `byzantine_validator.py` | 🟢 Стабильный | Автономный |
| - | `sdui_visual_validator.py` | 🟡 Требует requests | requests, sdui_web_validator_improved |

### Внешние зависимости

#### Локальные модули
- `sdui_index_cache.py` - модуль кэширования (25KB, найден в проекте)
- `sdui_web_validator_improved.py` - зависимость для visual validator

#### Python пакеты
- `requests` - только для visual_validator

## 🎯 Рекомендованная структура

```
/Users/username/Scripts/validators/
├── v2.0.0/                          # ✅ Актуальная версия
│   ├── sdui_web_validator.py       # Основной валидатор
│   ├── line_mapper.py               # Модуль работы с номерами строк
│   └── README.md
│
├── v1.0.0/                          # ✅ Стабильные версии
│   ├── simple_validator.py         # Простая валидация
│   ├── byzantine_validator.py      # Byzantine Fault-Tolerant
│   └── README.md
│
├── specialized/                     # ✅ Специализированные
│   ├── visual_validator.py         # Визуальная валидация
│   ├── terminal_validator.py       # Проверка через API
│   ├── contract_validator.py       # Контрактная валидация
│   └── README.md
│
├── utils/                           # ✅ Утилиты
│   ├── sdui_index_cache.py        # Кэширование
│   ├── compatibility_checker.py    # Проверка совместимости
│   └── test_runner.py              # Запуск тестов
│
├── archive/                         # 📦 Архив старых версий
│   ├── v1.0.0/
│   ├── v1.1.0/
│   └── v1.2.0/
│
├── validate.py                      # 🚀 Единая точка входа
├── requirements.txt                 # 📋 Зависимости
├── setup.py                        # ⚙️ Установщик
└── README.md                       # 📖 Документация
```

## 🚀 Шаги реализации

### Шаг 1: Запуск миграции
```bash
cd /Users/username/Scripts/validators/
python migration_plan.py
```

### Шаг 2: Проверка миграции
```bash
# Проверка структуры
ls -la /Users/username/Scripts/validators/

# Тест основного валидатора
python v2.0.0/sdui_web_validator.py test_contract.json

# Тест простого валидатора
python v1.0.0/simple_validator.py test_contract.json
```

### Шаг 3: Установка зависимостей
```bash
cd /Users/username/Scripts/validators/
pip install -r requirements.txt
```

### Шаг 4: Настройка единой точки входа
```bash
# Использование универсального валидатора
python validate.py contract.json          # Автоматический выбор
python validate.py contract.json advanced # v2.0.0
python validate.py contract.json simple   # Простой валидатор
python validate.py contract.json byzantine # Byzantine валидатор
```

## 📝 Изменения в импортах

### Для sdui_web_validator.py (v1.0.0)
```python
# Было:
from sdui_index_cache import SDUIIndexCache

# Стало:
from utils.sdui_index_cache import SDUIIndexCache
```

### Для sdui_visual_validator.py
```python
# Было:
from sdui_web_validator_improved import SDUIWebValidatorImproved

# Стало:
from specialized.web_validator_improved import SDUIWebValidatorImproved
```

## ⚡ Оптимизации

### 1. Выделение общих модулей
- Класс `AdvancedJSONLineMapper` → отдельный модуль `utils/line_mapper.py`
- Общие функции валидации → `utils/common_validators.py`

### 2. Унификация интерфейса
Все валидаторы должны поддерживать:
```python
def validate_contract(contract_path: str) -> bool:
    """Валидирует контракт и возвращает True если успешно"""
    pass
```

### 3. Настройка логирования
```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🔧 Интеграция с проектом

### Добавление в PATH
```bash
# В ~/.bashrc или ~/.zshrc
export PATH="$PATH:/Users/username/Scripts/validators"
```

### Создание алиасов
```bash
alias validate-sdui='python /Users/username/Scripts/validators/validate.py'
alias validate-simple='python /Users/username/Scripts/validators/v1.0.0/simple_validator.py'
alias validate-advanced='python /Users/username/Scripts/validators/v2.0.0/sdui_web_validator.py'
```

### VS Code задачи
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate SDUI Contract",
      "type": "shell",
      "command": "python",
      "args": [
        "/Users/username/Scripts/validators/validate.py",
        "${file}"
      ],
      "problemMatcher": []
    }
  ]
}
```

## 📊 Метрики успеха

- ✅ Все валидаторы организованы по версиям
- ✅ Создана единая точка входа
- ✅ Документированы зависимости
- ✅ Архивированы старые версии
- ✅ Настроена структура для будущих версий

## 🎯 Приоритеты

### Критические (сейчас)
1. Сохранить работоспособность `sdui_web_validator_v2.0.0_advanced_lines.py`
2. Скопировать `sdui_index_cache.py` в utils

### Важные (сегодня)
1. Запустить `migration_plan.py`
2. Проверить работоспособность
3. Обновить импорты

### Желательные (эта неделя)
1. Создать тесты
2. Настроить CI/CD
3. Добавить логирование

## 📄 Лицензия и использование

Внутренний проект для валидации SDUI контрактов.
Все права защищены.

---
**Дата создания плана**: 2025-01-27
**Автор**: SDUI Validation Team
**Версия плана**: 1.0.0