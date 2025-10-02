#!/usr/bin/env node
/**
 * VSCode On-Save Validator v1.1.0
 *
 * Автоматическая валидация SDUI контрактов при сохранении в VSCode
 * Используется через emeraldwalk.runonsave расширение
 *
 * CHANGELOG v1.1.0:
 * - Новая функция formatOutput с использованием validation-formatters
 * - Группировка errors/warnings по компонентам
 * - Прогресс-бар валидации
 * - JSON Pointers и file:// links
 * - Улучшенный дизайн вывода
 *
 * Usage:
 *   node vscode-validate-on-save_v1.1.0.js path/to/contract.json
 */

import { readFileSync } from 'fs';
import { basename, relative, join } from 'path';
import {
  createProgressBar,
  formatSectionHeader,
  formatFileInfo,
  formatValidationStatus,
  formatSummary,
  formatErrorsSection,
  formatWarningsSection,
  formatFooter,
  formatParseError
} from './validation-formatters_v1.0.0.js';

const PROJECT_ROOT =
  process.env.PROJECT_ROOT ||
  '/Users/username/Documents/front-middle-schema';

// Путь к MCP серверу с валидатором
const MCP_ROOT = '/Users/username/Scripts/alfa-sdui-mcp';

// Получить путь к файлу из аргументов
const filePath = process.argv[2];

if (!filePath) {
  console.error('❌ ERROR: Путь к файлу не указан');
  console.error('Usage: node vscode-validate-on-save_v1.1.0.js <file>');
  process.exit(1);
}

/**
 * Красивый вывод для VSCode Output Panel
 * v1.1.0 - с использованием validation-formatters
 */
function formatOutput(filePath, report, parseError, fileSize, duration) {
  const SEPARATOR = '━'.repeat(80);

  // Обработка parse error
  if (parseError) {
    console.log(formatParseError(filePath, PROJECT_ROOT, parseError));
    return;
  }

  // Начало вывода
  console.log(SEPARATOR);

  // FILE INFO секция
  console.log(formatFileInfo(filePath, PROJECT_ROOT, fileSize));

  // STATUS секция
  console.log(formatValidationStatus(report.valid));

  // SUMMARY секция
  console.log(formatSummary(report));

  // ERRORS секция (если есть)
  if (report.errors.length > 0) {
    console.log(formatErrorsSection(report.errors, filePath));
  }

  // WARNINGS секция (если есть)
  if (report.warnings.length > 0) {
    console.log(formatWarningsSection(report.warnings, filePath));
  }

  // FOOTER
  console.log('\n' + formatFooter(duration));
}

/**
 * Отображает прогресс валидации
 */
function showValidationProgress() {
  const steps = [
    { name: '📂 Reading file...', progress: 0.2 },
    { name: '🔍 Parsing JSON...', progress: 0.4 },
    { name: '⚙️  Initializing validator...', progress: 0.6 },
    { name: '🔬 Validating contract...', progress: 0.8 }
  ];

  console.log(formatSectionHeader('PROCESSING'));

  steps.forEach(step => {
    console.log(step.name);
  });

  console.log('');
}

/**
 * Основная функция валидации
 */
async function validateFile(filePath) {
  const startTime = Date.now();

  try {
    // Прогресс: Начало обработки
    showValidationProgress();

    // Шаг 1: Чтение файла
    console.log('📂 Reading file...');
    const content = readFileSync(filePath, 'utf-8');
    const fileSizeKB = (Buffer.byteLength(content, 'utf-8') / 1024).toFixed(2);
    console.log(`   Size: ${fileSizeKB} KB`);
    console.log(`   ${createProgressBar(1, 4)}`);

    // Шаг 2: Парсинг JSON
    console.log('\n🔍 Parsing JSON...');
    let contract;
    try {
      contract = JSON.parse(content);
      console.log('   ✓ JSON parsed successfully');
      console.log(`   ${createProgressBar(2, 4)}`);
    } catch (parseError) {
      console.log('   ✗ JSON parse failed');
      console.log('');
      formatOutput(filePath, null, parseError.message);
      process.exit(1);
    }

    // Динамический импорт модулей
    const { IncrementalValidator } = await import(
      `file://${join(MCP_ROOT, 'dist/validators/incremental-validator.js')}`
    );
    const { SDUISchemaIndex } = await import(
      `file://${join(MCP_ROOT, 'dist/schema-utils/schema-index.js')}`
    );

    // Шаг 3: Инициализация валидатора
    console.log('\n⚙️  Initializing validator...');
    const schemaIndex = new SDUISchemaIndex(PROJECT_ROOT);
    console.log('   ✓ Schema index loaded');

    const validator = new IncrementalValidator(PROJECT_ROOT, schemaIndex);
    console.log('   ✓ Validator ready');
    console.log(`   ${createProgressBar(3, 4)}`);

    // Шаг 4: Валидация
    console.log('\n🔬 Validating contract...');
    const report = validator.validateIncremental(contract);
    console.log('   ✓ Validation completed');
    console.log(`   ${createProgressBar(4, 4)}`);

    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);

    console.log('');

    // Вывод результатов
    formatOutput(filePath, report, undefined, fileSizeKB, duration);

    // Exit code: 0 если валиден, 1 если нет
    process.exit(report.valid ? 0 : 1);
  } catch (error) {
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);

    console.error('━'.repeat(80));
    console.error(`❌ VALIDATION ERROR (after ${duration}s)`);
    console.error('━'.repeat(80));
    console.error(error);
    console.error('━'.repeat(80));
    process.exit(1);
  }
}

// Запуск
console.log(''); // Пустая строка для читаемости в Output
validateFile(filePath);
