/**
 * Jinja Parser Usage Examples v1.0.0
 * Примеры использования парсера Jinja2/Java шаблонов
 *
 * @version 1.0.0
 * @author Claude Code (Agent 03)
 * @date 2025-10-05
 */

import JinjaParser, {
  JinjaParseResult,
  exportParseResult,
  isJinjaTemplate
} from './jinja_parser_v1.0.0';

// ============================================================================
// БАЗОВЫЙ ПРИМЕР
// ============================================================================

function basicExample() {
  console.log('=== Базовый пример парсинга Jinja шаблона ===\n');

  const parser = new JinjaParser({
    basePath: '/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/desktop',
    buildSourceMap: true
  });

  const templatePath = '/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java';

  const result = parser.parse(templatePath);

  console.log('Статистика парсинга:');
  console.log(`- Время парсинга: ${result.stats.parseTimeMs} мс`);
  console.log(`- Импортов: ${result.stats.importCount}`);
  console.log(`- Переменных: ${result.stats.variableCount}`);
  console.log(`- Управляющих конструкций: ${result.stats.controlCount}`);
  console.log(`- Размер: ${result.stats.totalSizeBytes} байт`);
  console.log();

  if (result.errors.length > 0) {
    console.log('Ошибки:');
    result.errors.forEach(err => {
      console.log(`  [${err.type}] ${err.message} (${err.filePath}:${err.line}:${err.column})`);
    });
    console.log();
  }

  console.log(`Импорты (${result.imports.length}):`);
  result.imports.forEach(imp => {
    console.log(`  - [${imp.description}] ${imp.path}`);
    console.log(`    Строка ${imp.line}, разрешено: ${imp.resolvedPath}`);
  });
  console.log();
}

// ============================================================================
// ПРИМЕР С ЗНАЧЕНИЯМИ ПО УМОЛЧАНИЮ
// ============================================================================

function defaultValuesExample() {
  console.log('=== Пример с предоставленными значениями по умолчанию ===\n');

  const parser = new JinjaParser({
    defaultValues: {
      averageSalaryState: {
        isAverageSalaryShow: true
      },
      videoBanner: {
        id: 'video-123',
        title: 'Тестовое видео'
      }
    }
  });

  const templatePath = '/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java';

  const result = parser.parse(templatePath);

  console.log('Извлеченный JSON (state секция):');
  console.log(JSON.stringify(result.extractedJson.state, null, 2));
  console.log();
}

// ============================================================================
// ПРИМЕР С ОБРАБОТКОЙ ОШИБОК
// ============================================================================

function errorHandlingExample() {
  console.log('=== Пример обработки ошибок ===\n');

  const parser = new JinjaParser({
    maxImportDepth: 5,
    allowRecursiveImports: false
  });

  const templatePath = '/path/to/nonexistent/template.j2.java';

  const result = parser.parse(templatePath);

  if (result.errors.length > 0) {
    console.log('Обнаружены ошибки:');
    result.errors.forEach((err, idx) => {
      console.log(`\nОшибка ${idx + 1}:`);
      console.log(`  Тип: ${err.type}`);
      console.log(`  Сообщение: ${err.message}`);
      console.log(`  Файл: ${err.filePath}`);
      console.log(`  Позиция: строка ${err.line}, колонка ${err.column}`);
    });
  }
  console.log();
}

// ============================================================================
// ПРИМЕР ЭКСПОРТА РЕЗУЛЬТАТОВ
// ============================================================================

function exportExample() {
  console.log('=== Пример экспорта результатов ===\n');

  const parser = new JinjaParser();

  const templatePath = '/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java';

  const result = parser.parse(templatePath);

  // Экспорт в файл
  const outputPath = '/Users/username/Scripts/validators/v3.0.0/parsed_output_v1.0.0.json';
  exportParseResult(result, outputPath);

  console.log(`Результаты экспортированы в: ${outputPath}`);
  console.log();
}

// ============================================================================
// ПРИМЕР РАБОТЫ С SOURCE MAP
// ============================================================================

function sourceMapExample() {
  console.log('=== Пример работы с Source Map ===\n');

  const parser = new JinjaParser({
    buildSourceMap: true
  });

  const templatePath = '/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java';

  const result = parser.parse(templatePath);

  console.log(`Source Map записей: ${result.sourceMap.length}\n`);

  // Показать первые 10 записей
  const sample = result.sourceMap.slice(0, 10);
  console.log('Примеры маппинга (первые 10):');
  sample.forEach(mapping => {
    console.log(`  ${mapping.sourceFile}:${mapping.jinjaLine}:${mapping.jinjaColumn}`);
    console.log(`    → Тип: ${mapping.tokenType}, JSON Pointer: ${mapping.jsonPointer || '(корень)'}`);
  });
  console.log();
}

// ============================================================================
// ПРИМЕР ПРОВЕРКИ ТИПА ФАЙЛА
// ============================================================================

function fileTypeCheckExample() {
  console.log('=== Пример проверки типа файла ===\n');

  const files = [
    '/path/to/template.j2.java',
    '/path/to/template.jinja.java',
    '/path/to/regular.json',
    '/path/to/script.js'
  ];

  files.forEach(file => {
    const isJinja = isJinjaTemplate(file);
    console.log(`${file}: ${isJinja ? 'Jinja шаблон' : 'НЕ Jinja шаблон'}`);
  });
  console.log();
}

// ============================================================================
// ПРИМЕР ИНТЕГРАЦИИ С ВАЛИДАТОРОМ
// ============================================================================

function validatorIntegrationExample() {
  console.log('=== Пример интеграции с валидатором ===\n');

  const parser = new JinjaParser();

  const templatePath = '/Users/username/Documents/FMS_GIT/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java';

  const result = parser.parse(templatePath);

  if (result.errors.length > 0) {
    console.log('Парсинг не удался, невозможно валидировать');
    return;
  }

  // Здесь можно передать result.extractedJson в валидатор JSON Schema
  console.log('Извлеченный JSON готов для валидации');
  console.log('JSON keys:', Object.keys(result.extractedJson));

  // Пример: валидация с помощью гипотетического валидатора
  // const validationResult = validateAgainstSchema(result.extractedJson, schema);
  console.log();
}

// ============================================================================
// ЗАПУСК ПРИМЕРОВ
// ============================================================================

if (require.main === module) {
  console.log('\n========================================');
  console.log('Jinja Parser Examples v1.0.0');
  console.log('========================================\n');

  try {
    basicExample();
    defaultValuesExample();
    errorHandlingExample();
    exportExample();
    sourceMapExample();
    fileTypeCheckExample();
    validatorIntegrationExample();
  } catch (error) {
    console.error('Ошибка при выполнении примеров:', error);
  }

  console.log('========================================');
  console.log('Примеры завершены');
  console.log('========================================\n');
}

export {
  basicExample,
  defaultValuesExample,
  errorHandlingExample,
  exportExample,
  sourceMapExample,
  fileTypeCheckExample,
  validatorIntegrationExample
};
