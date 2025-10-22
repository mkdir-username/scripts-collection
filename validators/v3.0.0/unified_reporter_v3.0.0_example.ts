/**
 * Unified Reporter v3.0.0 - Usage Examples
 *
 * Примеры использования унифицированного репортера ошибок
 */

import {
  UnifiedReporter,
  ValidationError,
  ErrorConverter,
  ReporterConfig,
} from './unified_reporter_v3.0.0';

// ============================================================================
// ПРИМЕР 1: Базовое использование
// ============================================================================

async function example1_BasicUsage() {
  console.log('='.repeat(80));
  console.log('EXAMPLE 1: Basic Usage');
  console.log('='.repeat(80));
  console.log('');

  // Создаем репортер с конфигурацией по умолчанию
  const reporter = new UnifiedReporter();

  // Создаем массив ошибок
  const errors: ValidationError[] = [
    {
      source: 'metaschema',
      severity: 'error',
      filePath: '/path/to/ButtonView.json',
      path: 'properties.title',
      message: 'Missing required field "title"',
      code: 'MISSING_REQUIRED_FIELD',
      component: 'ButtonView',
      version: 'v2',
      suggestion: 'Add "title" property with StateAware<string> value',
    },
    {
      source: 'stateaware',
      severity: 'warning',
      filePath: '/path/to/ButtonView.json',
      path: 'properties.backgroundColor',
      message: 'Incomplete Control pattern - missing required field',
      code: 'STATEAWARE_PATTERN_ERROR',
      component: 'ButtonView',
      metadata: {
        pattern: 'control',
        missingFields: ['defaultValue'],
      },
    },
  ];

  // Создаем отчет
  const report = reporter.createReport('/path/to/ButtonView.json', errors);

  // Выводим в консоль
  reporter.print(report);

  // Экспортируем в JSON
  const jsonOutput = await reporter.export(report, 'json');
  console.log('JSON Export:');
  console.log(jsonOutput);
  console.log('');
}

// ============================================================================
// ПРИМЕР 2: Интеграция с Ruby валидатором
// ============================================================================

async function example2_RubyIntegration() {
  console.log('='.repeat(80));
  console.log('EXAMPLE 2: Ruby Validator Integration');
  console.log('='.repeat(80));
  console.log('');

  const reporter = new UnifiedReporter({
    groupBy: 'source',
    showJsonPointer: false,
  });

  // Симулируем вывод Ruby валидатора
  const rubyOutput = [
    'SDUI/components/ButtonView/v2/ButtonView.json: invalid_schema: Missing required field "title"',
    'SDUI/components/IconView/v1/IconView.json: unreferenced_schema: Schema not referenced anywhere',
    'SDUI/atoms/Color/Color.json: metaschema_validation: Invalid type for property "value"',
  ];

  const errors: ValidationError[] = [];

  for (const line of rubyOutput) {
    const error = ErrorConverter.fromRuby(line, '/path/to/file.json');
    if (error) {
      errors.push(error);
    }
  }

  const report = reporter.createReport('/path/to/file.json', errors);
  reporter.print(report);
}

// ============================================================================
// ПРИМЕР 3: Интеграция с MCP валидатором
// ============================================================================

async function example3_McpIntegration() {
  console.log('='.repeat(80));
  console.log('EXAMPLE 3: MCP Validator Integration');
  console.log('='.repeat(80));
  console.log('');

  const reporter = new UnifiedReporter({
    groupBy: 'component',
    showSuggestions: true,
  });

  // Симулируем ошибки из RequiredFieldsValidator
  const mcpErrors = [
    {
      path: 'root.content',
      component: 'DataView',
      version: 'v1',
      missingFields: ['dataContent'],
      severity: 'error' as const,
      suggestion: 'Add "dataContent" array with DataContent items',
    },
    {
      path: 'root.content.iconView',
      component: 'IconView',
      version: 'v2',
      missingFields: ['graphic'],
      severity: 'error' as const,
      suggestion: 'Add "graphic" property with Graphic value',
    },
  ];

  const errors: ValidationError[] = mcpErrors.map(e =>
    ErrorConverter.fromMcpRequiredField(e, '/path/to/contract.json')
  );

  const report = reporter.createReport('/path/to/contract.json', errors);
  reporter.print(report);
}

// ============================================================================
// ПРИМЕР 4: Интеграция с StateAware валидатором
// ============================================================================

async function example4_StateAwareIntegration() {
  console.log('='.repeat(80));
  console.log('EXAMPLE 4: StateAware Validator Integration');
  console.log('='.repeat(80));
  console.log('');

  const reporter = new UnifiedReporter({
    groupBy: 'component',
    verbose: true,
  });

  // Симулируем ошибки из StateAwareValidator
  const stateAwareErrors = [
    {
      field: 'root.backgroundColor',
      pattern: 'control',
      message: 'Incomplete Control pattern - missing required field',
      severity: 'error' as const,
      missingFields: ['defaultValue'],
    },
    {
      field: 'root.textColor',
      pattern: 'control',
      message: 'Unexpected fields found in control pattern',
      severity: 'warning' as const,
      unexpectedFields: ['focusedValue'],
    },
  ];

  const errors: ValidationError[] = stateAwareErrors.map(e =>
    ErrorConverter.fromMcpStateAware(e, '/path/to/ButtonView.json')
  );

  const report = reporter.createReport('/path/to/ButtonView.json', errors, {
    component: 'ButtonView',
    version: 'v2',
  });

  reporter.print(report);
}

// ============================================================================
// ПРИМЕР 5: Комбинированный отчет (все источники)
// ============================================================================

async function example5_CombinedReport() {
  console.log('='.repeat(80));
  console.log('EXAMPLE 5: Combined Report (All Sources)');
  console.log('='.repeat(80));
  console.log('');

  const reporter = new UnifiedReporter({
    groupBy: 'severity',
    showPath: true,
    showJsonPointer: true,
    showLineNumbers: true,
    showSuggestions: true,
  });

  const errors: ValidationError[] = [
    // Ruby validator errors
    {
      source: 'metaschema',
      severity: 'error',
      filePath: '/path/to/contract.json',
      path: 'root.type',
      message: 'Component ButtonView not found',
      code: 'COMPONENT_NOT_FOUND',
      component: 'ButtonView',
      line: 5,
      column: 12,
    },

    // Required fields errors
    {
      source: 'required-fields',
      severity: 'error',
      filePath: '/path/to/contract.json',
      path: 'root.content',
      component: 'ButtonView',
      version: 'v2',
      message: 'Missing required fields: title, content',
      code: 'MISSING_REQUIRED_FIELD',
      suggestion: 'Add required fields: title, content',
      metadata: { missingFields: ['title', 'content'] },
      line: 8,
      column: 5,
    },

    // StateAware errors
    {
      source: 'stateaware',
      severity: 'warning',
      filePath: '/path/to/contract.json',
      path: 'root.backgroundColor',
      field: 'backgroundColor',
      message: 'Incomplete Control pattern - missing required field',
      code: 'STATEAWARE_PATTERN_ERROR',
      component: 'ButtonView',
      metadata: { pattern: 'control', missingFields: ['defaultValue'] },
      line: 15,
      column: 7,
    },

    // Web compatibility warnings
    {
      source: 'web-compat',
      severity: 'warning',
      filePath: '/path/to/contract.json',
      path: 'root.actions[0]',
      component: 'HttpAction',
      message: 'HttpAction v3 not supported on Web platform',
      line: 22,
      column: 3,
    },

    // Data binding infos
    {
      source: 'data-binding',
      severity: 'info',
      filePath: '/path/to/contract.json',
      path: 'root.title',
      message: 'Data binding detected: ${state.userName}',
      code: 'DATA_BINDING_FOUND',
      metadata: {
        bindingType: 'state',
        expression: '${state.userName}',
      },
      line: 10,
      column: 14,
    },
  ];

  const report = reporter.createReport('/path/to/contract.json', errors, {
    validator: 'combined',
    totalComponents: 3,
    webCompatibility: 85.5,
  });

  // Вывод в консоль
  reporter.print(report);

  // Экспорт в разные форматы
  console.log('\n--- JSON Export ---\n');
  const jsonOutput = await reporter.export(report, 'json');
  console.log(jsonOutput);

  console.log('\n--- Markdown Export ---\n');
  const mdOutput = await reporter.export(report, 'markdown');
  console.log(mdOutput);
}

// ============================================================================
// ПРИМЕР 6: Кастомный форматтер
// ============================================================================

import { ErrorFormatter, ValidationReport } from './unified_reporter_v3.0.0';

class SlackFormatter implements ErrorFormatter {
  name = 'slack';
  supportsColor = false;

  format(report: ValidationReport, config: ReporterConfig): string {
    const blocks = [];

    // Header
    blocks.push({
      type: 'header',
      text: {
        type: 'plain_text',
        text: `📄 Validation Report: ${report.filePath}`,
      },
    });

    // Status
    blocks.push({
      type: 'section',
      text: {
        type: 'mrkdwn',
        text: `*Status:* ${report.valid ? ':white_check_mark: Valid' : ':x: Invalid'}`,
      },
    });

    // Summary
    blocks.push({
      type: 'section',
      fields: [
        {
          type: 'mrkdwn',
          text: `*Errors:*\n${report.totalErrors}`,
        },
        {
          type: 'mrkdwn',
          text: `*Warnings:*\n${report.totalWarnings}`,
        },
      ],
    });

    // Errors
    if (report.errors.length > 0) {
      blocks.push({
        type: 'section',
        text: {
          type: 'mrkdwn',
          text: '*Errors:*',
        },
      });

      report.errors.slice(0, 5).forEach(error => {
        blocks.push({
          type: 'section',
          text: {
            type: 'mrkdwn',
            text: `• ${error.message}\n  _${error.path}_`,
          },
        });
      });

      if (report.errors.length > 5) {
        blocks.push({
          type: 'context',
          elements: [
            {
              type: 'mrkdwn',
              text: `_...and ${report.errors.length - 5} more errors_`,
            },
          ],
        });
      }
    }

    return JSON.stringify({ blocks }, null, 2);
  }
}

async function example6_CustomFormatter() {
  console.log('='.repeat(80));
  console.log('EXAMPLE 6: Custom Slack Formatter');
  console.log('='.repeat(80));
  console.log('');

  const reporter = new UnifiedReporter();

  // Регистрируем кастомный форматтер
  reporter.registerFormatter(new SlackFormatter());

  const errors: ValidationError[] = [
    {
      source: 'metaschema',
      severity: 'error',
      filePath: '/path/to/contract.json',
      path: 'root.type',
      message: 'Missing required field "type"',
    },
  ];

  const report = reporter.createReport('/path/to/contract.json', errors);

  // Экспортируем в Slack формат
  const slackOutput = await reporter.export(report, 'slack' as any);
  console.log(slackOutput);
}

// ============================================================================
// ПРИМЕР 7: Фильтрация по severity
// ============================================================================

async function example7_SeverityFiltering() {
  console.log('='.repeat(80));
  console.log('EXAMPLE 7: Severity Filtering');
  console.log('='.repeat(80));
  console.log('');

  // Показываем только errors (игнорируем warnings и infos)
  const reporter = new UnifiedReporter({
    minSeverity: 'error',
  });

  const errors: ValidationError[] = [
    {
      source: 'metaschema',
      severity: 'error',
      filePath: '/path/to/contract.json',
      path: 'root.type',
      message: 'This is an error',
    },
    {
      source: 'web-compat',
      severity: 'warning',
      filePath: '/path/to/contract.json',
      path: 'root.actions[0]',
      message: 'This is a warning (will be filtered out)',
    },
    {
      source: 'data-binding',
      severity: 'info',
      filePath: '/path/to/contract.json',
      path: 'root.title',
      message: 'This is an info (will be filtered out)',
    },
  ];

  const report = reporter.createReport('/path/to/contract.json', errors);
  reporter.print(report);

  console.log(`\nTotal errors in report: ${report.totalErrors}`);
  console.log(`Total warnings in report: ${report.totalWarnings} (filtered out)`);
  console.log(`Total infos in report: ${report.totalInfos} (filtered out)`);
}

// ============================================================================
// RUN ALL EXAMPLES
// ============================================================================

async function runAllExamples() {
  await example1_BasicUsage();
  await example2_RubyIntegration();
  await example3_McpIntegration();
  await example4_StateAwareIntegration();
  await example5_CombinedReport();
  await example6_CustomFormatter();
  await example7_SeverityFiltering();
}

// Uncomment to run examples
// runAllExamples().catch(console.error);

// Export for use in other modules
export {
  example1_BasicUsage,
  example2_RubyIntegration,
  example3_McpIntegration,
  example4_StateAwareIntegration,
  example5_CombinedReport,
  example6_CustomFormatter,
  example7_SeverityFiltering,
  runAllExamples,
};
