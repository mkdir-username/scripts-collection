# Интеграция SDUI Validator в FMS проект

## Обзор

Этот документ описывает процесс интеграции модульного валидатора в основной FMS репозиторий.

## Предварительные требования

- Node.js >= 18.0.0
- npm >= 9.0.0
- Python 3.13+ (для интеграции с существующими валидаторами)
- VSCode (рекомендуется)

## Шаг 1: Установка валидатора

### Локальная установка

```bash
cd /Users/username/Scripts/vscode-validator-v2.3.1

# Запустить установочный скрипт
./install.sh

# Или вручную
npm install
npm run build
npm link
```

### Проверка установки

```bash
# Проверка CLI
sdui-validate --version

# Тестовая валидация
sdui-validate /path/to/test.json
```

## Шаг 2: Интеграция с FMS

### 2.1 Добавление в package.json FMS

Добавить в `/Users/username/Documents/FMS_GIT/package.json`:

```json
{
  "scripts": {
    "validate:vscode": "sdui-validate",
    "validate:all": "npm run validate:vscode && npm run validate:python"
  },
  "devDependencies": {
    "vscode-sdui-validator": "file:../Scripts/vscode-validator-v2.3.1"
  }
}
```

### 2.2 Обновление .pre-commit-config.yaml

Добавить в `/Users/username/Documents/FMS_GIT/.pre-commit-config.yaml`:

```yaml
repos:
  # Существующие hooks...

  - repo: local
    hooks:
      - id: vscode-validator
        name: SDUI VSCode Validator
        entry: sdui-validate
        language: node
        types: [json]
        files: \.(json|j2\.json|jinja\.json)$
        pass_filenames: true
```

### 2.3 Настройка VSCode

Обновить `/Users/username/Documents/FMS_GIT/.vscode/settings.json`:

```json
{
  "sdui.validator.enabled": true,
  "sdui.validator.validateOnSave": true,
  "sdui.validator.excludePatterns": [
    "**/node_modules/**",
    "**/dist/**",
    "**/.tmp/**"
  ],
  "files.associations": {
    "*.j2.json": "jsonc",
    "*.jinja.json": "jsonc"
  }
}
```

### 2.4 Добавление задач VSCode

Обновить `/Users/username/Documents/FMS_GIT/.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "type": "npm",
      "script": "validate:vscode",
      "problemMatcher": [],
      "label": "Validate with VSCode Validator",
      "detail": "Run modular SDUI validator"
    },
    {
      "type": "shell",
      "command": "sdui-validate",
      "args": ["${file}"],
      "problemMatcher": [],
      "label": "Validate Current File",
      "detail": "Validate currently open file"
    }
  ]
}
```

## Шаг 3: Создание симлинка

```bash
cd /Users/username/Documents/FMS_GIT

# Создать симлинк на валидатор
ln -s /Users/username/Scripts/vscode-validator-v2.3.1 ./validators/vscode-validator

# Или добавить как git submodule
git submodule add /Users/username/Scripts/vscode-validator-v2.3.1 validators/vscode-validator
```

## Шаг 4: Интеграция с Python валидаторами

### 4.1 Создать мост между валидаторами

Создать `/Users/username/Documents/FMS_GIT/src/validators_bridge_v1.0.0.py`:

```python
#!/usr/bin/env python3
"""
Validators Bridge v1.0.0
Мост между Python и TypeScript валидаторами
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

class ValidatorsBridge:
    """Объединяет результаты Python и TypeScript валидаторов"""

    def __init__(self, vscode_validator_path: str):
        self.vscode_validator = vscode_validator_path

    def validate_with_vscode(self, file_path: str) -> Dict:
        """Запуск VSCode валидатора"""
        try:
            result = subprocess.run(
                ['node', self.vscode_validator, file_path],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.stdout:
                return json.loads(result.stdout)
            return {"errors": [], "warnings": []}

        except subprocess.TimeoutExpired:
            return {"error": "Validation timeout"}
        except Exception as e:
            return {"error": str(e)}

    def validate_with_python(self, file_path: str) -> Dict:
        """Запуск Python валидатора"""
        # Интеграция с существующим sdui_web_validator_v3_0_0.py
        from src.sdui_web_validator_v3_0_0 import validate_file

        return validate_file(file_path)

    def validate_combined(self, file_path: str) -> Dict:
        """Комбинированная валидация"""
        vscode_result = self.validate_with_vscode(file_path)
        python_result = self.validate_with_python(file_path)

        return {
            "file": file_path,
            "vscode_validator": vscode_result,
            "python_validator": python_result,
            "combined_status": self._merge_results(vscode_result, python_result)
        }

    def _merge_results(self, vscode: Dict, python: Dict) -> str:
        """Объединение результатов"""
        if "error" in vscode or "error" in python:
            return "ERROR"

        errors = (
            vscode.get("errors", []) +
            python.get("errors", [])
        )

        return "FAIL" if errors else "PASS"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validators_bridge_v1.0.0.py <file.json>")
        sys.exit(1)

    bridge = ValidatorsBridge(
        vscode_validator_path="/Users/username/Scripts/vscode-validator-v2.3.1/dist/cli.js"
    )

    result = bridge.validate_combined(sys.argv[1])
    print(json.dumps(result, indent=2, ensure_ascii=False))
```

### 4.2 Обновить validate.sh

Обновить `/Users/username/Documents/FMS_GIT/validate.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

FILE="$1"

echo "Running combined validation..."

# Python валидатор
echo "1. Python validator..."
python3 src/sdui_web_validator_v3_0_0.py "$FILE"

# VSCode валидатор
echo "2. VSCode validator..."
sdui-validate "$FILE"

# Объединенная валидация
echo "3. Combined validation..."
python3 src/validators_bridge_v1.0.0.py "$FILE"

echo "Validation completed"
```

## Шаг 5: CI/CD интеграция

### 5.1 GitHub Actions

Создать `/Users/username/Documents/FMS_GIT/.github/workflows/validate-schemas.yml`:

```yaml
name: Validate SDUI Schemas

on:
  push:
    paths:
      - '**/*.json'
      - '**/*.j2.json'
      - '**/*.jinja.json'
  pull_request:
    paths:
      - '**/*.json'
      - '**/*.j2.json'
      - '**/*.jinja.json'

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20.x'

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'

      - name: Install VSCode Validator
        run: |
          cd validators/vscode-validator
          npm install
          npm run build
          npm link

      - name: Install Python dependencies
        run: |
          pip install -r requirements.txt

      - name: Validate schemas
        run: |
          npm run validate:all
```

### 5.2 Pre-commit integration

```bash
cd /Users/username/Documents/FMS_GIT

# Установить pre-commit hooks
pre-commit install

# Запустить на всех файлах
pre-commit run --all-files
```

## Шаг 6: Тестирование интеграции

### 6.1 Тестовый файл

Создать `/Users/username/Documents/FMS_GIT/.tmp/test_integration_v1.0.0.json`:

```json
{
  "type": "object",
  "component": "ButtonView",
  "properties": {
    "text": "Test Button"
  }
}
```

### 6.2 Запуск валидации

```bash
# Через CLI
sdui-validate .tmp/test_integration_v1.0.0.json

# Через npm
npm run validate:vscode .tmp/test_integration_v1.0.0.json

# Через Python мост
python3 src/validators_bridge_v1.0.0.py .tmp/test_integration_v1.0.0.json

# Через Makefile FMS
make validate
```

## Шаг 7: Документация

### 7.1 Обновить CLAUDE.md

Добавить в `/Users/username/Documents/FMS_GIT/CLAUDE.md`:

```markdown
### TypeScript валидатор

Модульный TypeScript валидатор с поддержкой Jinja2:

\`\`\`bash
# CLI использование
sdui-validate <file.json>

# NPM скрипты
npm run validate:vscode <file.json>

# Комбинированная валидация
python3 src/validators_bridge_v1.0.0.py <file.json>
\`\`\`

**Возможности:**
- Валидация JSON синтаксиса
- Поддержка Jinja2 шаблонов (.j2.json, .jinja.json)
- Модульная архитектура
- Множественные форматы вывода
- Интеграция с VSCode

**Расположение:** `validators/vscode-validator/`
```

## Шаг 8: Мониторинг и метрики

### 8.1 Создать скрипт сбора метрик

Создать `/Users/username/Documents/FMS_GIT/scripts/validation_metrics_v1.0.0.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

echo "Collecting validation metrics..."

# Количество файлов
TOTAL_FILES=$(find . -name "*.json" | wc -l)
echo "Total JSON files: $TOTAL_FILES"

# Валидация через VSCode валидатор
VSCODE_ERRORS=0
VSCODE_SUCCESS=0

for file in $(find . -name "*.json" -not -path "*/node_modules/*"); do
    if sdui-validate "$file" > /dev/null 2>&1; then
        VSCODE_SUCCESS=$((VSCODE_SUCCESS + 1))
    else
        VSCODE_ERRORS=$((VSCODE_ERRORS + 1))
    fi
done

echo "VSCode Validator: $VSCODE_SUCCESS passed, $VSCODE_ERRORS failed"

# Результаты в JSON
cat > validation_metrics.json <<EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "total_files": $TOTAL_FILES,
  "vscode_validator": {
    "success": $VSCODE_SUCCESS,
    "errors": $VSCODE_ERRORS
  }
}
EOF

echo "Metrics saved to validation_metrics.json"
```

## Troubleshooting

### Проблема: Command not found: sdui-validate

**Решение:**
```bash
cd /Users/username/Scripts/vscode-validator-v2.3.1
npm link
```

### Проблема: Module resolution errors

**Решение:**
Проверить tsconfig.json:
```json
{
  "compilerOptions": {
    "moduleResolution": "bundler"
  }
}
```

### Проблема: Pre-commit hook fails

**Решение:**
```bash
# Проверить установку
which sdui-validate

# Переустановить hooks
pre-commit uninstall
pre-commit install
```

## Следующие шаги

1. ✅ Установка валидатора
2. ✅ Интеграция с FMS
3. ✅ Настройка CI/CD
4. ⏳ Создание документации команды
5. ⏳ Training сессии для команды
6. ⏳ Миграция с Python валидаторов

## Контакты

- DevOps: Вопросы по CI/CD интеграции
- FMS Team: Вопросы по схемам SDUI
- #server_driven_ui: Общие вопросы

## Дополнительные ресурсы

- [README.md](./README.md) - Основная документация
- [CLAUDE.md](/Users/username/Documents/FMS_GIT/CLAUDE.md) - FMS документация
- [GitHub Workflows](.github/workflows/) - CI/CD примеры
