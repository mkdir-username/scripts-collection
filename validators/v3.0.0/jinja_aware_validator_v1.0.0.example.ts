/**
 * Jinja-Aware Validator v1.0.0 - Examples
 *
 * Примеры использования Jinja-Aware Validator
 *
 * @author Claude Code CLI
 * @version 1.0.0
 * @date 2025-10-05
 */

import { JinjaAwareValidator } from './jinja_aware_validator_v1.0.0.js';
import { writeFile } from 'fs/promises';

// ============================================================================
// ПРИМЕР 1: БАЗОВАЯ ВАЛИДАЦИЯ
// ============================================================================

async function example1_basicValidation() {
  console.log('\n' + '='.repeat(80));
  console.log('ПРИМЕР 1: Базовая валидация Jinja-шаблона');
  console.log('='.repeat(80) + '\n');

  const validator = new JinjaAwareValidator({ verbose: true });

  // Валидация шаблона
  const result = await validator.validate(
    '/Users/username/Documents/FMS_GIT/metaschema/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java',
    {
      validateImports: true,
      checkWebCompatibility: true,
      checkRequiredFields: true,
    }
  );

  // Вывод результатов
  validator.printReport(result);

  console.log('\n✅ Пример 1 завершен\n');
}

// ============================================================================
// ПРИМЕР 2: ВАЛИДАЦИЯ С АНАЛИЗОМ КОМПОНЕНТОВ
// ============================================================================

async function example2_componentAnalysis() {
  console.log('\n' + '='.repeat(80));
  console.log('ПРИМЕР 2: Анализ компонентов в шаблоне');
  console.log('='.repeat(80) + '\n');

  const validator = new JinjaAwareValidator();

  const result = await validator.validate(
    '/Users/username/Documents/FMS_GIT/metaschema/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java'
  );

  console.log('📊 АНАЛИЗ КОМПОНЕНТОВ:\n');

  // Группируем компоненты по WEB-совместимости
  const compatible = result.components.filter(c => c.webCompatible);
  const incompatible = result.components.filter(c => !c.webCompatible);

  console.log(`✅ WEB-совместимые (${compatible.length}):`);
  compatible.forEach(comp => {
    console.log(`   - ${comp.name} @ ${comp.path}`);
  });

  console.log(`\n❌ WEB-несовместимые (${incompatible.length}):`);
  incompatible.forEach(comp => {
    console.log(`   - ${comp.name} @ ${comp.path} (line ${comp.line})`);
  });

  console.log(`\n⚠️  Компоненты с отсутствующими полями:`);
  result.components
    .filter(c => c.requiredFieldsMissing.length > 0)
    .forEach(comp => {
      console.log(`   - ${comp.name}: ${comp.requiredFieldsMissing.join(', ')}`);
    });

  console.log('\n✅ Пример 2 завершен\n');
}

// ============================================================================
// ПРИМЕР 3: ВАЛИДАЦИЯ IMPORTS
// ============================================================================

async function example3_importValidation() {
  console.log('\n' + '='.repeat(80));
  console.log('ПРИМЕР 3: Рекурсивная валидация imports');
  console.log('='.repeat(80) + '\n');

  const validator = new JinjaAwareValidator();

  const result = await validator.validate(
    '/Users/username/Documents/FMS_GIT/metaschema/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java',
    {
      validateImports: true,
      maxImportDepth: 5,
    }
  );

  console.log('📦 АНАЛИЗ IMPORTS:\n');

  if (result.imports.length === 0) {
    console.log('   Импорты не найдены');
  } else {
    result.imports.forEach((imp, idx) => {
      const status = imp.valid ? '✅' : '❌';
      const recursive = imp.recursive ? '(recursive)' : '';

      console.log(`${idx + 1}. ${status} ${imp.path} ${recursive}`);

      if (!imp.valid) {
        imp.errors.forEach(err => {
          console.log(`   → ${err.message}`);
        });
      }
    });
  }

  console.log('\n✅ Пример 3 завершен\n');
}

// ============================================================================
// ПРИМЕР 4: ЭКСПОРТ РЕЗУЛЬТАТОВ В JSON
// ============================================================================

async function example4_exportJson() {
  console.log('\n' + '='.repeat(80));
  console.log('ПРИМЕР 4: Экспорт результатов в JSON');
  console.log('='.repeat(80) + '\n');

  const validator = new JinjaAwareValidator();

  const result = await validator.validate(
    '/Users/username/Documents/FMS_GIT/metaschema/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java'
  );

  // Экспорт в JSON
  const json = validator.exportToJson(result);

  // Сохранение в файл
  const outputPath = '/Users/username/Scripts/validators/v3.0.0/.tmp/validation_result_v1.0.0.json';
  await writeFile(outputPath, json, 'utf-8');

  console.log(`✅ Результаты экспортированы в: ${outputPath}\n`);

  // Вывод краткой статистики
  const parsed = JSON.parse(json);
  console.log('📊 СТАТИСТИКА:');
  console.log(`   Valid: ${parsed.valid}`);
  console.log(`   Errors: ${parsed.errors.length}`);
  console.log(`   Warnings: ${parsed.warnings.length}`);
  console.log(`   Components: ${parsed.components.length}`);
  console.log(`   WEB Compatibility: ${parsed.webCompatibility}%`);

  console.log('\n✅ Пример 4 завершен\n');
}

// ============================================================================
// ПРИМЕР 5: ОБРАБОТКА ОШИБОК
// ============================================================================

async function example5_errorHandling() {
  console.log('\n' + '='.repeat(80));
  console.log('ПРИМЕР 5: Обработка ошибок валидации');
  console.log('='.repeat(80) + '\n');

  const validator = new JinjaAwareValidator();

  try {
    const result = await validator.validate(
      '/Users/username/Documents/FMS_GIT/metaschema/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java'
    );

    // Группировка ошибок по источникам
    const errorsBySource: Record<string, typeof result.errors> = {};

    result.errors.forEach(error => {
      if (!errorsBySource[error.source]) {
        errorsBySource[error.source] = [];
      }
      errorsBySource[error.source].push(error);
    });

    console.log('📋 ОШИБКИ ПО ИСТОЧНИКАМ:\n');

    for (const [source, errors] of Object.entries(errorsBySource)) {
      console.log(`${source.toUpperCase()} (${errors.length}):`);

      errors.forEach((err, idx) => {
        console.log(`  ${idx + 1}. ${err.message}`);
        if (err.line) {
          console.log(`     → ${err.filePath}:${err.line}:${err.column || 1}`);
        }
        if (err.suggestion) {
          console.log(`     💡 ${err.suggestion}`);
        }
        console.log();
      });
    }

    // Группировка по компонентам
    const errorsByComponent: Record<string, typeof result.errors> = {};

    result.errors.forEach(error => {
      const key = error.component || 'General';
      if (!errorsByComponent[key]) {
        errorsByComponent[key] = [];
      }
      errorsByComponent[key].push(error);
    });

    console.log('📦 ОШИБКИ ПО КОМПОНЕНТАМ:\n');

    for (const [component, errors] of Object.entries(errorsByComponent)) {
      console.log(`${component} (${errors.length}):`);
      errors.forEach((err, idx) => {
        console.log(`  ${idx + 1}. ${err.message}`);
      });
      console.log();
    }

  } catch (error) {
    console.error(`❌ Ошибка валидации: ${error}`);
  }

  console.log('\n✅ Пример 5 завершен\n');
}

// ============================================================================
// ПРИМЕР 6: КАСТОМНЫЕ ОПЦИИ ВАЛИДАЦИИ
// ============================================================================

async function example6_customOptions() {
  console.log('\n' + '='.repeat(80));
  console.log('ПРИМЕР 6: Кастомные опции валидации');
  console.log('='.repeat(80) + '\n');

  const validator = new JinjaAwareValidator();

  // Валидация только WEB-совместимости (без imports и required fields)
  console.log('🔍 Валидация 1: Только WEB-совместимость\n');

  const result1 = await validator.validate(
    '/Users/username/Documents/FMS_GIT/metaschema/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java',
    {
      validateImports: false,
      checkWebCompatibility: true,
      checkRequiredFields: false,
    }
  );

  console.log(`   Errors: ${result1.errors.length}`);
  console.log(`   WEB Compatibility: ${result1.webCompatibility}%\n`);

  // Валидация только required fields
  console.log('🔍 Валидация 2: Только обязательные поля\n');

  const result2 = await validator.validate(
    '/Users/username/Documents/FMS_GIT/metaschema/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java',
    {
      validateImports: false,
      checkWebCompatibility: false,
      checkRequiredFields: true,
    }
  );

  console.log(`   Errors: ${result2.errors.length}`);
  console.log(`   Missing Fields: ${result2.metadata.missingRequiredFields}\n`);

  // Полная валидация с большой глубиной imports
  console.log('🔍 Валидация 3: Полная валидация с глубокими imports\n');

  const result3 = await validator.validate(
    '/Users/username/Documents/FMS_GIT/metaschema/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java',
    {
      validateImports: true,
      checkWebCompatibility: true,
      checkRequiredFields: true,
      maxImportDepth: 10,
    }
  );

  console.log(`   Errors: ${result3.errors.length}`);
  console.log(`   Imports Validated: ${result3.metadata.importsValidated}`);
  console.log(`   WEB Compatibility: ${result3.webCompatibility}%\n`);

  console.log('\n✅ Пример 6 завершен\n');
}

// ============================================================================
// ПРИМЕР 7: BATCH VALIDATION
// ============================================================================

async function example7_batchValidation() {
  console.log('\n' + '='.repeat(80));
  console.log('ПРИМЕР 7: Batch валидация нескольких шаблонов');
  console.log('='.repeat(80) + '\n');

  const validator = new JinjaAwareValidator();

  const templates = [
    '/Users/username/Documents/FMS_GIT/metaschema/_JSON/WEB/payroll/1.0_main_screen/desktop/[JJ_PC]_1.0_main_screen.j2.java',
    // Добавьте другие шаблоны здесь
  ];

  const results = await Promise.all(
    templates.map(async (templatePath) => {
      try {
        return await validator.validate(templatePath);
      } catch (error) {
        return {
          valid: false,
          errors: [{
            source: 'custom' as const,
            severity: 'error' as const,
            filePath: templatePath,
            message: `Failed to validate: ${error}`,
          }],
          warnings: [],
          imports: [],
          webCompatibility: 0,
          components: [],
          metadata: {
            templatePath,
            totalComponents: 0,
            compatibleComponents: 0,
            incompatibleComponents: 0,
            missingRequiredFields: 0,
            importsValidated: 0,
          },
        };
      }
    })
  );

  console.log('📊 BATCH VALIDATION RESULTS:\n');

  results.forEach((result, idx) => {
    const status = result.valid ? '✅' : '❌';
    console.log(`${idx + 1}. ${status} ${result.metadata.templatePath}`);
    console.log(`   Errors: ${result.errors.length}`);
    console.log(`   WEB Compatibility: ${result.webCompatibility}%`);
    console.log();
  });

  const totalErrors = results.reduce((sum, r) => sum + r.errors.length, 0);
  const avgCompatibility = results.reduce((sum, r) => sum + r.webCompatibility, 0) / results.length;

  console.log('📈 ИТОГИ:');
  console.log(`   Всего шаблонов: ${results.length}`);
  console.log(`   Валидных: ${results.filter(r => r.valid).length}`);
  console.log(`   С ошибками: ${results.filter(r => !r.valid).length}`);
  console.log(`   Всего ошибок: ${totalErrors}`);
  console.log(`   Средняя WEB-совместимость: ${avgCompatibility.toFixed(1)}%`);

  console.log('\n✅ Пример 7 завершен\n');
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log('\n' + '═'.repeat(80));
  console.log('JINJA-AWARE VALIDATOR v1.0.0 - ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ');
  console.log('═'.repeat(80));

  const examples = [
    { name: 'Базовая валидация', fn: example1_basicValidation },
    { name: 'Анализ компонентов', fn: example2_componentAnalysis },
    { name: 'Валидация imports', fn: example3_importValidation },
    { name: 'Экспорт в JSON', fn: example4_exportJson },
    { name: 'Обработка ошибок', fn: example5_errorHandling },
    { name: 'Кастомные опции', fn: example6_customOptions },
    { name: 'Batch валидация', fn: example7_batchValidation },
  ];

  // Запуск всех примеров
  for (let i = 0; i < examples.length; i++) {
    try {
      await examples[i].fn();
    } catch (error) {
      console.error(`\n❌ Ошибка в примере ${i + 1}: ${error}\n`);
    }
  }

  console.log('\n' + '═'.repeat(80));
  console.log('✅ ВСЕ ПРИМЕРЫ ЗАВЕРШЕНЫ');
  console.log('═'.repeat(80) + '\n');
}

// Запуск
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export {
  example1_basicValidation,
  example2_componentAnalysis,
  example3_importValidation,
  example4_exportJson,
  example5_errorHandling,
  example6_customOptions,
  example7_batchValidation,
};
