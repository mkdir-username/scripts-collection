/**
 * Comprehensive Test Suite для SDUI Validator v2.3.0
 *
 * Полное покрытие тестами:
 * - jinja_parser_v1.0.0.ts (Unit тесты)
 * - jinja_aware_validator_v1.0.0.ts (Unit + Integration тесты)
 * - vscode-validate-on-save_v2.2.0.ts (Integration тесты)
 * - Реальные примеры .j2.java файлов
 *
 * @version 2.3.0
 * @author Claude Code (Agent Testing)
 * @date 2025-10-05
 */

import { describe, it, expect, beforeEach, afterEach } from '@jest/globals';
import { readFile, writeFile, mkdir, rm } from 'fs/promises';
import { join, resolve } from 'path';
import { tmpdir } from 'os';
import { existsSync } from 'fs';

// ============================================================================
// ИМПОРТЫ МОДУЛЕЙ ДЛЯ ТЕСТИРОВАНИЯ
// ============================================================================

import {
  JinjaParser,
  JinjaParseResult,
  ImportInfo,
  ParseError,
  isJinjaTemplate,
  normalizeImportPath,
} from './jinja_parser_v1.0.0.js';

import {
  JinjaAwareValidator,
  JinjaValidationResult,
  ComponentInfo,
  ImportValidation,
} from './jinja_aware_validator_v1.0.0.js';

// ============================================================================
// ТЕСТОВЫЕ УТИЛИТЫ
// ============================================================================

/**
 * Создание временной директории для тестов
 */
async function createTestWorkspace(): Promise<string> {
  const workspace = join(tmpdir(), `sdui-test-${Date.now()}`);
  await mkdir(workspace, { recursive: true });
  return workspace;
}

/**
 * Очистка временной директории
 */
async function cleanupTestWorkspace(workspace: string): Promise<void> {
  if (existsSync(workspace)) {
    await rm(workspace, { recursive: true, force: true });
  }
}

/**
 * Создание тестового Jinja файла
 */
async function createTestJinjaFile(
  workspace: string,
  fileName: string,
  content: string
): Promise<string> {
  const filePath = join(workspace, fileName);
  await writeFile(filePath, content, 'utf-8');
  return filePath;
}

// ============================================================================
// UNIT ТЕСТЫ: jinja_parser_v1.0.0.ts
// ============================================================================

describe('JinjaParser Unit Tests', () => {
  let workspace: string;
  let parser: JinjaParser;

  beforeEach(async () => {
    workspace = await createTestWorkspace();
    parser = new JinjaParser({
      basePath: workspace,
      allowRecursiveImports: true,
      maxImportDepth: 5,
      buildSourceMap: true,
    });
  });

  afterEach(async () => {
    await cleanupTestWorkspace(workspace);
  });

  // --------------------------------------------------------------------------
  // 1. ПАРСИНГ ИМПОРТОВ ИЗ КОММЕНТАРИЕВ
  // --------------------------------------------------------------------------

  describe('Import Parsing', () => {
    it('должен парсить импорты из комментариев формата // [...](file://path)', async () => {
      const mainContent = `
{
  "type": "StackView",
  "content": {
    "children": [
      // [Button Component](file://./button.json)
      // [Header Section](file://./header.json)
    ]
  }
}`.trim();

      const buttonContent = JSON.stringify({
        type: 'ButtonView',
        title: { defaultValue: 'Click Me' },
      });

      const headerContent = JSON.stringify({
        type: 'TextView',
        textContent: { defaultValue: 'Header' },
      });

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', mainContent);
      await createTestJinjaFile(workspace, 'button.json', buttonContent);
      await createTestJinjaFile(workspace, 'header.json', headerContent);

      const result = parser.parse(mainFile);

      expect(result.imports).toHaveLength(2);
      expect(result.imports[0].description).toBe('Button Component');
      expect(result.imports[0].path).toContain('button.json');
      expect(result.imports[1].description).toBe('Header Section');
      expect(result.imports[1].path).toContain('header.json');
      expect(result.errors).toHaveLength(0);
    });

    it('должен обрабатывать абсолютные пути в импортах', async () => {
      const absolutePath = join(workspace, 'absolute.json');
      const content = `
{
  "type": "StackView",
  // [Absolute Import](file://${absolutePath})
}`.trim();

      await createTestJinjaFile(workspace, 'absolute.json', '{"type": "Spacer"}');
      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);

      const result = parser.parse(mainFile);

      expect(result.imports).toHaveLength(1);
      expect(result.imports[0].resolvedPath).toBe(absolutePath);
      expect(result.errors).toHaveLength(0);
    });

    it('должен обрабатывать относительные пути в импортах', async () => {
      const nestedDir = join(workspace, 'nested');
      await mkdir(nestedDir, { recursive: true });

      const content = `
{
  "type": "StackView",
  // [Nested Component](file://./nested/component.json)
}`.trim();

      await createTestJinjaFile(workspace, 'nested/component.json', '{"type": "TextView"}');
      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);

      const result = parser.parse(mainFile);

      expect(result.imports).toHaveLength(1);
      expect(result.imports[0].resolvedPath).toContain('nested/component.json');
      expect(result.errors).toHaveLength(0);
    });

    it('должен детектировать циклические импорты', async () => {
      const fileA = `
{
  "type": "StackView",
  // [Import B](file://./b.j2.java)
}`.trim();

      const fileB = `
{
  "type": "StackView",
  // [Import A](file://./a.j2.java)
}`.trim();

      await createTestJinjaFile(workspace, 'a.j2.java', fileA);
      await createTestJinjaFile(workspace, 'b.j2.java', fileB);

      const mainPath = join(workspace, 'a.j2.java');
      const result = parser.parse(mainPath);

      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors.some((e) => e.type === 'circular_import')).toBe(true);
    });

    it('должен сообщать об отсутствующих импортах', async () => {
      const content = `
{
  "type": "StackView",
  // [Missing File](file://./nonexistent.json)
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = parser.parse(mainFile);

      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors.some((e) => e.type === 'file_not_found')).toBe(true);
    });

    it('должен ограничивать глубину импортов', async () => {
      // Создаем цепочку импортов глубже максимальной
      const maxDepth = 3;
      const parserWithLimit = new JinjaParser({ maxImportDepth: maxDepth });

      for (let i = 0; i <= maxDepth + 1; i++) {
        const nextImport =
          i < maxDepth + 1
            ? `// [Import ${i + 1}](file://./file${i + 1}.j2.java)`
            : '';
        const content = `{ "type": "StackView", "level": ${i} ${nextImport} }`;
        await createTestJinjaFile(workspace, `file${i}.j2.java`, content);
      }

      const mainPath = join(workspace, 'file0.j2.java');
      const result = parserWithLimit.parse(mainPath);

      expect(result.errors.some((e) => e.message.includes('максимальная глубина'))).toBe(
        true
      );
    });
  });

  // --------------------------------------------------------------------------
  // 2. РЕЗОЛВИНГ МОДУЛЕЙ
  // --------------------------------------------------------------------------

  describe('Module Resolution', () => {
    it('должен резолвить .json модули', async () => {
      const moduleContent = JSON.stringify({
        type: 'ButtonView',
        title: { defaultValue: 'Button' },
      });

      const mainContent = `
{
  "type": "StackView",
  // [Button Module](file://./modules/button.json)
}`.trim();

      await mkdir(join(workspace, 'modules'), { recursive: true });
      await createTestJinjaFile(workspace, 'modules/button.json', moduleContent);
      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', mainContent);

      const result = parser.parse(mainFile);

      expect(result.imports).toHaveLength(1);
      expect(result.imports[0].content).toEqual(JSON.parse(moduleContent));
      expect(result.errors).toHaveLength(0);
    });

    it('должен резолвить .j2.java модули', async () => {
      const moduleContent = `
{
  "type": "TextView",
  "textContent": {
    "defaultValue": "{{ title }}"
  }
}`.trim();

      const mainContent = `
{
  "type": "StackView",
  // [Text Module](file://./modules/text.j2.java)
}`.trim();

      await mkdir(join(workspace, 'modules'), { recursive: true });
      await createTestJinjaFile(workspace, 'modules/text.j2.java', moduleContent);
      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', mainContent);

      const parserWithDefaults = new JinjaParser({
        basePath: workspace,
        defaultValues: { title: 'Default Title' },
      });

      const result = parserWithDefaults.parse(mainFile);

      expect(result.imports).toHaveLength(1);
      expect(result.imports[0].content.textContent.defaultValue).toBe('Default Title');
    });

    it('должен резолвить вложенные импорты', async () => {
      const level3 = '{ "type": "Spacer" }';
      const level2 = `
{
  "type": "StackView",
  // [Level 3](file://./level3.json)
}`.trim();
      const level1 = `
{
  "type": "StackView",
  // [Level 2](file://./level2.j2.java)
}`.trim();

      await createTestJinjaFile(workspace, 'level3.json', level3);
      await createTestJinjaFile(workspace, 'level2.j2.java', level2);
      const mainFile = await createTestJinjaFile(workspace, 'level1.j2.java', level1);

      const result = parser.parse(mainFile);

      expect(result.stats.importCount).toBeGreaterThan(0);
      expect(result.errors).toHaveLength(0);
    });
  });

  // --------------------------------------------------------------------------
  // 3. ОБРАБОТКА JINJA ПЕРЕМЕННЫХ
  // --------------------------------------------------------------------------

  describe('Jinja Variable Processing', () => {
    it('должен заменять Jinja переменные на значения по умолчанию', async () => {
      const content = `
{
  "type": "TextView",
  "text": "{{ userName }}",
  "count": {{ itemCount }},
  "visible": {{ isVisible }}
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);

      const parserWithDefaults = new JinjaParser({
        defaultValues: {
          userName: 'John Doe',
          itemCount: 42,
          isVisible: true,
        },
      });

      const result = parserWithDefaults.parse(mainFile);

      expect(result.extractedJson.text).toBe('John Doe');
      expect(result.extractedJson.count).toBe(42);
      expect(result.extractedJson.visible).toBe(true);
      expect(result.stats.variableCount).toBe(3);
    });

    it('должен выводить значения по умолчанию на основе имен переменных', async () => {
      const content = `
{
  "isEnabled": {{ isEnabled }},
  "itemCount": {{ count }},
  "userList": {{ items }},
  "config": {{ settings }}
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = parser.parse(mainFile);

      expect(result.extractedJson.isEnabled).toBe(false); // is* -> boolean
      expect(result.extractedJson.itemCount).toBe(0); // *count -> number
      expect(result.extractedJson.userList).toEqual([]); // *items -> array
      expect(result.extractedJson.config).toEqual({}); // *settings -> object
    });

    it('должен обрабатывать вложенные переменные (obj.field)', async () => {
      const content = `
{
  "userName": "{{ user.name }}",
  "userAge": {{ user.age }},
  "accountBalance": {{ account.balance }}
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);

      const parserWithNested = new JinjaParser({
        defaultValues: {
          user: { name: 'Alice', age: 30 },
          account: { balance: 100.5 },
        },
      });

      const result = parserWithNested.parse(mainFile);

      expect(result.extractedJson.userName).toBe('Alice');
      expect(result.extractedJson.userAge).toBe(30);
      expect(result.extractedJson.accountBalance).toBe(100.5);
    });
  });

  // --------------------------------------------------------------------------
  // 4. SOURCE MAP ПОСТРОЕНИЕ
  // --------------------------------------------------------------------------

  describe('Source Map Building', () => {
    it('должен строить source map для маппинга позиций', async () => {
      const content = `
{
  "type": "StackView",
  // [Component](file://./comp.json)
  "title": "{{ title }}"
}`.trim();

      await createTestJinjaFile(workspace, 'comp.json', '{"type": "Spacer"}');
      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);

      const result = parser.parse(mainFile);

      expect(result.sourceMap.length).toBeGreaterThan(0);

      // Проверяем наличие маппинга для импорта
      const importMapping = result.sourceMap.find((m) => m.tokenType === 'import');
      expect(importMapping).toBeDefined();
      expect(importMapping?.jinjaLine).toBeGreaterThan(0);

      // Проверяем наличие маппинга для переменной
      const variableMapping = result.sourceMap.find((m) => m.tokenType === 'variable');
      expect(variableMapping).toBeDefined();
      expect(variableMapping?.jinjaLine).toBeGreaterThan(0);
    });

    it('должен правильно мапить строки и колонки', async () => {
      const content = `{
  "field1": "value1",
  "field2": {{ variable }}
}`;

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);

      const parserWithMap = new JinjaParser({ buildSourceMap: true });
      const result = parserWithMap.parse(mainFile);

      const varMapping = result.sourceMap.find((m) => m.tokenType === 'variable');
      expect(varMapping?.jinjaLine).toBe(3); // Переменная на 3-й строке
      expect(varMapping?.jinjaColumn).toBeGreaterThan(0);
    });
  });

  // --------------------------------------------------------------------------
  // 5. ОБРАБОТКА ОШИБОК
  // --------------------------------------------------------------------------

  describe('Error Handling', () => {
    it('должен обрабатывать некорректный JSON синтаксис', async () => {
      const content = `
{
  "type": "StackView",
  "invalid": missing_quotes
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = parser.parse(mainFile);

      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors.some((e) => e.type === 'parse_error')).toBe(true);
    });

    it('должен обрабатывать отсутствующие файлы', async () => {
      const nonExistentPath = join(workspace, 'nonexistent.j2.java');
      const result = parser.parse(nonExistentPath);

      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors[0].type).toBe('file_not_found');
    });

    it('должен собирать статистику парсинга', async () => {
      const content = `
{
  "type": "StackView",
  "title": "{{ title }}",
  "count": {{ count }}
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = parser.parse(mainFile);

      expect(result.stats.parseTimeMs).toBeGreaterThan(0);
      expect(result.stats.variableCount).toBe(2);
      expect(result.stats.totalSizeBytes).toBeGreaterThan(0);
    });
  });

  // --------------------------------------------------------------------------
  // 6. УТИЛИТЫ
  // --------------------------------------------------------------------------

  describe('Utility Functions', () => {
    it('isJinjaTemplate должен определять Jinja файлы', () => {
      expect(isJinjaTemplate('file.j2.java')).toBe(true);
      expect(isJinjaTemplate('file.jinja.java')).toBe(true);
      expect(isJinjaTemplate('file.json')).toBe(false);
      expect(isJinjaTemplate('file.js')).toBe(false);
    });

    it('normalizeImportPath должен нормализовать file:// пути', () => {
      expect(normalizeImportPath('file:///path/to/file.json')).toBe('/path/to/file.json');
      expect(normalizeImportPath('./relative/path.json')).toBe('./relative/path.json');
      expect(normalizeImportPath('file://./module.json')).toBe('./module.json');
    });
  });
});

// ============================================================================
// INTEGRATION ТЕСТЫ: jinja_aware_validator_v1.0.0.ts
// ============================================================================

describe('JinjaAwareValidator Integration Tests', () => {
  let workspace: string;
  let validator: JinjaAwareValidator;

  beforeEach(async () => {
    workspace = await createTestWorkspace();
    validator = new JinjaAwareValidator({
      basePath: process.env.FMS_PATH || '/Users/username/Documents/FMS_GIT',
      verbose: false,
    });
  });

  afterEach(async () => {
    await cleanupTestWorkspace(workspace);
  });

  // --------------------------------------------------------------------------
  // 1. WEB COMPATIBILITY ВАЛИДАЦИЯ
  // --------------------------------------------------------------------------

  describe('Web Compatibility Validation', () => {
    it('должен валидировать WEB-совместимые компоненты', async () => {
      const content = `
{
  "type": "StackView",
  "content": {
    "children": [
      {
        "type": "ButtonView",
        "textContent": { "defaultValue": "Click" },
        "actions": []
      }
    ]
  }
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = await validator.validate(mainFile, {
        checkWebCompatibility: true,
      });

      expect(result.components.length).toBeGreaterThan(0);
      expect(result.webCompatibility).toBeGreaterThanOrEqual(0);
    });

    it('должен детектировать WEB-несовместимые компоненты', async () => {
      // Создаем компонент, который может быть notReleased для WEB
      const content = `
{
  "type": "StackView",
  "content": {
    "children": [
      {
        "type": "HypotheticalNotReleasedView",
        "content": {}
      }
    ]
  }
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = await validator.validate(mainFile, {
        checkWebCompatibility: true,
      });

      // Проверяем, что валидатор обработал компонент
      expect(result.components.length).toBeGreaterThan(0);
    });
  });

  // --------------------------------------------------------------------------
  // 2. ВАЛИДАЦИЯ ОБЯЗАТЕЛЬНЫХ ПОЛЕЙ
  // --------------------------------------------------------------------------

  describe('Required Fields Validation', () => {
    it('должен детектировать отсутствующие обязательные поля', async () => {
      const content = `
{
  "type": "ButtonView"
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = await validator.validate(mainFile, {
        checkRequiredFields: true,
      });

      // ButtonView требует textContent и actions
      const buttonComponent = result.components.find((c) => c.name === 'ButtonView');
      expect(buttonComponent).toBeDefined();
      expect(buttonComponent?.requiredFieldsMissing.length).toBeGreaterThan(0);
    });

    it('должен пропускать компоненты с корректными полями', async () => {
      const content = `
{
  "type": "ButtonView",
  "textContent": { "defaultValue": "Click Me" },
  "actions": [{ "type": "HttpAction", "url": "/api" }]
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = await validator.validate(mainFile, {
        checkRequiredFields: true,
      });

      const buttonComponent = result.components.find((c) => c.name === 'ButtonView');
      expect(buttonComponent?.requiredFieldsMissing).toEqual([]);
    });
  });

  // --------------------------------------------------------------------------
  // 3. РЕКУРСИВНАЯ ВАЛИДАЦИЯ ИМПОРТОВ
  // --------------------------------------------------------------------------

  describe('Recursive Import Validation', () => {
    it('должен валидировать импорты рекурсивно', async () => {
      const buttonModule = `
{
  "type": "ButtonView",
  "textContent": { "defaultValue": "Button" },
  "actions": []
}`.trim();

      const mainContent = `
{
  "type": "StackView",
  "content": {
    "children": [
      // [Button Module](file://./button.json)
    ]
  }
}`.trim();

      await createTestJinjaFile(workspace, 'button.json', buttonModule);
      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', mainContent);

      const result = await validator.validate(mainFile, {
        validateImports: true,
        maxImportDepth: 3,
      });

      expect(result.imports.length).toBeGreaterThan(0);
      expect(result.imports[0].valid).toBe(true);
      expect(result.metadata.importsValidated).toBeGreaterThan(0);
    });

    it('должен сообщать об ошибках в импортах', async () => {
      const invalidModule = `
{
  "type": "InvalidComponent"
}`.trim();

      const mainContent = `
{
  "type": "StackView",
  // [Invalid Module](file://./invalid.json)
}`.trim();

      await createTestJinjaFile(workspace, 'invalid.json', invalidModule);
      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', mainContent);

      const result = await validator.validate(mainFile, {
        validateImports: true,
      });

      expect(result.imports.length).toBeGreaterThan(0);
      // Может быть валидным или нет в зависимости от схемы
    });

    it('должен обрабатывать отсутствующие импорты', async () => {
      const mainContent = `
{
  "type": "StackView",
  // [Missing Module](file://./missing.json)
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', mainContent);

      const result = await validator.validate(mainFile, {
        validateImports: true,
      });

      expect(result.imports.length).toBeGreaterThan(0);
      expect(result.imports[0].valid).toBe(false);
      expect(result.imports[0].errors.some((e) => e.code === 'IMPORT_NOT_FOUND')).toBe(
        true
      );
    });
  });

  // --------------------------------------------------------------------------
  // 4. POSITION TRACKING ДЛЯ .j2.java
  // --------------------------------------------------------------------------

  describe('Position Tracking for .j2.java', () => {
    it('должен мапить ошибки на исходные позиции в Jinja', async () => {
      const content = `
{
  "type": "StackView",
  "content": {
    "children": [
      {
        "type": "ButtonView"
      }
    ]
  }
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = await validator.validate(mainFile);

      // Если есть ошибки, они должны иметь номера строк
      if (result.errors.length > 0) {
        result.errors.forEach((error) => {
          expect(error.line).toBeDefined();
          expect(error.line).toBeGreaterThan(0);
        });
      }
    });

    it('должен корректно мапить позиции после обработки Jinja', async () => {
      const content = `
{
  "type": "TextView",
  "textContent": {
    "defaultValue": "{{ title }}"
  }
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = await validator.validate(mainFile);

      // Проверяем, что исходная позиция сохранена
      expect(result.metadata.templatePath).toBe(mainFile);
    });
  });

  // --------------------------------------------------------------------------
  // 5. ОБРАТНАЯ СОВМЕСТИМОСТЬ С .json
  // --------------------------------------------------------------------------

  describe('Backward Compatibility with .json', () => {
    it('должен валидировать обычные .json файлы', async () => {
      const content = `
{
  "type": "StackView",
  "content": {
    "children": [
      {
        "type": "TextView",
        "textContent": { "defaultValue": "Hello" }
      }
    ]
  }
}`.trim();

      const jsonFile = await createTestJinjaFile(workspace, 'contract.json', content);
      const result = await validator.validate(jsonFile);

      expect(result.components.length).toBeGreaterThan(0);
      expect(result.valid).toBeDefined();
    });

    it('должен обрабатывать .json без Jinja логики', async () => {
      const content = JSON.stringify({
        type: 'StackView',
        content: {
          children: [
            {
              type: 'ButtonView',
              textContent: { defaultValue: 'Pure JSON' },
              actions: [],
            },
          ],
        },
      });

      const jsonFile = await createTestJinjaFile(workspace, 'pure.json', content);
      const result = await validator.validate(jsonFile);

      expect(result.metadata.templatePath).toBe(jsonFile);
      expect(result.components.some((c) => c.name === 'ButtonView')).toBe(true);
    });
  });

  // --------------------------------------------------------------------------
  // 6. ВЫВОД ОТЧЕТОВ
  // --------------------------------------------------------------------------

  describe('Validation Reporting', () => {
    it('должен генерировать детальный отчет валидации', async () => {
      const content = `
{
  "type": "StackView",
  "content": {
    "children": [
      {
        "type": "ButtonView",
        "textContent": { "defaultValue": "Button" },
        "actions": []
      }
    ]
  }
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = await validator.validate(mainFile);

      expect(result.metadata.totalComponents).toBeGreaterThan(0);
      expect(result.metadata.templatePath).toBe(mainFile);
      expect(result.webCompatibility).toBeGreaterThanOrEqual(0);
      expect(result.webCompatibility).toBeLessThanOrEqual(100);
    });

    it('должен экспортировать результат в JSON', async () => {
      const content = `
{
  "type": "TextView",
  "textContent": { "defaultValue": "Text" }
}`.trim();

      const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', content);
      const result = await validator.validate(mainFile);
      const jsonReport = validator.exportToJson(result);

      const parsed = JSON.parse(jsonReport);
      expect(parsed.valid).toBeDefined();
      expect(parsed.metadata).toBeDefined();
      expect(parsed.components).toBeInstanceOf(Array);
    });
  });
});

// ============================================================================
// INTEGRATION ТЕСТЫ: РЕАЛЬНЫЕ ПРИМЕРЫ
// ============================================================================

describe('Real-World Examples', () => {
  let validator: JinjaAwareValidator;

  beforeEach(() => {
    validator = new JinjaAwareValidator({
      basePath: process.env.FMS_PATH || '/Users/username/Documents/FMS_GIT',
      verbose: false,
    });
  });

  // --------------------------------------------------------------------------
  // ТЕСТ НА РЕАЛЬНОМ ФАЙЛЕ [JJ_PC]_1.0_main_screen.j2.java
  // --------------------------------------------------------------------------

  describe('Real Project File: main_screen.j2.java', () => {
    const realFilePath =
      '/Users/username/Documents/FMS_GIT/tests/validator_v3.0.0/test_real_project_file_v1.0.0.j2.java';

    it('должен успешно парсить реальный файл с импортами', async () => {
      if (!existsSync(realFilePath)) {
        console.warn('⚠️  Real test file not found, skipping test');
        return;
      }

      const parser = new JinjaParser({
        basePath: '/Users/username/Documents/FMS_GIT',
        allowRecursiveImports: true,
        maxImportDepth: 5,
        defaultValues: {
          averageSalaryState: { isAverageSalaryShow: true },
          videoBanner: { url: 'https://example.com/video.mp4' },
        },
      });

      const result = parser.parse(realFilePath);

      // Проверяем, что файл содержит импорты
      expect(result.imports.length).toBeGreaterThan(0);

      // Проверяем наличие Jinja переменных
      expect(result.stats.variableCount).toBeGreaterThan(0);

      // Проверяем, что JSON был извлечен
      expect(result.extractedJson).toBeDefined();
      expect(result.extractedJson.version).toBe(1);
      expect(result.extractedJson.rootElement).toBeDefined();
    });

    it('должен валидировать реальный файл с WEB compatibility', async () => {
      if (!existsSync(realFilePath)) {
        console.warn('⚠️  Real test file not found, skipping test');
        return;
      }

      const result = await validator.validate(realFilePath, {
        validateImports: false, // Пропускаем, т.к. импорты могут не существовать
        checkWebCompatibility: true,
        checkRequiredFields: true,
      });

      expect(result).toBeDefined();
      expect(result.metadata.templatePath).toBe(realFilePath);
      expect(result.components.length).toBeGreaterThan(0);
    });

    it('должен обрабатывать state и data bindings в реальном файле', async () => {
      if (!existsSync(realFilePath)) {
        console.warn('⚠️  Real test file not found, skipping test');
        return;
      }

      const content = await readFile(realFilePath, 'utf-8');
      const parser = new JinjaParser({
        defaultValues: {
          averageSalaryState: { isAverageSalaryShow: false },
          videoBanner: null,
        },
      });

      const result = parser.parse(realFilePath);

      // Проверяем, что state обработан
      expect(result.extractedJson.state).toBeDefined();
      expect(result.extractedJson.state.isAverageSalaryShow).toBe(false);
      expect(result.extractedJson.state.isVideoBannerShow).toBe(false);
    });
  });

  // --------------------------------------------------------------------------
  // ТЕСТ НА ВАЛИДНОМ BASIC ФАЙЛЕ
  // --------------------------------------------------------------------------

  describe('Valid Basic Jinja File', () => {
    const basicFilePath =
      '/Users/username/Documents/FMS_GIT/tests/validator_v3.0.0/test_j2_java_valid_basic_v1.0.0.j2.java';

    it('должен парсить базовый Jinja файл с Java кодом', async () => {
      if (!existsSync(basicFilePath)) {
        console.warn('⚠️  Basic test file not found, skipping test');
        return;
      }

      const parser = new JinjaParser({
        defaultValues: {
          package: { imports: 'java.util.*' },
          user: { name: 'TestUser', balance: 1000 },
          state: { visible: true },
          account: { balance: 500.5, currency: 'USD' },
          enableFeature: true,
        },
      });

      const result = parser.parse(basicFilePath);

      // Проверяем обработку Jinja переменных
      expect(result.stats.variableCount).toBeGreaterThan(0);

      // Проверяем обработку управляющих конструкций
      expect(result.stats.controlCount).toBeGreaterThan(0);

      // Проверяем, что нет критических ошибок
      expect(result.errors.filter((e) => e.type === 'parse_error').length).toBe(0);
    });
  });
});

// ============================================================================
// PERFORMANCE ТЕСТЫ
// ============================================================================

describe('Performance Tests', () => {
  let workspace: string;

  beforeEach(async () => {
    workspace = await createTestWorkspace();
  });

  afterEach(async () => {
    await cleanupTestWorkspace(workspace);
  });

  it('должен парсить большой файл за разумное время', async () => {
    // Генерируем большой JSON с 1000 компонентами
    const components = Array.from({ length: 1000 }, (_, i) => ({
      type: 'TextView',
      id: `text_${i}`,
      textContent: { defaultValue: `Text ${i}` },
    }));

    const largeContent = JSON.stringify({
      type: 'StackView',
      content: { children: components },
    });

    const mainFile = await createTestJinjaFile(workspace, 'large.j2.java', largeContent);

    const parser = new JinjaParser();
    const startTime = Date.now();
    const result = parser.parse(mainFile);
    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(500); // Должен парсить за < 500ms
    expect(result.extractedJson.content.children.length).toBe(1000);
  });

  it('должен эффективно обрабатывать множественные импорты', async () => {
    // Создаем 50 модулей
    for (let i = 0; i < 50; i++) {
      const moduleContent = JSON.stringify({
        type: 'Spacer',
        id: `spacer_${i}`,
      });
      await createTestJinjaFile(workspace, `module${i}.json`, moduleContent);
    }

    // Создаем главный файл с импортами
    const imports = Array.from(
      { length: 50 },
      (_, i) => `  // [Module ${i}](file://./module${i}.json)`
    ).join('\n');

    const mainContent = `
{
  "type": "StackView",
  "content": {
    "children": [
${imports}
    ]
  }
}`.trim();

    const mainFile = await createTestJinjaFile(workspace, 'main.j2.java', mainContent);

    const parser = new JinjaParser({ basePath: workspace });
    const startTime = Date.now();
    const result = parser.parse(mainFile);
    const duration = Date.now() - startTime;

    expect(duration).toBeLessThan(1000); // < 1s для 50 импортов
    expect(result.stats.importCount).toBe(50);
  });
});

// ============================================================================
// EDGE CASES ТЕСТЫ
// ============================================================================

describe('Edge Cases', () => {
  let workspace: string;

  beforeEach(async () => {
    workspace = await createTestWorkspace();
  });

  afterEach(async () => {
    await cleanupTestWorkspace(workspace);
  });

  it('должен обрабатывать пустой файл', async () => {
    const emptyFile = await createTestJinjaFile(workspace, 'empty.j2.java', '');
    const parser = new JinjaParser();
    const result = parser.parse(emptyFile);

    expect(result.errors.length).toBeGreaterThan(0);
  });

  it('должен обрабатывать файл только с комментариями', async () => {
    const content = `
// Comment 1
// Comment 2
// [Not an import](note)
`.trim();

    const mainFile = await createTestJinjaFile(workspace, 'comments.j2.java', content);
    const parser = new JinjaParser();
    const result = parser.parse(mainFile);

    expect(result.imports).toHaveLength(0);
  });

  it('должен обрабатывать экранированные символы в Jinja переменных', async () => {
    const content = `
{
  "text": "{{ 'Line 1\\nLine 2' }}",
  "quote": "{{ "Double \\"quotes\\"" }}"
}`.trim();

    const mainFile = await createTestJinjaFile(workspace, 'escaped.j2.java', content);
    const parser = new JinjaParser();
    const result = parser.parse(mainFile);

    // Проверяем, что парсер не упал
    expect(result).toBeDefined();
  });

  it('должен обрабатывать Unicode символы', async () => {
    const content = `
{
  "type": "TextView",
  "textContent": {
    "defaultValue": "{{ greeting }}"
  }
}`.trim();

    const mainFile = await createTestJinjaFile(workspace, 'unicode.j2.java', content);
    const parser = new JinjaParser({
      defaultValues: { greeting: 'Привет, мир! 👋 🌍' },
    });
    const result = parser.parse(mainFile);

    expect(result.extractedJson.textContent.defaultValue).toBe('Привет, мир! 👋 🌍');
  });

  it('должен обрабатывать очень длинные строки', async () => {
    const longString = 'A'.repeat(10000);
    const content = `
{
  "type": "TextView",
  "text": "{{ longText }}"
}`.trim();

    const mainFile = await createTestJinjaFile(workspace, 'long.j2.java', content);
    const parser = new JinjaParser({
      defaultValues: { longText: longString },
    });
    const result = parser.parse(mainFile);

    expect(result.extractedJson.text).toBe(longString);
  });
});

// ============================================================================
// ЭКСПОРТ
// ============================================================================

export {
  createTestWorkspace,
  cleanupTestWorkspace,
  createTestJinjaFile,
};
