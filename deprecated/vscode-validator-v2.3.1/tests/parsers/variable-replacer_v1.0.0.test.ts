/**
 * Variable Replacer Tests
 * @version 1.0.0
 * @created 2025-10-07
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import { VariableReplacer, ReplacementSource } from '../../src/parsers/variable-replacer_v1.0.0.js';
import { ParseErrorType } from '../../src/parsers/types_v1.0.0.js';

describe('VariableReplacer', () => {
  let replacer: VariableReplacer;

  beforeEach(() => {
    replacer = new VariableReplacer();
  });

  describe('parse()', () => {
    it('должен заменять простые переменные', async () => {
      const content = '{"value": {{ myVar }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('""'); // myVar -> ""
      expect(result.data!.stats.totalReplacements).toBe(1);
    });

    it('должен заменять множественные переменные', async () => {
      const content = '{"a": {{ var1 }}, "b": {{ var2 }}, "c": {{ var3 }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.stats.totalReplacements).toBe(3);
    });

    it('должен использовать кастомные значения', async () => {
      const customReplacer = new VariableReplacer({
        customDefaults: new Map([
          ['myVar', 'custom value'],
          ['count', 42],
        ]),
      });

      const content = '{"text": {{ myVar }}, "count": {{ count }}}';

      const result = await customReplacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('"custom value"');
      expect(result.data!.content).toContain('42');
    });
  });

  describe('Type Inference', () => {
    it('должен выводить boolean для is/has префиксов', async () => {
      const content = '{"enabled": {{ isEnabled }}, "data": {{ hasData }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('false');
      expect(result.data!.stats.byType.boolean).toBe(2);
    });

    it('должен выводить number для count/size суффиксов', async () => {
      const content = '{"count": {{ itemCount }}, "size": {{ totalSize }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('0');
      expect(result.data!.stats.byType.number).toBe(2);
    });

    it('должен выводить array для list суффиксов', async () => {
      const content = '{"items": {{ itemList }}, "data": {{ dataArray }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('[]');
      expect(result.data!.replacements.every(r => Array.isArray(r.replacedValue))).toBe(
        true
      );
    });

    it('должен выводить object для config/options суффиксов', async () => {
      const content = '{"config": {{ appConfig }}, "opts": {{ userOptions }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('{}');
    });

    it('должен выводить null для null переменных', async () => {
      const content = '{"value": {{ nullValue }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('null');
    });

    it('должен использовать пустую строку по умолчанию', async () => {
      const content = '{"unknown": {{ unknownVar }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('""');
    });
  });

  describe('Replacement Sources', () => {
    it('должен отмечать кастомные замены', async () => {
      const customReplacer = new VariableReplacer({
        customDefaults: new Map([['myVar', 'custom']]),
      });

      const content = '{"value": {{ myVar }}}';

      const result = await customReplacer.parse(content);

      expect(result.data!.replacements[0].source).toBe(
        ReplacementSource.CUSTOM_DEFAULTS
      );
      expect(result.data!.replacements[0].inferred).toBe(false);
    });

    it('должен отмечать выведенные замены', async () => {
      const content = '{"enabled": {{ isEnabled }}}';

      const result = await replacer.parse(content);

      expect(result.data!.replacements[0].source).toBe(ReplacementSource.INFERENCE);
      expect(result.data!.replacements[0].inferred).toBe(true);
    });
  });

  describe('Undefined Variables', () => {
    it('должен отслеживать неопределенные переменные', async () => {
      const strictReplacer = new VariableReplacer({
        defaultInferenceEnabled: false,
        allowUndefined: true,
      });

      const content = '{"value": {{ undefinedVar }}}';

      const result = await strictReplacer.parse(content);

      expect(result.data!.undefinedVariables.length).toBeGreaterThan(0);
      expect(result.data!.stats.undefinedReplacements).toBeGreaterThan(0);
    });

    it('должен выдавать ошибки для неопределенных переменных в strict режиме', async () => {
      const strictReplacer = new VariableReplacer({
        strict: true,
        defaultInferenceEnabled: false,
        allowUndefined: false,
      });

      const content = '{"value": {{ undefinedVar }}}';

      const result = await strictReplacer.parse(content);

      expect(result.success).toBe(false);
      expect(result.errors.some(e => e.type === ParseErrorType.UNRESOLVED_VARIABLE)).toBe(
        true
      );
    });
  });

  describe('Statistics', () => {
    it('должен собирать статистику по типам', async () => {
      const content = `{
        "bool": {{ isEnabled }},
        "num": {{ count }},
        "arr": {{ items }},
        "obj": {{ config }},
        "str": {{ text }}
      }`;

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.stats.totalReplacements).toBe(5);
      expect(result.data!.stats.inferredReplacements).toBe(5);
      expect(Object.keys(result.data!.stats.byType).length).toBeGreaterThan(0);
    });

    it('должен различать кастомные и выведенные замены', async () => {
      const mixedReplacer = new VariableReplacer({
        customDefaults: new Map([['custom', 'value']]),
      });

      const content = '{"custom": {{ custom }}, "inferred": {{ isEnabled }}}';

      const result = await mixedReplacer.parse(content);

      expect(result.data!.stats.customReplacements).toBe(1);
      expect(result.data!.stats.inferredReplacements).toBe(1);
    });
  });

  describe('Variable Extraction', () => {
    it('должен извлекать все переменные', () => {
      const content = '{"a": {{ var1 }}, "b": {{ var2 }}, "c": {{ var1 }}}';

      const variables = replacer.extractVariables(content);

      expect(variables.length).toBe(3); // var1 встречается 2 раза
      expect(variables.map(v => v.name)).toContain('var1');
      expect(variables.map(v => v.name)).toContain('var2');
    });

    it('должен предоставлять контекст для переменных', () => {
      const content = '{"value": {{ myVariable }}}';

      const variables = replacer.extractVariables(content);

      expect(variables[0].surroundingText).toBeTruthy();
      expect(variables[0].position.line).toBeGreaterThan(0);
      expect(variables[0].position.column).toBeGreaterThan(0);
    });
  });

  describe('Variable Statistics', () => {
    it('должен подсчитывать уникальные переменные', () => {
      const content = '{"a": {{ var1 }}, "b": {{ var2 }}, "c": {{ var1 }}}';

      const stats = replacer.getVariableStats(content);

      expect(stats.total).toBe(3);
      expect(stats.unique).toHaveLength(2);
      expect(stats.byOccurrence.get('var1')).toBe(2);
      expect(stats.byOccurrence.get('var2')).toBe(1);
    });
  });

  describe('Custom Strategies', () => {
    it('должен поддерживать кастомные стратегии вывода', async () => {
      replacer.addInferenceStrategy({
        name: 'custom-uuid',
        pattern: /uuid$/i,
        inferValue: () => '00000000-0000-0000-0000-000000000000',
        priority: 200,
      });

      const content = '{"id": {{ userUuid }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('00000000-0000-0000-0000-000000000000');
    });

    it('должен использовать приоритет стратегий', async () => {
      replacer.addInferenceStrategy({
        name: 'high-priority',
        pattern: /test/i,
        inferValue: () => 'high',
        priority: 1000,
      });

      replacer.addInferenceStrategy({
        name: 'low-priority',
        pattern: /test/i,
        inferValue: () => 'low',
        priority: 1,
      });

      const content = '{"value": {{ testVar }}}';

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('"high"');
    });
  });

  describe('Dynamic Updates', () => {
    it('должен добавлять кастомные значения динамически', async () => {
      const content = '{"value": {{ dynamicVar }}}';

      replacer.setCustomDefault('dynamicVar', 'dynamic value');

      const result = await replacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('dynamic value');
    });
  });

  describe('Escaping', () => {
    it('должен экранировать специальные символы', async () => {
      const escapingReplacer = new VariableReplacer({
        escapeOutput: true,
        customDefaults: new Map([['text', 'Line 1\nLine 2']]),
      });

      const content = '{"value": {{ text }}}';

      const result = await escapingReplacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.content).toContain('\\n');
    });

    it('должен пропускать экранирование при необходимости', async () => {
      const noEscapeReplacer = new VariableReplacer({
        escapeOutput: false,
        customDefaults: new Map([['text', 'Line 1\nLine 2']]),
      });

      const content = '{"value": {{ text }}}';

      const result = await noEscapeReplacer.parse(content);

      expect(result.success).toBe(true);
    });
  });

  describe('validate()', () => {
    it('должен валидировать контент с определенными переменными', async () => {
      const validatingReplacer = new VariableReplacer({
        customDefaults: new Map([['myVar', 'value']]),
      });

      const content = '{"value": {{ myVar }}}';

      const isValid = await validatingReplacer.validate(content);

      expect(isValid).toBe(true);
    });

    it('должен отклонять контент с неопределенными переменными', async () => {
      const strictReplacer = new VariableReplacer({
        defaultInferenceEnabled: false,
        strict: true,
      });

      const content = '{"value": {{ undefinedVar }}}';

      const isValid = await strictReplacer.validate(content);

      expect(isValid).toBe(false);
    });
  });

  describe('Complex Scenarios', () => {
    it('должен обрабатывать сложные шаблоны', async () => {
      const complexReplacer = new VariableReplacer({
        customDefaults: new Map([
          ['appName', 'MyApp'],
          ['version', '1.0.0'],
        ]),
      });

      const content = `{
        "application": {
          "name": {{ appName }},
          "version": {{ version }},
          "enabled": {{ isEnabled }},
          "userCount": {{ userCount }},
          "features": {{ featureList }},
          "settings": {{ appSettings }}
        }
      }`;

      const result = await complexReplacer.parse(content);

      expect(result.success).toBe(true);
      expect(result.data!.stats.totalReplacements).toBe(6);
      expect(result.data!.stats.customReplacements).toBe(2);
      expect(result.data!.stats.inferredReplacements).toBe(4);
    });
  });
});
