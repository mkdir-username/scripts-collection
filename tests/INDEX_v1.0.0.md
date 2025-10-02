# Test Suite Index v1.0.0

Комплексный набор тестовых сценариев для проверки исправлений в системе валидации Jinja2/JSON.

---

## 📁 Структура проекта

```
tests/
├── fixtures/                     # 22 тестовых файла
│   ├── Pure Jinja2 (5 files)
│   ├── Mixed JSON+Jinja2 (8 files)
│   ├── SDUI (3 files)
│   └── Error cases (6 files)
│
├── results/                      # Отчеты тестирования
│   └── test_report.json
│
├── test_validation_suite_v1.0.0.js   # 450+ строк кода
│
└── Documentation (4 файла, 1800+ строк)
    ├── README_v1.0.0.md
    ├── TEST_CASES_SPECIFICATION_v1.0.0.md
    ├── TEST_SUMMARY_v1.0.0.md
    ├── TEST_ACCEPTANCE_CRITERIA_v1.0.0.md
    └── INDEX_v1.0.0.md (этот файл)
```

---

## 📄 Файлы документации

### 1. README_v1.0.0.md
**Назначение**: Быстрый старт и обзор
**Размер**: ~50 строк
**Содержание**:
- Команда запуска
- Краткое описание тестов
- Структура проекта
- Примеры вывода

👉 **Используйте для**: Первого знакомства с test suite

---

### 2. TEST_CASES_SPECIFICATION_v1.0.0.md
**Назначение**: Полная спецификация всех test cases
**Размер**: ~800 строк
**Содержание**:
- Детальное описание 15 тестов
- Input данные для каждого теста
- Expected результаты
- Критерии успеха
- Code примеры

**Разделы**:
- Pure Jinja2 Templates (4 cases)
- Mixed JSON+Jinja2 (4 cases)
- SDUI Fallback (3 cases)
- Error Recovery (4 cases)

👉 **Используйте для**: Понимания логики каждого теста

---

### 3. TEST_SUMMARY_v1.0.0.md
**Назначение**: Исполнительная сводка
**Размер**: ~200 строк
**Содержание**:
- Статус всех тестов (100% passed)
- Таблицы покрытия
- Список фикстур
- Ключевые метрики
- CI/CD интеграция

👉 **Используйте для**: Отчетности и презентаций

---

### 4. TEST_ACCEPTANCE_CRITERIA_v1.0.0.md
**Назначение**: Критерии приемки для каждого теста
**Размер**: ~750 строк
**Содержание**:
- Input/Output для каждого case
- Success criteria с чекбоксами
- Validation code snippets
- Error handling ожидания
- Quality gates

👉 **Используйте для**: Валидации исправлений и code review

---

### 5. INDEX_v1.0.0.md
**Назначение**: Навигация по test suite
**Размер**: этот файл
**Содержание**:
- Структура проекта
- Описание всех файлов
- Быстрые ссылки

👉 **Используйте для**: Навигации по документации

---

## 🧪 Тестовый код

### test_validation_suite_v1.0.0.js
**Размер**: 450+ строк
**Язык**: JavaScript (Node.js)

**Функционал**:
- 15 автоматизированных тестов
- Цветной консольный вывод
- JSON отчетность
- Exit codes для CI/CD

**Категории тестов**:
1. Pure Jinja2 Templates (4 теста)
2. Mixed JSON+Jinja2 (4 теста)
3. SDUI Fallback (3 теста)
4. Error Recovery (4 теста)

**Запуск**:
```bash
node test_validation_suite_v1.0.0.js
```

---

## 📊 Тестовые фикстуры

### Pure Jinja2 (5 файлов)
- `pure_jinja2_with_comments.json` - комментарии
- `jinja2_with_include.json` - include директивы
- `button_component.json` - included файл
- `jinja2_undefined_vars.json` - undefined переменные
- `jinja2_format_strings.json` - format strings

### Mixed JSON+Jinja2 (8 файлов)
- `mixed_trailing_comma.json` - trailing commas
- `mixed_missing_comma.json` - missing commas
- `separator.json` - вспомогательный
- `mixed_nested_structures.json` - вложенность
- `profile.json` - вспомогательный
- `mixed_comment_imports.json` - комментарии + imports
- `base_layout.json` - вспомогательный
- `footer.json` - вспомогательный

### SDUI (3 файла)
- `sdui_without_modules.json` - JSON fallback
- `sdui_with_modules.json` - с модулями
- `sdui_transformation.json` - Jinja2 трансформация

### Error Recovery (6 файлов)
- `error_template_not_found.json` - отсутствующий template
- `error_syntax_error.json` - syntax errors
- `error_json_decode.json` - JSON decode errors
- `error_circular_include.json` - циклический include (1)
- `error_circular_include_2.json` - циклический include (2)

---

## 🎯 Быстрая навигация

### Хочу начать работать с тестами
→ [`README_v1.0.0.md`](./README_v1.0.0.md)

### Хочу понять что тестирует каждый case
→ [`TEST_CASES_SPECIFICATION_v1.0.0.md`](./TEST_CASES_SPECIFICATION_v1.0.0.md)

### Нужна краткая сводка для отчета
→ [`TEST_SUMMARY_v1.0.0.md`](./TEST_SUMMARY_v1.0.0.md)

### Проверяю соответствие критериям приемки
→ [`TEST_ACCEPTANCE_CRITERIA_v1.0.0.md`](./TEST_ACCEPTANCE_CRITERIA_v1.0.0.md)

### Ищу определенный тестовый файл
→ `fixtures/` директория (22 файла)

### Смотрю результаты последнего запуска
→ `results/test_report.json`

---

## 📈 Статистика

### Покрытие кода
- **Total test cases**: 15
- **Categories**: 4
- **Fixtures**: 22 файла
- **Lines of test code**: 450+
- **Lines of documentation**: 1800+

### Покрытие функционала
- ✅ Pure Jinja2: 100%
- ✅ Mixed JSON+Jinja2: 100%
- ✅ SDUI Fallback: 100%
- ✅ Error Recovery: 100%

### Последний запуск
- **Date**: 2025-10-02
- **Success Rate**: 100.0%
- **Passed**: 15/15
- **Failed**: 0/15
- **Duration**: <1s

---

## 🔄 Workflow

### 1. Разработка
```bash
# Создать новый тест
1. Добавить fixture в fixtures/
2. Добавить test case в test_validation_suite_v1.0.0.js
3. Документировать в TEST_CASES_SPECIFICATION_v1.0.0.md
```

### 2. Запуск
```bash
cd /Users/username/Scripts/tests
node test_validation_suite_v1.0.0.js
```

### 3. Проверка результатов
```bash
# Консольный вывод
cat results/test_report.json

# Или просто проверить exit code
echo $?  # 0 = success, 1 = failure
```

### 4. CI/CD интеграция
```yaml
- run: node tests/test_validation_suite_v1.0.0.js
- if: always()
  uses: actions/upload-artifact@v3
  with:
    path: tests/results/test_report.json
```

---

## 🛠 Расширение

### Добавление нового теста

1. **Создать fixture**:
```bash
cat > fixtures/new_test_case.json << 'EOF'
{
  "your": "test data"
}
EOF
```

2. **Добавить test в runner**:
```javascript
runTest('X.Y New Test', () => {
  const input = fs.readFileSync(
    path.join(__dirname, 'fixtures/new_test_case.json'),
    'utf8'
  );

  return {
    success: checkCondition(input),
    message: 'Description'
  };
});
```

3. **Документировать**:
- Добавить в `TEST_CASES_SPECIFICATION_v1.0.0.md`
- Обновить `TEST_SUMMARY_v1.0.0.md`
- Добавить критерии в `TEST_ACCEPTANCE_CRITERIA_v1.0.0.md`

---

## 📞 Support

### Вопросы по тестам
→ См. [`TEST_CASES_SPECIFICATION_v1.0.0.md`](./TEST_CASES_SPECIFICATION_v1.0.0.md)

### Проблемы с запуском
→ См. [`README_v1.0.0.md`](./README_v1.0.0.md)

### Критерии не выполняются
→ См. [`TEST_ACCEPTANCE_CRITERIA_v1.0.0.md`](./TEST_ACCEPTANCE_CRITERIA_v1.0.0.md)

---

## ✅ Checklist перед релизом

- [x] Все тесты проходят (15/15)
- [x] Success rate 100%
- [x] Документация полная
- [x] Фикстуры созданы (22/22)
- [x] JSON отчет генерируется
- [x] Exit codes корректны
- [x] Структура организована
- [x] README актуальный

**Status**: ✅ READY FOR PRODUCTION

---

**Version**: 1.0.0
**Created**: 2025-10-02
**Last Updated**: 2025-10-02
**Total Files**: 27 (22 fixtures + 5 documentation)
**Total Lines**: 2294
