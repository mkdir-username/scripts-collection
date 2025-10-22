# SDUI Validator v2.3.1

Модульный валидатор для SDUI JSON схем с поддержкой Jinja2 шаблонов и интеграцией с VSCode.

## Возможности

- **Валидация JSON**: Проверка синтаксиса и структуры JSON файлов
- **Поддержка Jinja2**: Валидация Jinja2 шаблонов (`.j2.json`, `.jinja.json`)
- **Модульная архитектура**: Разделение парсеров, форматтеров и валидаторов
- **Интеграция VSCode**: Автоматическая валидация при сохранении
- **Множественные форматы вывода**: JSON, Markdown, HTML, консольный
- **Производительность**: Оптимизированная работа с большими файлами
- **TypeScript**: Полная типизация и строгая проверка типов

## Требования

- **Node.js**: >= 18.0.0
- **npm**: >= 9.0.0
- **TypeScript**: 5.3+

## Быстрый старт

### Установка

```bash
# Клонировать репозиторий
cd /Users/username/Scripts/vscode-validator-v2.3.1

# Запустить установочный скрипт
chmod +x install.sh
./install.sh
```

Скрипт установки автоматически:
1. Установит зависимости
2. Соберет проект
3. Запустит тесты
4. Создаст глобальную ссылку на CLI
5. Обновит настройки VSCode

### Ручная установка

```bash
# Установить зависимости
npm install

# Собрать проект
npm run build

# Запустить тесты
npm test

# Линковать глобально
npm link
```

## Использование

### CLI

```bash
# Валидация одного файла
sdui-validate path/to/file.json

# Валидация с выводом в JSON
sdui-validate path/to/file.json --format json

# Валидация с детальным выводом
sdui-validate path/to/file.json --verbose
```

### NPM Scripts

```bash
# Сборка проекта
npm run build

# Сборка в watch режиме
npm run build:watch

# Запуск тестов
npm test

# Тесты в watch режиме
npm run test:watch

# Тесты с покрытием
npm run test:coverage

# Проверка кода
npm run lint
npm run lint:fix

# Форматирование
npm run format
npm run format:check

# Проверка типов
npm run typecheck

# Все проверки перед коммитом
npm run precommit
```

### Makefile

```bash
# Показать доступные команды
make help

# Установка и сборка
make setup

# Только сборка
make build

# Тестирование
make test
make test-coverage

# Проверка качества
make verify

# Очистка
make clean

# Все шаги
make all
```

## Архитектура

```
vscode-validator-v2.3.1/
├── src/
│   ├── core/              # Основная логика валидации
│   ├── parsers/           # Парсеры для JSON/Jinja2
│   ├── formatters/        # Форматтеры вывода
│   ├── types/             # TypeScript типы
│   └── utils/             # Утилиты
├── scripts/               # Вспомогательные скрипты
├── dist/                  # Скомпилированный код
└── tests/                 # Тесты
```

### Модули

- **@core**: Валидаторы и основная логика
- **@parsers**: JSON и Jinja2 парсеры
- **@formatters**: Форматтеры результатов (JSON, MD, HTML)
- **@utils**: Утилиты и хелперы
- **@types**: TypeScript определения типов

## Конфигурация

### TypeScript

- `tsconfig.json` - основная конфигурация
- `tsconfig.build.json` - конфигурация для сборки
- Strict mode enabled
- Module resolution: bundler
- Path aliases для модулей

### ESLint

- TypeScript parser
- Строгие правила для типов
- Import ordering
- No console warnings
- Auto-fix поддержка

### Prettier

- Single quotes
- 2 spaces indentation
- Trailing commas (ES5)
- 80 символов на строку

### Jest

- TypeScript support (ts-jest)
- ESM modules
- Coverage threshold: 70%
- Path aliases

## Интеграция с VSCode

Валидатор автоматически интегрируется с VSCode через:

1. **File associations**: `.j2.json`, `.jinja.json` → jsonc
2. **Tasks**: Задачи для валидации
3. **Settings**: Настройки валидатора

Настройки добавляются автоматически при установке через `install.sh`.

## Разработка

### Структура коммита

```bash
# Запуск проверок перед коммитом
npm run precommit

# Или через Make
make precommit
```

### Pre-commit hooks

Автоматически запускаются:
1. Lint + auto-fix
2. Type checking
3. Tests
4. Format checking

### Workflow

1. Создать feature branch
2. Внести изменения
3. Запустить `npm run precommit`
4. Коммитнуть изменения
5. Создать PR

## Тестирование

```bash
# Все тесты
npm test

# С покрытием
npm run test:coverage

# Watch режим
npm run test:watch

# Через Make
make test
make test-coverage
```

### Coverage требования

- Branches: 70%
- Functions: 70%
- Lines: 70%
- Statements: 70%

## Сборка

```bash
# Через npm
npm run build

# Через скрипт
./build.sh

# Через Make
make build
```

Процесс сборки:
1. Проверка prerequisites
2. Установка зависимостей
3. Lint проверка
4. Type checking
5. Очистка dist/
6. Компиляция TypeScript
7. Создание executable
8. Проверка размера бандла

## Деплой

```bash
# Проверка перед публикацией
npm run prepublishOnly

# Публикация (если настроен npm registry)
npm publish
```

## Troubleshooting

### Module resolution errors

Проверьте `tsconfig.json`:
```json
{
  "compilerOptions": {
    "moduleResolution": "bundler"
  }
}
```

### Import errors

Используйте алиасы:
```typescript
import { Parser } from '@parsers/json-parser';
import { Validator } from '@core/validator';
```

### Build errors

```bash
# Очистка и пересборка
make clean
make build
```

## Метрики качества

- ✅ TypeScript strict mode
- ✅ ESLint без ошибок
- ✅ Prettier форматирование
- ✅ Test coverage > 70%
- ✅ Bundle size < 5MB
- ✅ No security vulnerabilities

## Roadmap

- [ ] Плагин система
- [ ] Кастомные правила валидации
- [ ] Language Server Protocol (LSP)
- [ ] Интеграция с CI/CD
- [ ] Performance profiling
- [ ] Incremental validation

## Лицензия

MIT

## Контакты

FMS Team - Server Driven UI
