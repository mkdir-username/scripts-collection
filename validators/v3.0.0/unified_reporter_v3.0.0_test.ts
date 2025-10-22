#!/usr/bin/env node
/**
 * Unified Reporter v3.0.0 - Test Suite
 *
 * Тесты и демонстрация работы унифицированного репортера
 */

import {
  UnifiedReporter,
  ValidationError,
  ErrorConverter,
  pathToJsonPointer,
  extractComponentFromMessage,
  extractErrorField,
} from './unified_reporter_v3.0.0';

// ============================================================================
// UNIT TESTS
// ============================================================================

function testPathToJsonPointer() {
  console.log('🧪 Testing pathToJsonPointer()...');

  const tests = [
    {
      input: "root.properties.title",
      expected: "/root/properties/title",
    },
    {
      input: "root['properties']['title']",
      expected: "/root/properties/title",
    },
    {
      input: "root[0].items[1].name",
      expected: "/root/0/items/1/name",
    },
    {
      input: "",
      expected: "",
    },
    {
      input: "root.path~with~tildes",
      expected: "/root/path~0with~0tildes",
    },
    {
      input: "root.path/with/slashes",
      expected: "/root/path~1with~1slashes",
    },
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    const result = pathToJsonPointer(test.input);
    if (result === test.expected) {
      console.log(`  ✅ "${test.input}" -> "${result}"`);
      passed++;
    } else {
      console.log(`  ❌ "${test.input}" -> Expected: "${test.expected}", Got: "${result}"`);
      failed++;
    }
  }

  console.log(`\n  Result: ${passed} passed, ${failed} failed\n`);
  return failed === 0;
}

function testExtractComponent() {
  console.log('🧪 Testing extractComponentFromMessage()...');

  const tests = [
    {
      message: "Missing field in ButtonView (v2): title",
      expected: "ButtonView",
    },
    {
      message: "IconView is notReleased on Web",
      expected: "IconView",
    },
    {
      message: "Unexpected fields found in Control pattern",
      expected: null,
    },
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    const result = extractComponentFromMessage(test.message);
    if (result === test.expected) {
      console.log(`  ✅ "${test.message}" -> "${result}"`);
      passed++;
    } else {
      console.log(`  ❌ "${test.message}" -> Expected: "${test.expected}", Got: "${result}"`);
      failed++;
    }
  }

  console.log(`\n  Result: ${passed} passed, ${failed} failed\n`);
  return failed === 0;
}

function testExtractField() {
  console.log('🧪 Testing extractErrorField()...');

  const tests = [
    {
      message: "Missing required field 'title'",
      expected: "title",
    },
    {
      message: "Invalid value for 'backgroundColor'",
      expected: "backgroundColor",
    },
    {
      message: "Unexpected field 'focusedValue'",
      expected: "focusedValue",
    },
    {
      message: "Component ButtonView not found",
      expected: "type",
    },
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    const result = extractErrorField(test.message);
    if (result === test.expected) {
      console.log(`  ✅ "${test.message}" -> "${result}"`);
      passed++;
    } else {
      console.log(`  ❌ "${test.message}" -> Expected: "${test.expected}", Got: "${result}"`);
      failed++;
    }
  }

  console.log(`\n  Result: ${passed} passed, ${failed} failed\n`);
  return failed === 0;
}

function testErrorConverter() {
  console.log('🧪 Testing ErrorConverter...');

  let passed = 0;
  let failed = 0;

  // Test Ruby format
  const rubyText = "SDUI/components/ButtonView/v2/ButtonView.json: invalid_schema: Missing required field 'title'";
  const rubyError = ErrorConverter.fromRuby(rubyText, '/path/to/file.json');

  if (rubyError && rubyError.source === 'metaschema' && rubyError.code === 'invalid_schema') {
    console.log('  ✅ Ruby format conversion');
    passed++;
  } else {
    console.log('  ❌ Ruby format conversion failed');
    failed++;
  }

  // Test MCP RequiredField format
  const mcpError = ErrorConverter.fromMcpRequiredField(
    {
      path: 'root.content',
      component: 'DataView',
      version: 'v1',
      missingFields: ['dataContent'],
      severity: 'error',
      suggestion: 'Add "dataContent" array',
    },
    '/path/to/file.json'
  );

  if (mcpError && mcpError.source === 'required-fields' && mcpError.component === 'DataView') {
    console.log('  ✅ MCP RequiredField conversion');
    passed++;
  } else {
    console.log('  ❌ MCP RequiredField conversion failed');
    failed++;
  }

  console.log(`\n  Result: ${passed} passed, ${failed} failed\n`);
  return failed === 0;
}

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

function testReporterBasic() {
  console.log('🧪 Testing UnifiedReporter (basic)...');

  const reporter = new UnifiedReporter({
    colorize: false,
    groupBy: 'component',
  });

  const errors: ValidationError[] = [
    {
      source: 'metaschema',
      severity: 'error',
      filePath: '/test/ButtonView.json',
      path: 'root.type',
      message: 'Component ButtonView not found',
      component: 'ButtonView',
    },
    {
      source: 'required-fields',
      severity: 'error',
      filePath: '/test/ButtonView.json',
      path: 'root.content',
      component: 'ButtonView',
      message: 'Missing required field "title"',
    },
  ];

  const report = reporter.createReport('/test/ButtonView.json', errors);

  if (report.valid === false && report.totalErrors === 2 && report.byComponent.size > 0) {
    console.log('  ✅ Basic report creation');
    return true;
  } else {
    console.log('  ❌ Basic report creation failed');
    return false;
  }
}

function testReporterGrouping() {
  console.log('🧪 Testing UnifiedReporter (grouping)...');

  let passed = 0;
  let failed = 0;

  const errors: ValidationError[] = [
    {
      source: 'metaschema',
      severity: 'error',
      filePath: '/test/file.json',
      path: 'root',
      message: 'Error 1',
      component: 'ComponentA',
    },
    {
      source: 'sdui',
      severity: 'warning',
      filePath: '/test/file.json',
      path: 'root',
      message: 'Error 2',
      component: 'ComponentA',
    },
    {
      source: 'web-compat',
      severity: 'error',
      filePath: '/test/file.json',
      path: 'root',
      message: 'Error 3',
      component: 'ComponentB',
    },
  ];

  // Test groupBy: component
  const reporter1 = new UnifiedReporter({ groupBy: 'component' });
  const report1 = reporter1.createReport('/test/file.json', errors);

  if (report1.byComponent.size === 2) {
    console.log('  ✅ Group by component');
    passed++;
  } else {
    console.log('  ❌ Group by component failed');
    failed++;
  }

  // Test groupBy: source
  const reporter2 = new UnifiedReporter({ groupBy: 'source' });
  const report2 = reporter2.createReport('/test/file.json', errors);

  if (report2.bySource.size === 3) {
    console.log('  ✅ Group by source');
    passed++;
  } else {
    console.log('  ❌ Group by source failed');
    failed++;
  }

  // Test groupBy: severity
  const reporter3 = new UnifiedReporter({ groupBy: 'severity' });
  const report3 = reporter3.createReport('/test/file.json', errors);

  if (report3.bySeverity.size === 2) {
    console.log('  ✅ Group by severity');
    passed++;
  } else {
    console.log('  ❌ Group by severity failed');
    failed++;
  }

  console.log(`\n  Result: ${passed} passed, ${failed} failed\n`);
  return failed === 0;
}

function testReporterFiltering() {
  console.log('🧪 Testing UnifiedReporter (filtering)...');

  const errors: ValidationError[] = [
    {
      source: 'metaschema',
      severity: 'error',
      filePath: '/test/file.json',
      path: 'root',
      message: 'Error',
    },
    {
      source: 'sdui',
      severity: 'warning',
      filePath: '/test/file.json',
      path: 'root',
      message: 'Warning',
    },
    {
      source: 'data-binding',
      severity: 'info',
      filePath: '/test/file.json',
      path: 'root',
      message: 'Info',
    },
  ];

  // Filter by severity: only errors
  const reporter = new UnifiedReporter({ minSeverity: 'error' });
  const report = reporter.createReport('/test/file.json', errors);

  if (report.totalErrors === 1 && report.totalWarnings === 0 && report.totalInfos === 0) {
    console.log('  ✅ Severity filtering (errors only)');
    return true;
  } else {
    console.log('  ❌ Severity filtering failed');
    console.log(`    Got: ${report.totalErrors} errors, ${report.totalWarnings} warnings, ${report.totalInfos} infos`);
    return false;
  }
}

async function testReporterExport() {
  console.log('🧪 Testing UnifiedReporter (export)...');

  const reporter = new UnifiedReporter();

  const errors: ValidationError[] = [
    {
      source: 'metaschema',
      severity: 'error',
      filePath: '/test/file.json',
      path: 'root.type',
      message: 'Test error',
      component: 'TestComponent',
    },
  ];

  const report = reporter.createReport('/test/file.json', errors);

  let passed = 0;
  let failed = 0;

  // Test JSON export
  try {
    const jsonOutput = await reporter.export(report, 'json');
    const parsed = JSON.parse(jsonOutput);
    if (parsed.filePath && parsed.errors) {
      console.log('  ✅ JSON export');
      passed++;
    } else {
      console.log('  ❌ JSON export failed (invalid structure)');
      failed++;
    }
  } catch (e) {
    console.log('  ❌ JSON export failed:', e);
    failed++;
  }

  // Test Markdown export
  try {
    const mdOutput = await reporter.export(report, 'markdown');
    if (mdOutput.includes('# Validation Report') && mdOutput.includes('TestComponent')) {
      console.log('  ✅ Markdown export');
      passed++;
    } else {
      console.log('  ❌ Markdown export failed (invalid content)');
      failed++;
    }
  } catch (e) {
    console.log('  ❌ Markdown export failed:', e);
    failed++;
  }

  // Test HTML export
  try {
    const htmlOutput = await reporter.export(report, 'html');
    if (htmlOutput.includes('<!DOCTYPE html>') && htmlOutput.includes('TestComponent')) {
      console.log('  ✅ HTML export');
      passed++;
    } else {
      console.log('  ❌ HTML export failed (invalid content)');
      failed++;
    }
  } catch (e) {
    console.log('  ❌ HTML export failed:', e);
    failed++;
  }

  console.log(`\n  Result: ${passed} passed, ${failed} failed\n`);
  return failed === 0;
}

// ============================================================================
// DEMO
// ============================================================================

async function runDemo() {
  console.log('');
  console.log('='.repeat(80));
  console.log('📄 UNIFIED REPORTER v3.0.0 - DEMO');
  console.log('='.repeat(80));
  console.log('');

  const reporter = new UnifiedReporter({
    groupBy: 'component',
    showPath: true,
    showJsonPointer: true,
    showSuggestions: true,
  });

  // Создаем разнообразные ошибки
  const errors: ValidationError[] = [
    // Ruby validator errors
    {
      source: 'metaschema',
      severity: 'error',
      filePath: '/path/to/SDUI/components/ButtonView/v2/ButtonView.json',
      path: 'properties.title',
      jsonPointer: '/properties/title',
      message: 'Missing required field in schema definition',
      code: 'INVALID_SCHEMA',
      component: 'ButtonView',
      version: 'v2',
      line: 15,
      column: 5,
      suggestion: 'Add "title" to required array',
    },

    // Required fields errors
    {
      source: 'required-fields',
      severity: 'error',
      filePath: '/path/to/SDUI/components/ButtonView/v2/ButtonView.json',
      path: 'root.content',
      jsonPointer: '/root/content',
      message: 'Missing required fields: title, content',
      code: 'MISSING_REQUIRED_FIELD',
      component: 'ButtonView',
      version: 'v2',
      line: 8,
      column: 3,
      suggestion: 'Add "title" and "content" properties',
      metadata: {
        missingFields: ['title', 'content'],
      },
    },

    // StateAware errors
    {
      source: 'stateaware',
      severity: 'warning',
      filePath: '/path/to/SDUI/components/ButtonView/v2/ButtonView.json',
      path: 'root.backgroundColor',
      jsonPointer: '/root/backgroundColor',
      field: 'backgroundColor',
      message: 'Incomplete Control pattern - missing required field "defaultValue"',
      code: 'STATEAWARE_PATTERN_ERROR',
      component: 'ButtonView',
      version: 'v2',
      line: 22,
      column: 7,
      metadata: {
        pattern: 'control',
        missingFields: ['defaultValue'],
      },
    },

    // StateAware errors
    {
      source: 'stateaware',
      severity: 'warning',
      filePath: '/path/to/SDUI/components/ButtonView/v2/ButtonView.json',
      path: 'root.textColor',
      jsonPointer: '/root/textColor',
      field: 'textColor',
      message: 'Unexpected fields found in control pattern',
      code: 'STATEAWARE_PATTERN_ERROR',
      component: 'ButtonView',
      version: 'v2',
      line: 28,
      column: 7,
      metadata: {
        pattern: 'control',
        unexpectedFields: ['focusedValue'],
      },
    },

    // Web compatibility
    {
      source: 'web-compat',
      severity: 'warning',
      filePath: '/path/to/SDUI/components/ButtonView/v2/ButtonView.json',
      path: 'root.actions[0]',
      jsonPointer: '/root/actions/0',
      component: 'HttpAction',
      version: 'v3',
      message: 'HttpAction v3 not supported on Web platform',
      line: 35,
      column: 5,
    },

    // IconView errors
    {
      source: 'required-fields',
      severity: 'error',
      filePath: '/path/to/SDUI/components/ButtonView/v2/ButtonView.json',
      path: 'root.iconView',
      jsonPointer: '/root/iconView',
      message: 'Missing required field "graphic"',
      code: 'MISSING_REQUIRED_FIELD',
      component: 'IconView',
      version: 'v2',
      line: 42,
      column: 3,
      suggestion: 'Add "graphic" property with Graphic value',
      metadata: {
        missingFields: ['graphic'],
      },
    },

    // Data binding info
    {
      source: 'data-binding',
      severity: 'info',
      filePath: '/path/to/SDUI/components/ButtonView/v2/ButtonView.json',
      path: 'root.title',
      jsonPointer: '/root/title',
      message: 'Data binding detected: ${state.userName}',
      code: 'DATA_BINDING_FOUND',
      line: 10,
      column: 14,
      metadata: {
        bindingType: 'state',
        expression: '${state.userName}',
      },
    },
  ];

  const report = reporter.createReport(
    '/path/to/SDUI/components/ButtonView/v2/ButtonView.json',
    errors,
    {
      validator: 'unified',
      totalComponents: 3,
      webCompatibility: 75.0,
      dataBindings: {
        hasBindings: true,
        totalBindings: 1,
        byType: {
          state: 1,
          data: 0,
          computed: 0,
        },
      },
    }
  );

  // Вывод в консоль
  reporter.print(report);

  // Экспорт в JSON
  console.log('\n--- JSON Export (sample) ---\n');
  const jsonOutput = await reporter.export(report, 'json');
  const jsonParsed = JSON.parse(jsonOutput);
  console.log(JSON.stringify({
    filePath: jsonParsed.filePath,
    valid: jsonParsed.valid,
    summary: jsonParsed.summary,
    // Показываем только первую ошибку для краткости
    firstError: jsonParsed.errors[0],
  }, null, 2));
}

// ============================================================================
// RUN ALL TESTS
// ============================================================================

async function runAllTests() {
  console.log('');
  console.log('='.repeat(80));
  console.log('🧪 UNIFIED REPORTER v3.0.0 - TEST SUITE');
  console.log('='.repeat(80));
  console.log('');

  const results: boolean[] = [];

  // Unit tests
  console.log('--- UNIT TESTS ---\n');
  results.push(testPathToJsonPointer());
  results.push(testExtractComponent());
  results.push(testExtractField());
  results.push(testErrorConverter());

  // Integration tests
  console.log('--- INTEGRATION TESTS ---\n');
  results.push(testReporterBasic());
  results.push(testReporterGrouping());
  results.push(testReporterFiltering());
  results.push(await testReporterExport());

  // Summary
  console.log('='.repeat(80));
  const passed = results.filter(r => r).length;
  const failed = results.filter(r => !r).length;

  if (failed === 0) {
    console.log(`✅ ALL TESTS PASSED (${passed}/${results.length})`);
  } else {
    console.log(`❌ SOME TESTS FAILED (${passed} passed, ${failed} failed)`);
  }
  console.log('='.repeat(80));
  console.log('');

  return failed === 0;
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  const args = process.argv.slice(2);

  if (args.includes('--test')) {
    const success = await runAllTests();
    process.exit(success ? 0 : 1);
  } else if (args.includes('--demo')) {
    await runDemo();
  } else {
    console.log('Usage:');
    console.log('  node unified_reporter_v3.0.0_test.ts --test   # Run test suite');
    console.log('  node unified_reporter_v3.0.0_test.ts --demo   # Run demo');
  }
}

// Run if executed directly
if (require.main === module) {
  main().catch(console.error);
}

export {
  testPathToJsonPointer,
  testExtractComponent,
  testExtractField,
  testErrorConverter,
  testReporterBasic,
  testReporterGrouping,
  testReporterFiltering,
  testReporterExport,
  runAllTests,
  runDemo,
};
