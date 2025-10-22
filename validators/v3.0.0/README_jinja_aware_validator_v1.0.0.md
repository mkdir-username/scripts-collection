# Jinja-Aware Validator v1.0.0

**Jinja-Aware Validator** — валидатор Jinja-шаблонов с поддержкой WEB-совместимости, проверки обязательных полей и рекурсивной валидации imports.

## Возможности

- **Извлечение JSON из Jinja-шаблонов** (.j2.java, .jinja.java)
- **WEB-совместимость** — проверка компонентов на поддержку веб-платформы
- **Обязательные поля** — валидация required fields для каждого компонента
- **Рекурсивная валидация imports** — автоматическая проверка всех импортированных файлов
- **Точное мапирование ошибок** — указание номеров строк в исходном Jinja-файле
- **Детальная статистика** — процент WEB-совместимости, количество ошибок по категориям
- **Экспорт результатов** — JSON, консольный вывод с цветами

---

## Установка

```bash
cd /Users/username/Scripts/validators/v3.0.0
npm install
```

---

## Использование

### CLI

```bash
# Базовая валидация
node jinja_aware_validator_v1.0.0.js template.j2.java

# С детальным выводом
VERBOSE=1 node jinja_aware_validator_v1.0.0.js template.j2.java
```

### TypeScript API

```typescript
import { JinjaAwareValidator } from './jinja_aware_validator_v1.0.0.js';

const validator = new JinjaAwareValidator({ verbose: true });

const result = await validator.validate('path/to/template.j2.java', {
  validateImports: true,
  checkWebCompatibility: true,
  checkRequiredFields: true,
  maxImportDepth: 3,
});

// Вывод результатов
validator.printReport(result);

// Экспорт в JSON
const json = validator.exportToJson(result);
console.log(json);
```

---

## Примеры

### Пример 1: Простая валидация

```typescript
import { JinjaAwareValidator } from './jinja_aware_validator_v1.0.0.js';

async function validateTemplate() {
  const validator = new JinjaAwareValidator();

  const result = await validator.validate('payroll_screen.j2.java');

  console.log(`Valid: ${result.valid}`);
  console.log(`Errors: ${result.errors.length}`);
  console.log(`WEB Compatibility: ${result.webCompatibility}%`);
}
```

**Вывод:**

```
═══════════════════════════════════════════════════════════════════════════════
📄 JINJA TEMPLATE VALIDATION v1.0.0
═══════════════════════════════════════════════════════════════════════════════

📁 File: /path/to/payroll_screen.j2.java

📊 Summary:
   Components .............. 5
   WEB Compatible .......... 4
   WEB Incompatible ........ 1
   WEB Compatibility ....... 80%
   Missing Required Fields . 0
   Imports Validated ....... 2

📝 Validation Results:
   Errors .................. 1
   Warnings ................ 0

❌ ERRORS:

1. [ImageView] Component ImageView is not compatible with WEB platform (web: notReleased)
   → /path/to/payroll_screen.j2.java:42:1
   💡 Use a different component or check if there's a WEB-compatible version

═══════════════════════════════════════════════════════════════════════════════
❌ Template has validation errors
═══════════════════════════════════════════════════════════════════════════════
```

---

### Пример 2: Валидация с imports

```typescript
const result = await validator.validate('main.j2.java', {
  validateImports: true,
  maxImportDepth: 5,
});

console.log(`Imports validated: ${result.imports.length}`);

result.imports.forEach(imp => {
  console.log(`- ${imp.path}: ${imp.valid ? 'OK' : 'ERRORS'}`);
  if (!imp.valid) {
    imp.errors.forEach(err => console.log(`  ❌ ${err.message}`));
  }
});
```

**Вывод:**

```
Imports validated: 3
- ./header.j2.java: OK
- ./footer.j2.java: OK
- ./sidebar.j2.java: ERRORS
  ❌ Component IconView is not compatible with WEB platform (web: willNotBeReleased)
```

---

### Пример 3: Проверка обязательных полей

```typescript
const result = await validator.validate('button_template.j2.java', {
  checkRequiredFields: true,
  checkWebCompatibility: false,
});

result.components.forEach(comp => {
  if (comp.requiredFieldsMissing.length > 0) {
    console.log(`${comp.name}: missing ${comp.requiredFieldsMissing.join(', ')}`);
  }
});
```

**Вывод:**

```
ButtonView: missing textContent, actions
TextView: missing textContent
```

---

## Структура результата валидации

```typescript
interface JinjaValidationResult {
  valid: boolean;              // true если нет ошибок
  errors: ValidationError[];   // Массив ошибок с line/column
  warnings: ValidationError[]; // Массив предупреждений

  imports: ImportValidation[]; // Результаты валидации импортов

  webCompatibility: number;    // Процент совместимости (0-100)

  components: ComponentInfo[]; // Информация о найденных компонентах

  metadata: {
    templatePath: string;
    totalComponents: number;
    compatibleComponents: number;
    incompatibleComponents: number;
    missingRequiredFields: number;
    importsValidated: number;
  };
}
```

---

## ValidationError

```typescript
interface ValidationError {
  source: 'web-compat' | 'required-fields' | 'custom';
  severity: 'error' | 'warning' | 'info';

  filePath: string;   // Путь к Jinja-файлу
  line?: number;      // Номер строки в Jinja-файле
  column?: number;    // Колонка в Jinja-файле
  path?: string;      // JSON path (components[0].textContent)

  component?: string; // Имя компонента (ButtonView, IconView)
  version?: string;   // Версия компонента (v1, v2)

  message: string;    // Текст ошибки
  code?: string;      // Код ошибки (WEB_INCOMPATIBLE_COMPONENT)
  suggestion?: string; // Подсказка по исправлению
}
```

---

## Опции валидации

```typescript
interface JinjaValidationOptions {
  validateImports?: boolean;      // Валидировать импорты (default: true)
  checkWebCompatibility?: boolean; // Проверять WEB-совместимость (default: true)
  checkRequiredFields?: boolean;  // Проверять обязательные поля (default: true)
  maxImportDepth?: number;        // Максимальная глубина импортов (default: 5)
  verbose?: boolean;              // Подробный вывод (default: false)
}
```

---

## Интеграция с Unified Reporter

Jinja-Aware Validator использует **Unified Reporter v3.0.0** для форматирования ошибок.

```typescript
import { UnifiedReporter } from './unified_reporter_v3.0.0.js';

const validator = new JinjaAwareValidator();
const result = await validator.validate('template.j2.java');

// Создаем отчет через UnifiedReporter
const reporter = new UnifiedReporter({ groupBy: 'component' });
const report = reporter.createReport(
  result.metadata.templatePath,
  result.errors,
  result.metadata
);

reporter.print(report);
```

---

## Интеграция с WEB Validator

Для проверки WEB-совместимости используется **SDUI Web Validator v3.0.0**:

```typescript
class WebCompatibilityChecker {
  async checkComponent(componentName: string): Promise<{
    compatible: boolean;
    reason: string;
  }> {
    // Поиск схемы в FMS_GIT/SDUI
    const schema = await this.findComponentSchema(componentName);

    // Проверка releaseVersion.web
    if (schema.releaseVersion.web === 'notReleased') {
      return { compatible: false, reason: 'web: notReleased' };
    }

    return { compatible: true, reason: 'released' };
  }
}
```

---

## Обработка Jinja-шаблонов

### Поддерживаемые конструкции

- `{% import "file.j2.java" as var %}` — импорты
- `{{ variable }}` — переменные (заменяются на заглушки)
- `{# comment #}` — комментарии (удаляются)
- `{% if/for/block %}` — управляющие конструкции (пропускаются)

### Пример шаблона

```jinja
{% import "./header.j2.java" as header %}

{
  "type": "StackView",
  "elements": [
    {{ header }},
    {
      "type": "ButtonView",
      "textContent": {
        "kind": "plain",
        "text": "{{ buttonText }}"
      },
      "actions": [
        {
          "type": "HttpAction",
          "url": "{{ apiUrl }}"
        }
      ]
    }
  ]
}
```

### Извлеченный JSON

```json
{
  "type": "StackView",
  "elements": [
    "{{header}}",
    {
      "type": "ButtonView",
      "textContent": {
        "kind": "plain",
        "text": "{{buttonText}}"
      },
      "actions": [
        {
          "type": "HttpAction",
          "url": "{{apiUrl}}"
        }
      ]
    }
  ]
}
```

---

## Мапирование ошибок

Все ошибки мапятся на исходные позиции в Jinja-файле:

```typescript
interface SourceMapping {
  jsonPointer: string;   // "/elements/1/textContent"
  jsonPath: string;      // "elements[1].textContent"
  templateLine: number;  // 12
  templateColumn: number; // 7
  extractedLine: number; // 8
}
```

**Пример:**

Ошибка в JSON:
```
Path: elements[1].textContent
```

Мапится в Jinja:
```
→ template.j2.java:12:7
```

---

## CLI Commands

### Базовая валидация
```bash
node jinja_aware_validator_v1.0.0.js template.j2.java
```

### Валидация без imports
```bash
node jinja_aware_validator_v1.0.0.js --no-imports template.j2.java
```

### Валидация без WEB-проверки
```bash
node jinja_aware_validator_v1.0.0.js --no-web template.j2.java
```

### Экспорт в JSON
```bash
node jinja_aware_validator_v1.0.0.js --export-json result.json template.j2.java
```

---

## Exit Codes

- **0** — Валидация успешна (нет ошибок)
- **1** — Валидация провалилась (есть ошибки)

---

## Обязательные поля по компонентам

```typescript
const requiredFields: Record<string, string[]> = {
  ButtonView: ['textContent', 'actions'],
  TextView: ['textContent'],
  IconView: ['icon'],
  ImageView: ['imageContent'],
  StackView: ['elements'],
};
```

---

## Troubleshooting

### Проблема: "Import file not found"

**Решение:**
- Проверьте путь к импортируемому файлу
- Используйте относительные пути (`./file.j2.java`)
- Убедитесь, что файл существует

### Проблема: "Failed to parse extracted JSON"

**Решение:**
- Проверьте синтаксис JSON в шаблоне
- Убедитесь, что все скобки закрыты
- Проверьте, что переменные Jinja корректно заменяются

### Проблема: "Component X is not compatible with WEB"

**Решение:**
- Проверьте `releaseVersion.web` в схеме компонента
- Используйте альтернативный компонент
- Обновите компонент до WEB-совместимой версии

---

## Best Practices

1. **Всегда валидируйте перед коммитом**
   ```bash
   node jinja_aware_validator_v1.0.0.js template.j2.java
   ```

2. **Используйте максимальную глубину импортов**
   ```typescript
   { maxImportDepth: 10 }
   ```

3. **Проверяйте WEB-совместимость для веб-проектов**
   ```typescript
   { checkWebCompatibility: true }
   ```

4. **Экспортируйте результаты для анализа**
   ```typescript
   const json = validator.exportToJson(result);
   fs.writeFileSync('validation_result.json', json);
   ```

---

## Интеграция с Pre-commit Hooks

### .pre-commit-config.yaml

```yaml
- repo: local
  hooks:
    - id: jinja-aware-validator
      name: Jinja Template Validator
      entry: node /Users/username/Scripts/validators/v3.0.0/jinja_aware_validator_v1.0.0.js
      language: node
      files: \.(j2\.java|jinja\.java)$
      pass_filenames: true
```

---

## Changelog

### v1.0.0 (2025-10-05)
- Начальная реализация
- Поддержка WEB-совместимости
- Проверка обязательных полей
- Рекурсивная валидация imports
- Мапирование ошибок на Jinja source locations
- Интеграция с UnifiedReporter v3.0.0

---

## Автор

**Claude Code CLI** (Agent 04: Jinja-Aware Validator Implementation)

---

## Лицензия

Internal tool for FMS project (Альфа-Банк)

---

## Ссылки

- [Unified Reporter v3.0.0](./README_unified_reporter_v3.0.0.md)
- [SDUI Web Validator v3.0.0](./sdui_web_validator_v3.0.0.py)
- [FMS Repository](https://bitbucket.moscow.alfaintra.net/projects/BDUI/repos/front-middle-schema)
