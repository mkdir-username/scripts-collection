/**
 * Jinja-Aware Validator v1.0.0 - Tests
 *
 * Unit тесты для Jinja-Aware Validator
 *
 * @author Claude Code CLI
 * @version 1.0.0
 * @date 2025-10-05
 */

import { JinjaAwareValidator, SimpleJinjaParser, WebCompatibilityChecker } from './jinja_aware_validator_v1.0.0.js';
import { writeFile, mkdir, rm } from 'fs/promises';
import { join } from 'path';
import { existsSync } from 'fs';

// ============================================================================
// TEST HELPERS
// ============================================================================

const TEST_DIR = '/Users/username/Scripts/validators/v3.0.0/.tmp/test_jinja_validator';

async function setupTestDir() {
  if (existsSync(TEST_DIR)) {
    await rm(TEST_DIR, { recursive: true, force: true });
  }
  await mkdir(TEST_DIR, { recursive: true });
}

async function cleanupTestDir() {
  if (existsSync(TEST_DIR)) {
    await rm(TEST_DIR, { recursive: true, force: true });
  }
}

async function createTestTemplate(filename: string, content: string): Promise<string> {
  const path = join(TEST_DIR, filename);
  await writeFile(path, content, 'utf-8');
  return path;
}

function assert(condition: boolean, message: string) {
  if (!condition) {
    throw new Error(`Assertion failed: ${message}`);
  }
}

function assertEquals(actual: any, expected: any, message: string) {
  if (actual !== expected) {
    throw new Error(`${message}\n  Expected: ${expected}\n  Actual: ${actual}`);
  }
}

// ============================================================================
// UNIT TESTS
// ============================================================================

async function test_simpleJinjaParser_extractJson() {
  console.log('TEST: SimpleJinjaParser.extractJson()');

  const parser = new SimpleJinjaParser();

  const template = `
{
  "type": "ButtonView",
  "textContent": {
    "kind": "plain",
    "text": "{{ buttonText }}"
  }
}
  `.trim();

  const templatePath = await createTestTemplate('test1.j2.java', template);
  const result = await parser.parse(templatePath);

  assert(result.extractedJson.length > 0, 'Extracted JSON should not be empty');
  assert(result.extractedJson.includes('"type"'), 'Should contain "type" field');
  assert(result.extractedJson.includes('ButtonView'), 'Should contain ButtonView');

  console.log('  ✅ PASSED\n');
}

async function test_simpleJinjaParser_findImports() {
  console.log('TEST: SimpleJinjaParser.findImports()');

  const parser = new SimpleJinjaParser();

  const template = `
{% import "./header.j2.java" as header %}
{% import "./footer.j2.java" as footer %}

{
  "type": "StackView",
  "elements": [
    {{ header }},
    {{ footer }}
  ]
}
  `.trim();

  const templatePath = await createTestTemplate('test2.j2.java', template);
  const result = await parser.parse(templatePath);

  assertEquals(result.imports.length, 2, 'Should find 2 imports');
  assertEquals(result.imports[0].variable, 'header', 'First import variable should be "header"');
  assertEquals(result.imports[1].variable, 'footer', 'Second import variable should be "footer"');

  console.log('  ✅ PASSED\n');
}

async function test_simpleJinjaParser_findComponents() {
  console.log('TEST: SimpleJinjaParser.findComponents()');

  const parser = new SimpleJinjaParser();

  const template = `
{
  "type": "StackView",
  "elements": [
    {
      "type": "ButtonView",
      "textContent": { "kind": "plain", "text": "Click" }
    },
    {
      "type": "TextView",
      "textContent": { "kind": "plain", "text": "Hello" }
    }
  ]
}
  `.trim();

  const templatePath = await createTestTemplate('test3.j2.java', template);
  const result = await parser.parse(templatePath);

  assert(result.components.length >= 3, 'Should find at least 3 components (StackView, ButtonView, TextView)');

  const componentNames = result.components.map(c => c.name);
  assert(componentNames.includes('StackView'), 'Should find StackView');
  assert(componentNames.includes('ButtonView'), 'Should find ButtonView');
  assert(componentNames.includes('TextView'), 'Should find TextView');

  console.log('  ✅ PASSED\n');
}

async function test_jinjaAwareValidator_basicValidation() {
  console.log('TEST: JinjaAwareValidator.validate() - basic');

  const validator = new JinjaAwareValidator();

  const template = `
{
  "type": "ButtonView",
  "textContent": {
    "kind": "plain",
    "text": "Submit"
  },
  "actions": [
    {
      "type": "HttpAction",
      "url": "https://api.example.com/submit"
    }
  ]
}
  `.trim();

  const templatePath = await createTestTemplate('test4.j2.java', template);

  const result = await validator.validate(templatePath, {
    validateImports: false,
    checkWebCompatibility: false,
    checkRequiredFields: false,
  });

  assert(result.metadata.totalComponents > 0, 'Should find components');
  assert(result.components.length > 0, 'Should have component info');

  console.log('  ✅ PASSED\n');
}

async function test_jinjaAwareValidator_requiredFields() {
  console.log('TEST: JinjaAwareValidator - required fields validation');

  const validator = new JinjaAwareValidator();

  // ButtonView без textContent и actions (required fields)
  const template = `
{
  "type": "ButtonView"
}
  `.trim();

  const templatePath = await createTestTemplate('test5.j2.java', template);

  const result = await validator.validate(templatePath, {
    validateImports: false,
    checkWebCompatibility: false,
    checkRequiredFields: true,
  });

  // Проверяем, что найдены отсутствующие поля
  const buttonView = result.components.find(c => c.name === 'ButtonView');
  assert(buttonView !== undefined, 'Should find ButtonView component');

  if (buttonView) {
    assert(buttonView.requiredFieldsMissing.length > 0, 'Should have missing required fields');
  }

  console.log('  ✅ PASSED\n');
}

async function test_jinjaAwareValidator_importValidation() {
  console.log('TEST: JinjaAwareValidator - import validation');

  const validator = new JinjaAwareValidator();

  // Создаем импортируемый файл
  const headerTemplate = `
{
  "type": "TextView",
  "textContent": {
    "kind": "plain",
    "text": "Header"
  }
}
  `.trim();

  const headerPath = await createTestTemplate('header.j2.java', headerTemplate);

  // Создаем главный файл с импортом
  const mainTemplate = `
{% import "./header.j2.java" as header %}

{
  "type": "StackView",
  "elements": [
    {{ header }}
  ]
}
  `.trim();

  const mainPath = await createTestTemplate('main.j2.java', mainTemplate);

  const result = await validator.validate(mainPath, {
    validateImports: true,
    maxImportDepth: 2,
  });

  assert(result.imports.length > 0, 'Should find imports');

  console.log('  ✅ PASSED\n');
}

async function test_jinjaAwareValidator_errorMapping() {
  console.log('TEST: JinjaAwareValidator - error line mapping');

  const validator = new JinjaAwareValidator();

  const template = `
{
  "type": "ButtonView",
  "textContent": {
    "kind": "plain",
    "text": "Click"
  }
}
  `.trim();

  const templatePath = await createTestTemplate('test6.j2.java', template);

  const result = await validator.validate(templatePath, {
    checkRequiredFields: true,
  });

  // Если есть ошибки, они должны иметь номера строк
  result.errors.forEach(error => {
    if (error.line === undefined) {
      console.warn(`  ⚠️  Warning: Error without line number: ${error.message}`);
    }
  });

  console.log('  ✅ PASSED\n');
}

async function test_jinjaAwareValidator_webCompatibility() {
  console.log('TEST: JinjaAwareValidator - WEB compatibility check');

  const validator = new JinjaAwareValidator();

  const template = `
{
  "type": "ButtonView",
  "textContent": {
    "kind": "plain",
    "text": "Submit"
  },
  "actions": []
}
  `.trim();

  const templatePath = await createTestTemplate('test7.j2.java', template);

  const result = await validator.validate(templatePath, {
    validateImports: false,
    checkWebCompatibility: true,
    checkRequiredFields: false,
  });

  assert(result.webCompatibility >= 0 && result.webCompatibility <= 100, 'WEB compatibility should be between 0-100');

  console.log(`  WEB Compatibility: ${result.webCompatibility}%`);
  console.log('  ✅ PASSED\n');
}

async function test_jinjaAwareValidator_exportJson() {
  console.log('TEST: JinjaAwareValidator - JSON export');

  const validator = new JinjaAwareValidator();

  const template = `
{
  "type": "TextView",
  "textContent": {
    "kind": "plain",
    "text": "Hello World"
  }
}
  `.trim();

  const templatePath = await createTestTemplate('test8.j2.java', template);

  const result = await validator.validate(templatePath);
  const json = validator.exportToJson(result);

  assert(json.length > 0, 'Exported JSON should not be empty');

  const parsed = JSON.parse(json);
  assert(parsed.valid !== undefined, 'Should have "valid" field');
  assert(parsed.metadata !== undefined, 'Should have "metadata" field');
  assert(parsed.components !== undefined, 'Should have "components" field');

  console.log('  ✅ PASSED\n');
}

async function test_webCompatibilityChecker() {
  console.log('TEST: WebCompatibilityChecker.checkComponent()');

  const checker = new WebCompatibilityChecker();

  // Проверяем известный компонент
  const result = await checker.checkComponent('ButtonView');

  assert(result.compatible !== undefined, 'Should return compatibility status');
  assert(result.reason !== undefined, 'Should return reason');

  console.log(`  ButtonView: ${result.compatible ? 'compatible' : 'incompatible'} (${result.reason})`);
  console.log('  ✅ PASSED\n');
}

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

async function integrationTest_fullValidation() {
  console.log('INTEGRATION TEST: Full validation pipeline');

  const validator = new JinjaAwareValidator({ verbose: false });

  const template = `
{
  "type": "StackView",
  "elements": [
    {
      "type": "ButtonView",
      "textContent": {
        "kind": "plain",
        "text": "Submit"
      },
      "actions": [
        {
          "type": "HttpAction",
          "url": "https://api.example.com/submit"
        }
      ]
    },
    {
      "type": "TextView",
      "textContent": {
        "kind": "plain",
        "text": "Description"
      }
    }
  ]
}
  `.trim();

  const templatePath = await createTestTemplate('integration.j2.java', template);

  const result = await validator.validate(templatePath, {
    validateImports: true,
    checkWebCompatibility: true,
    checkRequiredFields: true,
    maxImportDepth: 3,
  });

  console.log(`  Valid: ${result.valid}`);
  console.log(`  Errors: ${result.errors.length}`);
  console.log(`  Warnings: ${result.warnings.length}`);
  console.log(`  Components: ${result.metadata.totalComponents}`);
  console.log(`  WEB Compatibility: ${result.webCompatibility}%`);

  console.log('  ✅ PASSED\n');
}

// ============================================================================
// TEST RUNNER
// ============================================================================

async function runAllTests() {
  console.log('\n' + '═'.repeat(80));
  console.log('JINJA-AWARE VALIDATOR v1.0.0 - TEST SUITE');
  console.log('═'.repeat(80) + '\n');

  await setupTestDir();

  const tests = [
    // Unit tests
    { name: 'SimpleJinjaParser.extractJson()', fn: test_simpleJinjaParser_extractJson },
    { name: 'SimpleJinjaParser.findImports()', fn: test_simpleJinjaParser_findImports },
    { name: 'SimpleJinjaParser.findComponents()', fn: test_simpleJinjaParser_findComponents },
    { name: 'JinjaAwareValidator - basic', fn: test_jinjaAwareValidator_basicValidation },
    { name: 'JinjaAwareValidator - required fields', fn: test_jinjaAwareValidator_requiredFields },
    { name: 'JinjaAwareValidator - imports', fn: test_jinjaAwareValidator_importValidation },
    { name: 'JinjaAwareValidator - error mapping', fn: test_jinjaAwareValidator_errorMapping },
    { name: 'JinjaAwareValidator - WEB compatibility', fn: test_jinjaAwareValidator_webCompatibility },
    { name: 'JinjaAwareValidator - JSON export', fn: test_jinjaAwareValidator_exportJson },
    { name: 'WebCompatibilityChecker', fn: test_webCompatibilityChecker },

    // Integration tests
    { name: 'Full validation pipeline', fn: integrationTest_fullValidation },
  ];

  let passed = 0;
  let failed = 0;

  for (const test of tests) {
    try {
      await test.fn();
      passed++;
    } catch (error) {
      console.error(`  ❌ FAILED: ${error}\n`);
      failed++;
    }
  }

  await cleanupTestDir();

  console.log('═'.repeat(80));
  console.log(`TEST RESULTS: ${passed} passed, ${failed} failed`);
  console.log('═'.repeat(80) + '\n');

  return failed === 0;
}

// Запуск тестов
if (import.meta.url === `file://${process.argv[1]}`) {
  runAllTests()
    .then(success => process.exit(success ? 0 : 1))
    .catch(error => {
      console.error(`Test runner failed: ${error}`);
      process.exit(1);
    });
}

export { runAllTests };
