# Быстрый старт - vscode-validator v2.3.1

## Установка и сборка

```bash
cd /Users/username/Scripts/vscode-validator-v2.3.1

# Установка зависимостей (уже выполнено)
npm install

# Сборка проекта
npm run build
```

## Использование CLI

### Базовая валидация

```bash
# Валидация одного файла
node dist/cli.js examples/test-valid.json

# С детальным выводом
node dist/cli.js examples/test-valid.json --verbose

# Проверка с Jinja поддержкой
node dist/cli.js examples/test-jinja.jinja.json --jinja-aware
```

### Форматы вывода

```bash
# JSON формат
node dist/cli.js examples/test-valid.json -o json

# HTML отчет
node dist/cli.js examples/test-valid.json -o html > report.html
```

### Batch валидация

```bash
# Валидация всех примеров
node dist/cli.js examples/*.json --verbose

# Рекурсивная валидация директории
node dist/cli.js examples/ -r
```

### Метрики производительности

```bash
node dist/cli.js examples/test-valid.json --performance
```

## Programmatic API

```typescript
import { validateFile } from 'vscode-sdui-validator';

// Простая валидация
const result = await validateFile('path/to/file.json');

if (result.isValid) {
  console.log('✓ Файл валиден');
} else {
  console.log(`✗ Найдено ${result.errorCount} ошибок`);
  result.errors.forEach(error => {
    console.log(`  Line ${error.line}: ${error.message}`);
  });
}
```

### С опциями

```typescript
const result = await validateFile('path/to/file.json', {
  jinjaAware: true,        // Поддержка Jinja2
  strict: true,            // Строгий режим
  maxFileSize: 10485760,   // Максимальный размер (10MB)
  trackPerformance: true   // Метрики производительности
});
```

### Batch валидация

```typescript
import { validateFiles } from 'vscode-sdui-validator';

const results = await validateFiles([
  'file1.json',
  'file2.jinja.json',
  'file3.j2.java'
], {
  jinjaAware: true
});

const failedFiles = results.filter(r => !r.isValid);
console.log(`Провалено: ${failedFiles.length} файлов`);
```

## Тестирование

### Автоматический тест CLI

```bash
./test-cli.sh
```

### Ручное тестирование

```bash
# Валидный файл
node dist/cli.js examples/test-valid.json
# Ожидается: ✓ Valid

# Невалидный файл
node dist/cli.js examples/test-invalid.json
# Ожидается: ✗ с ошибкой парсинга

# Jinja файл
node dist/cli.js examples/test-jinja.jinja.json --jinja-aware
# Ожидается: валидация шаблона
```

## Exit Codes

- **0** - Валидация успешна
- **1** - Найдены ошибки валидации

```bash
node dist/cli.js examples/test-valid.json && echo "Success" || echo "Failed"
```

## Поддерживаемые файлы

- `.json` - обычный JSON
- `.jinja.json` - JSON с Jinja2 шаблонами
- `.j2.java` - Java файлы с Jinja2

## Флаги CLI

| Флаг | Описание | По умолчанию |
|------|----------|--------------|
| `--verbose` | Детальный вывод | `false` |
| `--no-color` | Без цветов | `false` |
| `--jinja-aware` | Поддержка Jinja2 | `true` |
| `--strict` | Строгий режим | `true` |
| `--max-errors <n>` | Лимит ошибок | `50` |
| `-r, --recursive` | Рекурсивно | `false` |
| `-o, --output <fmt>` | Формат вывода | `text` |
| `--performance` | Метрики | `false` |

## Примеры валидных JSON

Смотри `examples/test-valid.json`:
```json
{
  "name": "TestComponent",
  "type": "object",
  "properties": {
    "text": { "type": "string", "default": "Hello" },
    "count": { "type": "integer", "default": 0 }
  }
}
```

## Примеры Jinja шаблонов

Смотри `examples/test-jinja.jinja.json`:
```json
{
  "name": "{{ component_name }}",
  "properties": {
    {% for prop in properties %}
    "{{ prop.name }}": {
      "type": "{{ prop.type }}"
    }{% if not loop.last %},{% endif %}
    {% endfor %}
  }
}
```

## Troubleshooting

### "Cannot find module"
```bash
# Пересборка
npm run build
```

### "File not found"
```bash
# Проверка путей
ls -la examples/
```

### Ошибки компиляции
```bash
# Проверка типов
npm run typecheck
```

## Следующие шаги

1. Исправить ошибки компиляции в `src/core/`, `src/detectors/`, `src/formatters/`
2. Добавить unit тесты
3. Создать интеграцию с VSCode
4. Оптимизировать производительность

## Файлы созданы

- ✅ `/Users/username/Scripts/vscode-validator-v2.3.1/src/index.ts`
- ✅ `/Users/username/Scripts/vscode-validator-v2.3.1/src/main.ts`
- ✅ `/Users/username/Scripts/vscode-validator-v2.3.1/src/cli.ts`
- ✅ Конфигурация (package.json, tsconfig.json, eslint, prettier)
- ✅ Примеры (examples/)
- ✅ Тесты (test-cli.sh)

## Документация

- **README.md** - полная документация
- **IMPLEMENTATION_SUMMARY_v1.0.0.md** - детали реализации
- **QUICK_START_v1.0.0.md** - этот файл
