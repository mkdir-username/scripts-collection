#!/usr/bin/env node
/**
 * VSCode On-Save Validator v1.0.0
 *
 * Автоматическая валидация SDUI контрактов при сохранении в VSCode
 * Используется через emeraldwalk.runonsave расширение
 *
 * Usage:
 *   node vscode-validate-on-save_v1.0.0.js path/to/contract.json
 */

import { readFileSync } from 'fs';
import { basename, relative, join } from 'path';

const PROJECT_ROOT =
  process.env.PROJECT_ROOT ||
  '/Users/username/Documents/front-middle-schema';

// Путь к MCP серверу с валидатором
const MCP_ROOT = '/Users/username/Documents/front-middle-schema/alfa-sdui-mcp';

// Получить путь к файлу из аргументов
const filePath = process.argv[2];

if (!filePath) {
  console.error('❌ ERROR: Путь к файлу не указан');
  console.error('Usage: node vscode-validate-on-save_v1.0.0.js <file>');
  process.exit(1);
}

// Красивый вывод для VSCode Output Panel
function formatOutput(
  filePath: string,
  report: any | null,
  parseError?: string
): void {
  const fileName = basename(filePath);
  const relativePath = relative(PROJECT_ROOT, filePath);

  console.log('━'.repeat(80));
  console.log(`📄 File: ${fileName}`);
  console.log(`📁 Path: ${relativePath}`);
  console.log('━'.repeat(80));

  if (parseError) {
    console.log('');
    console.log('❌ PARSE ERROR');
    console.log('━'.repeat(80));
    console.log(parseError);
    console.log('');
    console.log('💡 Исправьте синтаксические ошибки JSON');
    console.log('━'.repeat(80));
    return;
  }

  if (report.valid) {
    console.log('');
    console.log('✅ CONTRACT VALID');
    console.log('━'.repeat(80));
    console.log(
      `📊 Web Compatibility: ${report.webCompatibility.toFixed(1)}%`
    );

    if (report.dataBindings?.hasBindings) {
      console.log(
        `🔗 Data Bindings: ${report.dataBindings.totalBindings} found`
      );
      console.log(`   Types: state(${report.dataBindings.byType.state}), data(${report.dataBindings.byType.data}), computed(${report.dataBindings.byType.computed})`
      );
    }

    if (report.versions) {
      const versionsList = Object.entries(report.versions.byVersion)
        .map(([v, count]) => `${v}(${count})`)
        .join(', ');
      console.log(`📦 Components: ${report.versions.totalComponents}`);
      console.log(`   Versions: ${versionsList}`);
    }

    if (report.warnings.length > 0) {
      console.log('');
      console.log(`⚠️  WARNINGS (${report.warnings.length})`);
      console.log('━'.repeat(80));
      report.warnings.forEach((warning: string, i: number) => {
        console.log(`${i + 1}. ${warning}`);
      });
    }

    console.log('');
    console.log('✅ Контракт готов к использованию');
  } else {
    console.log('');
    console.log('❌ CONTRACT INVALID');
    console.log('━'.repeat(80));
    console.log(
      `📊 Web Compatibility: ${report.webCompatibility.toFixed(1)}%`
    );
    console.log(`🔴 Errors: ${report.errors.length}`);
    console.log(`🟡 Warnings: ${report.warnings.length}`);

    if (report.errors.length > 0) {
      console.log('');
      console.log(`🔴 ERRORS (${report.errors.length})`);
      console.log('━'.repeat(80));
      report.errors.forEach((error: string, i: number) => {
        console.log(`${i + 1}. ${error}`);
      });
    }

    if (report.warnings.length > 0) {
      console.log('');
      console.log(`⚠️  WARNINGS (${report.warnings.length})`);
      console.log('━'.repeat(80));
      report.warnings.forEach((warning: string, i: number) => {
        console.log(`${i + 1}. ${warning}`);
      });
    }

    console.log('');
    console.log('💡 Исправьте ошибки для использования контракта');
  }

  console.log('━'.repeat(80));
  console.log('');
}

// Основная функция валидации
async function validateFile(filePath: string): Promise<void> {
  const startTime = Date.now();

  try {
    // Динамический импорт модулей
    const { IncrementalValidator } = await import(`file://${join(MCP_ROOT, 'dist/validators/incremental-validator.js')}`);
    const { SDUISchemaIndex } = await import(`file://${join(MCP_ROOT, 'dist/schema-utils/schema-index.js')}`);

    // Прогресс: Начало обработки
    const fileName = basename(filePath);
    console.log('━'.repeat(80));
    console.log(`🔄 PROCESSING: ${fileName}`);
    console.log('━'.repeat(80));

    // Прочитать файл
    console.log('📂 Reading file...');
    const content = readFileSync(filePath, 'utf-8');
    const fileSizeKB = (Buffer.byteLength(content, 'utf-8') / 1024).toFixed(2);
    console.log(`   Size: ${fileSizeKB} KB`);

    // Парсинг JSON
    console.log('🔍 Parsing JSON...');
    let contract;
    try {
      contract = JSON.parse(content);
      console.log('   ✓ JSON parsed successfully');
    } catch (parseError) {
      console.log('   ✗ JSON parse failed');
      console.log('');
      formatOutput(filePath, null, (parseError as Error).message);
      process.exit(1);
    }

    // Инициализация валидатора
    console.log('⚙️  Initializing validator...');
    const schemaIndex = new SDUISchemaIndex(PROJECT_ROOT);
    console.log('   ✓ Schema index loaded');

    const validator = new IncrementalValidator(PROJECT_ROOT, schemaIndex);
    console.log('   ✓ Validator ready');

    // Валидация
    console.log('🔬 Validating contract...');
    const report = validator.validateIncremental(contract);

    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);
    console.log(`   ✓ Validation completed in ${duration}s`);
    console.log('');

    // Вывод результатов
    formatOutput(filePath, report);

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
