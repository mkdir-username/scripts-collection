/**
 * JSON Parser Tests
 * @version 1.0.0
 * @created 2025-10-07
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import { JsonParser } from '../../src/parsers/json-parser_v1.0.0.js';
import { ParseErrorType } from '../../src/parsers/types_v1.0.0.js';
import { writeFileSync, unlinkSync, mkdirSync } from 'fs';
import { join } from 'path';

describe('JsonParser', () => {
  let parser: JsonParser;
  const testDir = join(__dirname, '.tmp');
  const testFile = join(testDir, 'test.json');

  beforeEach(() => {
    parser = new JsonParser();
    mkdirSync(testDir, { recursive: true });
  });

  afterEach(() => {
    try {
      unlinkSync(testFile);
    } catch {}
  });

  describe('parse()', () => {
    it('должен успешно парсить валидный JSON', async () => {
      const json = { name: 'test', value: 42 };
      writeFileSync(testFile, JSON.stringify(json, null, 2));

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data).not.toBeNull();
      expect(result.data!.json).toEqual(json);
      expect(result.errors).toHaveLength(0);
    });

    it('должен возвращать ошибку для невалидного JSON', async () => {
      writeFileSync(testFile, '{ "invalid": }');

      const result = await parser.parse(testFile);

      expect(result.success).toBe(false);
      expect(result.data).toBeNull();
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors[0].type).toBe(ParseErrorType.INVALID_JSON);
    });

    it('должен строить position map', async () => {
      const json = {
        component: {
          type: 'ButtonView',
          properties: {
            text: 'Click me',
          },
        },
      };
      writeFileSync(testFile, JSON.stringify(json, null, 2));

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data).not.toBeNull();

      const posMap = result.data!.positionMap;
      expect(posMap.byPath.size).toBeGreaterThan(0);
      expect(posMap.byPointer.size).toBeGreaterThan(0);
      expect(posMap.totalLines).toBeGreaterThan(0);
    });

    it('должен находить позицию по пути', async () => {
      const json = {
        component: {
          type: 'ButtonView',
        },
      };
      writeFileSync(testFile, JSON.stringify(json, null, 2));

      const result = await parser.parse(testFile);
      expect(result.success).toBe(true);

      const position = parser.findPosition(
        result.data!.positionMap,
        'component.type'
      );

      expect(position).not.toBeNull();
      expect(position!.line).toBeGreaterThan(0);
      expect(position!.column).toBeGreaterThan(0);
    });

    it('должен обрабатывать вложенные массивы', async () => {
      const json = {
        items: [
          { id: 1, name: 'Item 1' },
          { id: 2, name: 'Item 2' },
        ],
      };
      writeFileSync(testFile, JSON.stringify(json, null, 2));

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.json.items).toHaveLength(2);

      const position = parser.findPosition(
        result.data!.positionMap,
        'items[0].name'
      );
      expect(position).not.toBeNull();
    });
  });

  describe('parseSync()', () => {
    it('должен синхронно парсить JSON', () => {
      const json = { sync: true };
      writeFileSync(testFile, JSON.stringify(json));

      const result = parser.parseSync(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.json).toEqual(json);
    });
  });

  describe('validate()', () => {
    it('должен валидировать корректный JSON', async () => {
      writeFileSync(testFile, '{"valid": true}');

      const isValid = await parser.validate(testFile);

      expect(isValid).toBe(true);
    });

    it('должен отклонять некорректный JSON', async () => {
      writeFileSync(testFile, '{invalid}');

      const isValid = await parser.validate(testFile);

      expect(isValid).toBe(false);
    });
  });

  describe('Configuration', () => {
    it('должен использовать кастомный reviver', async () => {
      const json = { date: '2025-10-07' };
      writeFileSync(testFile, JSON.stringify(json));

      const customParser = new JsonParser({
        reviver: (key, value) => {
          if (key === 'date') {
            return new Date(value);
          }
          return value;
        },
      });

      const result = await customParser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.json.date).toBeInstanceOf(Date);
    });

    it('должен обновлять конфигурацию', () => {
      parser.updateConfig({ strict: false });

      const config = parser.getConfig();
      expect(config.strict).toBe(false);
    });
  });

  describe('Position Map Advanced Features', () => {
    it('должен кэшировать вложенные пути', async () => {
      const json = {
        level1: {
          level2: {
            level3: {
              value: 'deep',
            },
          },
        },
      };
      writeFileSync(testFile, JSON.stringify(json, null, 2));

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      const posMap = result.data!.positionMap;

      // Проверяем кэш вложенных путей
      expect(posMap.nestedCache.has('level1')).toBe(true);
      expect(posMap.nestedCache.has('level1.level2')).toBe(true);
      expect(posMap.nestedCache.has('level1.level2.level3')).toBe(true);
    });

    it('должен отслеживать родительские пути', async () => {
      const json = {
        parent: {
          child: 'value',
        },
      };
      writeFileSync(testFile, JSON.stringify(json, null, 2));

      const result = await parser.parse(testFile);

      const childPosition = parser.findPosition(
        result.data!.positionMap,
        'parent.child'
      );

      expect(childPosition).not.toBeNull();
      expect(childPosition!.parent).toBeDefined();
    });

    it('должен обрабатывать массивы с объектами', async () => {
      const json = {
        components: [
          { type: 'ButtonView', text: 'Button 1' },
          { type: 'TextView', text: 'Text 1' },
        ],
      };
      writeFileSync(testFile, JSON.stringify(json, null, 2));

      const result = await parser.parse(testFile);

      // Проверяем позиции элементов массива
      const pos0 = parser.findPosition(result.data!.positionMap, 'components[0].type');
      const pos1 = parser.findPosition(result.data!.positionMap, 'components[1].type');

      expect(pos0).not.toBeNull();
      expect(pos1).not.toBeNull();
      expect(pos0!.line).not.toBe(pos1!.line);
    });
  });

  describe('Error Handling', () => {
    it('должен предоставлять контекст ошибки', async () => {
      const invalid = '{"key": "value",}'; // trailing comma
      writeFileSync(testFile, invalid);

      const result = await parser.parse(testFile);

      expect(result.success).toBe(false);
      expect(result.errors[0].context).toBeDefined();
      expect(result.errors[0].position.line).toBeGreaterThan(0);
    });

    it('должен предлагать исправления', async () => {
      writeFileSync(testFile, '{invalid}');

      const result = await parser.parse(testFile);

      expect(result.errors[0].suggestion).toBeDefined();
    });
  });

  describe('Performance', () => {
    it('должен быстро обрабатывать большие JSON файлы', async () => {
      const largeJson = {
        items: Array.from({ length: 1000 }, (_, i) => ({
          id: i,
          name: `Item ${i}`,
          data: { value: i * 2 },
        })),
      };
      writeFileSync(testFile, JSON.stringify(largeJson, null, 2));

      const startTime = Date.now();
      const result = await parser.parse(testFile);
      const parseTime = Date.now() - startTime;

      expect(result.success).toBe(true);
      expect(parseTime).toBeLessThan(1000); // Должен завершиться за 1 секунду
      expect(result.metadata.parseTimeMs).toBeLessThan(1000);
    });

    it('должен эффективно строить position map', async () => {
      const json = {
        components: Array.from({ length: 100 }, (_, i) => ({
          type: 'Component',
          id: i,
        })),
      };
      writeFileSync(testFile, JSON.stringify(json, null, 2));

      const result = await parser.parse(testFile);

      expect(result.success).toBe(true);
      expect(result.data!.positionMap.buildTimeMs).toBeLessThan(100);
    });
  });
});
