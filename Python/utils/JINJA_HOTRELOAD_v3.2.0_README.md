# Jinja Hot Reload v3.2.0 - SMART MODE

## 🎯 Что нового в v3.2.0

### 🧠 Интеллектуальный режим (Smart Mode)

Новый режим с автоматическим исправлением типичных ошибок в JSON/Jinja2 контрактах.

**Возможности:**

1. **SmartJSONFixer** - интеллектуальное исправление JSON:
   - ✅ Удаление trailing commas (`},` → `}`)
   - ✅ Добавление missing commas (` } {` → `}, {`)
   - ✅ Замена пустых значений на `null` (`: ,` → `: null,`)
   - ✅ Нормализация пробелов

2. **SmartJinja2ContextBuilder** - умные заглушки для undefined переменных:
   - ✅ Автоматическое создание заглушек для отсутствующих переменных
   - ✅ Умное определение типа заглушки по контексту:
     - `{% for x in items %}` → `items = []`
     - `{% if flag %}` → `flag = False`
     - `{{ user.name }}` → `user = defaultdict(lambda: None)`
     - По умолчанию → `""`

3. **Улучшенная диагностика**:
   - ✅ Детальные сообщения об ошибках с контекстом
   - ✅ Автоматическое создание debug файлов
   - ✅ Логирование всех примененных исправлений

## 📦 Использование

### Базовый режим (без изменений)

```bash
# Старая версия v3.1.0
python3 jinja_hot_reload_v3.1.0.py

# или через alias
jj
```

### 🧠 Smart режим (новый!)

```bash
# Включить smart режим
python3 jinja_hot_reload_v3.2.0.py --smart

# Smart + Debug
python3 jinja_hot_reload_v3.2.0.py --smart --debug

# Smart + Тестирование (однократная обработка)
python3 jinja_hot_reload_v3.2.0.py --smart --test

# Smart для конкретной директории
python3 jinja_hot_reload_v3.2.0.py --smart --path /path/to/dir
```

### Создать новый alias для v3.2.0

```bash
# Добавить в ~/.zshrc или ~/.bashrc
alias jj2='python3 /Users/username/Scripts/Python/utils/jinja_hot_reload_v3.2.0.py'
alias jj-smart='python3 /Users/username/Scripts/Python/utils/jinja_hot_reload_v3.2.0.py --smart'

# Применить
source ~/.zshrc
```

## 🔍 Примеры работы Smart режима

### Пример 1: Автоматическое создание заглушек

**Входной файл `[JJ_PC]_test.json.j2`:**
```json
{
  "title": "{{ title }}",
  "items": [
    {% for item in products %}
      {
        "name": "{{ item.name }}",
        "price": {{ item.price }}
      }
    {% endfor %}
  ],
  "isActive": {% if isEnabled %}true{% else %}false{% endif %}
}
```

**Data файл `[data]_test.json` (пустой):**
```json
{}
```

**Без smart режима:**
```
❌ Ошибка Jinja2: 'title' is undefined
❌ Ошибка Jinja2: 'products' is undefined
❌ Ошибка Jinja2: 'isEnabled' is undefined
```

**Со smart режимом:**
```
✅ Создано заглушек: 3
  • title = ""
  • products = []
  • isEnabled = False
✅ Создан: [FULL_PC]_test_web.json
```

### Пример 2: Исправление JSON структуры

**Проблемный JSON после препроцессинга:**
```json
{
  "key1": ,
  "key2": "value"
  "key3": {}
}
```

**Smart исправления:**
```
🧠 Smart исправления:
  - Заменены пустые значения на null (после двоеточия перед запятой)
  - Добавлены 1 запятых между свойствами
```

**Результат:**
```json
{
  "key1": null,
  "key2": "value",
  "key3": {}
}
```

## 📊 Сравнение v3.1.0 vs v3.2.0

| Функция | v3.1.0 | v3.2.0 Smart |
|---------|--------|--------------|
| Обработка Jinja2 | ✅ | ✅ |
| Undefined переменные | ❌ Ошибка | ✅ Заглушки |
| Trailing commas | ⚠️ Базовая | ✅ Умная |
| Missing commas | ❌ | ✅ |
| Пустые значения | ⚠️ Базовая | ✅ Умная |
| Детальная диагностика | ⚠️ | ✅ |
| Debug файлы | ✅ | ✅ Улучшенные |

## 🎬 Пример использования

```bash
# 1. Перейти в директорию с контрактами
cd /Users/username/Documents/front-middle-schema/.JSON

# 2. Запустить в smart режиме
python3 /Users/username/Scripts/Python/utils/jinja_hot_reload_v3.2.0.py --smart

# Вывод:
# ╔══════════════════════════════════════════════════╗
# ║     Jinja Hot Reload v3.2.0                     ║
# ║     🧠 SMART MODE: Intelligent Error Fixing     ║
# ╚══════════════════════════════════════════════════╝
#
# 2025-09-30 17:30:00 - INFO - 📁 Директория наблюдения: ./.JSON
# 2025-09-30 17:30:00 - INFO - 🧠 Smart режим: ✅ Включен
# 2025-09-30 17:30:00 - INFO - 👀 Отслеживание изменений...
# 2025-09-30 17:30:00 - INFO - 📊 Найдено 9 [JJ_] файлов
#
# 2025-09-30 17:30:00 - INFO - 🔄 Обработка: [JJ_PC]_test.json.j2
# 2025-09-30 17:30:00 - INFO - 🧠 Создано заглушек: 3
# 2025-09-30 17:30:00 - INFO - ✅ Создан: [FULL_PC]_test_web.json
# 2025-09-30 17:30:00 - INFO - 🌐 Браузер Vivaldi перезагружен
```

## ⚙️ Все параметры командной строки

```bash
python3 jinja_hot_reload_v3.2.0.py [OPTIONS]

OPTIONS:
  --path PATH              Директория для наблюдения
                          (по умолчанию: /Users/username/Documents/front-middle-schema/.JSON)

  --debug                 Включить режим отладки
                          (подробное логирование, контекст ошибок)

  --test                  Однократная обработка без наблюдения
                          (обработать все файлы и выйти)

  --no-browser-reload     Отключить автоматическую перезагрузку браузера
                          (не перезагружать Vivaldi:9090)

  --smart                 🧠 Включить интеллектуальный режим
                          (автоисправление ошибок, умные заглушки)

  -h, --help              Показать справку
```

## 🚀 Рекомендации

### Когда использовать v3.2.0 Smart:

✅ **Используйте Smart режим если:**
- В контрактах есть undefined переменные
- Встречаются ошибки парсинга JSON
- Нужна автоматическая обработка множества файлов
- Хотите сэкономить время на ручных исправлениях

❌ **Не используйте Smart режим если:**
- Нужен строгий контроль над данными
- Важна точность undefined переменных
- Контракты уже валидны и работают

### Миграция с v3.1.0 на v3.2.0:

1. **Протестируйте на одном файле:**
   ```bash
   python3 jinja_hot_reload_v3.2.0.py --smart --test --debug --path /path/to/single/file
   ```

2. **Проверьте результат:**
   - Откройте `[FULL_*]_web.json`
   - Проверьте debug файлы если были ошибки
   - Убедитесь что данные корректны

3. **Если всё OK - используйте постоянно:**
   ```bash
   # Замените alias jj на v3.2.0
   alias jj='python3 /Users/username/Scripts/Python/utils/jinja_hot_reload_v3.2.0.py --smart'
   ```

## 🐛 Известные ограничения

1. **Большие файлы с complex Jinja2:**
   - Препроцессор может удалить переносы строк
   - Результирующий JSON может быть в одну строку
   - **Решение**: Используйте `--debug` для анализа

2. **Сложные вложенные конструкции:**
   - Некоторые edge cases могут не обрабатываться
   - **Решение**: Ручное исправление проблемных мест

3. **Производительность:**
   - Smart режим медленнее на ~10-15%
   - **Решение**: Выключайте для больших проектов если скорость критична

## 📝 Логи и debug

### Где найти debug файлы:

```
/path/to/contract/
  ├── [JJ_PC]_contract.json.j2           # Исходный файл
  ├── [data]_contract.json                # Data файл
  ├── [FULL_PC]_contract_web.json        # Результат ✅
  └── [JJ_PC]_contract_debug_cleaned.json # Debug (если ошибка)
```

### Анализ проблем:

```bash
# 1. Запустить с debug
python3 jinja_hot_reload_v3.2.0.py --smart --debug --test

# 2. Найти debug файл
ls -la *_debug_cleaned.json

# 3. Посмотреть проблемное место
cat [JJ_PC]_contract_debug_cleaned.json | python3 -m json.tool
```

## 📞 Поддержка

Если обнаружена проблема:

1. Запустите с флагами `--smart --debug`
2. Сохраните логи
3. Сохраните debug файл
4. Опишите проблему

---

**Версия:** v3.2.0
**Дата:** 2025-09-30
**Автор:** Claude Code