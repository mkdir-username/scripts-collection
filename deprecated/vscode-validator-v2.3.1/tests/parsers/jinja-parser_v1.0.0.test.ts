/**
 * Jinja Parser Tests
 * @version 1.0.0
 * @created 2025-10-07
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import { JinjaParser } from '../../src/parsers/jinja-parser_v1.0.0.js';
import { ParseErrorType } from '../../src/parsers/types_v1.0.0.js';
import { writeFileSync, unlinkSync, mkdirSync } from 'fs';
import { join } from 'path';

describe('JinjaParser', () => {
  let parser: JinjaParser;
  const testDir = join(__dirname, '.tmp');
  const testFile = join(testDir, 'test.j2.java');
  const importFile = join(testDir, 'import.json');

  beforeEach(() => {
    parser = new JinjaParser({ basePath: testDir });
    mkdirSync(testDir, { recursive: true });
  });

  afterEach(() => {
    try {
      unlinkSync(testFile);
      unlinkSync(importFile);
    } catch {}
  });

  describe('parse()', () => {
    it('должен парсить простой шаблон без переменных', async () => {
      const template = '{"type": "ButtonView", "text": "Click me"}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data).not.toBeNull();
      expect(result.data!.extractedJson.type).toBe('ButtonView');
    });

    it('должен заменять переменные значениями по умолчанию', async () => {
      const template = '{"enabled": {{ isEnabled }}, "count": {{ itemCount }}}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.extractedJson.enabled).toBe(false); // isEnabled -> false
      expect(result.data!.extractedJson.count).toBe(0); // itemCount -> 0
      expect(result.data!.stats.variableCount).toBe(2);
    });

    it('должен обрабатывать импорты', async () => {
      const importData = { imported: true, value: 42 };
      writeFileSync(importFile, JSON.stringify(importData));

      const template = `// [Import Data](file://${importFile})`;
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.imports).toHaveLength(1);
      expect(result.data!.imports[0].content).toEqual(importData);
      expect(result.data!.stats.importCount).toBe(1);
    });

    it('должен удалять управляющие конструкции', async () => {
      const template = `
{
  "type": "ButtonView",
  {% if condition %}
  "optional": true,
  {% endif %}
  "text": "Button"
}`;
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.stats.controlCount).toBeGreaterThan(0);
    });

    it('должен обрабатывать комбинацию импортов и переменных', async () => {
      const importData = { base: 'value' };
      writeFileSync(importFile, JSON.stringify(importData));

      const template = `
{
  "config": // [Config](file://${importFile}),
  "enabled": {{ isEnabled }},
  "count": {{ count }}
}`;
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.stats.importCount).toBe(1);
      expect(result.data!.stats.variableCount).toBe(2);
    });
  });

  describe('Variable Inference', () => {
    it('должен выводить boolean для is* переменных', async () => {
      const template = '{"isEnabled": {{ isEnabled }}, "hasData": {{ hasData }}}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.data!.extractedJson.isEnabled).toBe(false);
      expect(result.data!.extractedJson.hasData).toBe(false);
    });

    it('должен выводить number для count переменных', async () => {
      const template = '{"itemCount": {{ itemCount }}, "totalSize": {{ totalSize }}}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.data!.extractedJson.itemCount).toBe(0);
      expect(result.data!.extractedJson.totalSize).toBe(0);
    });

    it('должен выводить array для list переменных', async () => {
      const template = '{"items": {{ itemList }}, "elements": {{ elements }}}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.data!.extractedJson.items).toEqual([]);
      expect(result.data!.extractedJson.elements).toEqual([]);
    });

    it('должен выводить object для config переменных', async () => {
      const template = '{"config": {{ configData }}, "options": {{ options }}}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.data!.extractedJson.config).toEqual({});
      expect(result.data!.extractedJson.options).toEqual({});
    });

    it('должен выводить null для null переменных', async () => {
      const template = '{"value": {{ nullValue }}}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.data!.extractedJson.value).toBeNull();
    });

    it('должен использовать пустую строку по умолчанию', async () => {
      const template = '{"unknown": {{ unknownVariable }}}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.data!.extractedJson.unknown).toBe('');
    });
  });

  describe('Import Handling', () => {
    it('должен обнаруживать отсутствующие файлы', async () => {
      const template = '// [Missing](file:///nonexistent.json)';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors[0].type).toBe(ParseErrorType.FILE_NOT_FOUND);
    });

    it('должен обрабатывать ошибки парсинга импортов', async () => {
      writeFileSync(importFile, '{invalid json}');

      const template = `// [Invalid](file://${importFile})`;
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(false);
      expect(result.errors.some(e => e.type === ParseErrorType.INVALID_JSON)).toBe(true);
    });

    it('должен проверять глубину импорта', async () => {
      const deepParser = new JinjaParser({
        basePath: testDir,
        maxImportDepth: 1,
      });

      const importData = { data: true };
      writeFileSync(importFile, JSON.stringify(importData));

      const template = `// [Deep Import](file://${importFile})`;
      writeFileSync(testFile, template);

      const result = await deepParser.parse(testFile);

      // Первый уровень должен работать
      expect(result.success).toBe(true);
    });
  });

  describe('Source Mapping', () => {
    it('должен строить source map для импортов', async () => {
      const importData = { value: 1 };
      writeFileSync(importFile, JSON.stringify(importData));

      const template = `// [Data](file://${importFile})`;
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.sourceMap.length).toBeGreaterThan(0);

      const importMapping = result.data!.sourceMap.find(
        m => m.tokenType === 'import'
      );
      expect(importMapping).toBeDefined();
    });

    it('должен строить source map для переменных', async () => {
      const template = '{"value": {{ myVar }}}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);

      const variableMapping = result.data!.sourceMap.find(
        m => m.tokenType === 'variable'
      );
      expect(variableMapping).toBeDefined();
    });

    it('должен строить source map для управляющих конструкций', async () => {
      const template = '{% if true %}{"value": 1}{% endif %}';
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      const controlMapping = result.data!.sourceMap.find(
        m => m.tokenType === 'control'
      );
      expect(controlMapping).toBeDefined();
    });
  });

  describe('validate()', () => {
    it('должен валидировать корректный шаблон', async () => {
      const template = '{"type": "ButtonView"}';
      writeFileSync(testFile, template);

      const isValid = await parser.validate(testFile);

      expect(isValid).toBe(true);
    });

    it('должен отклонять шаблон с ошибками', async () => {
      const template = '// [Missing](file:///nonexistent.json)';
      writeFileSync(testFile, template);

      const isValid = await parser.validate(testFile);

      expect(isValid).toBe(false);
    });
  });

  describe('Configuration', () => {
    it('должен использовать кастомные значения переменных', async () => {
      const customDefaults = new Map([['myVar', 'custom value']]);

      const customParser = new JinjaParser({
        basePath: testDir,
        variableDefaults: customDefaults,
      });

      const template = '{"value": {{ myVar }}}';
      writeFileSync(testFile, template);

      const result = await customParser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.extractedJson.value).toBe('custom value');
    });

    it('должен отключать source map при необходимости', async () => {
      const noMapParser = new JinjaParser({
        basePath: testDir,
        buildSourceMap: false,
      });

      const template = '{"value": {{ myVar }}}';
      writeFileSync(testFile, template);

      const result = await noMapParser.parse(testFile);

      expect(result.success).toBe(true);
      // Source map не должен строиться
      expect(result.data!.sourceMap).toHaveLength(0);
    });
  });

  describe('Statistics', () => {
    it('должен собирать статистику парсинга', async () => {
      const importData = { data: true };
      writeFileSync(importFile, JSON.stringify(importData));

      const template = `
{
  "config": // [Config](file://${importFile}),
  "enabled": {{ isEnabled }},
  "count": {{ count }},
  {% if true %}
  "optional": true
  {% endif %}
}`;
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.stats.importCount).toBe(1);
      expect(result.data!.stats.variableCount).toBe(2);
      expect(result.data!.stats.controlCount).toBeGreaterThan(0);
      expect(result.data!.stats.totalSizeBytes).toBeGreaterThan(0);
    });
  });

  describe('Complex Scenarios', () => {
    it('должен обрабатывать реальный SDUI шаблон', async () => {
      const baseComponent = {
        type: 'StackView',
        orientation: 'vertical',
      };
      writeFileSync(importFile, JSON.stringify(baseComponent));

      const template = `
{
  "base": // [Base Component](file://${importFile}),
  "components": [
    {
      "type": "ButtonView",
      "text": {{ buttonText }},
      "enabled": {{ isEnabled }}
    },
    {
      "type": "TextView",
      "text": {{ headerText }}
    }
  ],
  "metadata": {
    "version": {{ version }},
    "itemCount": {{ itemCount }}
  }
}`;
      writeFileSync(testFile, template);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.extractedJson.base).toEqual(baseComponent);
      expect(result.data!.extractedJson.components).toHaveLength(2);
      expect(result.data!.stats.importCount).toBe(1);
      expect(result.data!.stats.variableCount).toBeGreaterThan(0);
    });
  });
});
