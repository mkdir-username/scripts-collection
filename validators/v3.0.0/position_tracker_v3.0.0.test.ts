/**
 * Unit Tests для Position Tracker v3.0.0
 *
 * @version 3.0.0
 * @author Claude Code
 * @date 2025-10-05
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import {
  PositionTracker,
  TokenType,
  normalizePath,
  extractPatterns,
  hashString
} from './position_tracker_v3.0.0';

// ============================================================================
// ТЕСТОВЫЕ ДАННЫЕ
// ============================================================================

const SIMPLE_JSON = `{
  "name": "test",
  "value": 42,
  "nested": {
    "deep": "value"
  }
}`;

const ARRAY_JSON = `{
  "items": [
    { "id": 1 },
    { "id": 2 },
    { "id": 3 }
  ]
}`;

const COMPLEX_JSON = `{
  "component": {
    "type": "ButtonView",
    "content": {
      "textContent": {
        "text": "Click me"
      }
    },
    "actions": [
      {
        "type": "HttpAction",
        "url": "/api/submit"
      }
    ]
  }
}`;

const JSON5_SAMPLE = `{
  // Это комментарий
  "name": "test",
  /* Многострочный
     комментарий */
  "value": 42,
  "trailing": "comma",
}`;

const MINIFIED_JSON = `{"name":"test","value":42,"nested":{"deep":"value"}}`;

// ============================================================================
// УТИЛИТЫ
// ============================================================================

describe('Утилиты', () => {
  describe('normalizePath', () => {
    it('должен нормализовать простой путь', () => {
      expect(normalizePath('a.b.c')).toBe('a.b.c');
    });

    it('должен нормализовать путь с массивами', () => {
      expect(normalizePath('a[0].b[1].c')).toBe('a[0].b[1].c');
    });

    it('должен убирать лишние точки и скобки', () => {
      expect(normalizePath('a].b')).toBe('a.b');
      expect(normalizePath('a.[b')).toBe('a[b');
    });
  });

  describe('extractPatterns', () => {
    it('должен извлекать паттерны из простого пути', () => {
      const patterns = extractPatterns('a.b.c');
      expect(patterns).toContain('*.c');
      expect(patterns).toContain('a.*');
      expect(patterns).toContain('a.b.*');
    });

    it('должен извлекать паттерны с wildcards для массивов', () => {
      const patterns = extractPatterns('items[0].name');
      expect(patterns).toContain('items[*].name');
      expect(patterns).toContain('*.name');
    });

    it('должен возвращать уникальные паттерны', () => {
      const patterns = extractPatterns('a.b.c');
      const uniquePatterns = [...new Set(patterns)];
      expect(patterns.length).toBe(uniquePatterns.length);
    });
  });

  describe('hashString', () => {
    it('должен генерировать одинаковый хеш для одной строки', () => {
      const str = 'test string';
      expect(hashString(str)).toBe(hashString(str));
    });

    it('должен генерировать разные хеши для разных строк', () => {
      expect(hashString('test1')).not.toBe(hashString('test2'));
    });

    it('должен возвращать шестнадцатеричную строку', () => {
      const hash = hashString('test');
      expect(hash).toMatch(/^[0-9a-f]+$/);
    });
  });
});

// ============================================================================
// POSITION TRACKER - БАЗОВЫЕ ФУНКЦИИ
// ============================================================================

describe('PositionTracker - Базовые функции', () => {
  let tracker: PositionTracker;

  beforeEach(() => {
    tracker = new PositionTracker({
      enableCaching: false // Отключаем кэш для тестов
    });
  });

  describe('buildPositionMap', () => {
    it('должен построить position map для простого JSON', () => {
      const map = tracker.buildPositionMap(SIMPLE_JSON);

      expect(map).toBeDefined();
      expect(map.version).toBe('3.0.0');
      expect(map.totalLines).toBeGreaterThan(0);
      expect(map.stats.tokenCount).toBeGreaterThan(0);
    });

    it('должен корректно индексировать вложенные объекты', () => {
      const map = tracker.buildPositionMap(SIMPLE_JSON);

      expect(map.byPath.has('name')).toBe(true);
      expect(map.byPath.has('nested')).toBe(true);
      expect(map.byPath.has('nested.deep')).toBe(true);
    });

    it('должен корректно индексировать массивы', () => {
      const map = tracker.buildPositionMap(ARRAY_JSON);

      expect(map.byPath.has('items')).toBe(true);
      expect(map.byPath.has('items[0]')).toBe(true);
      expect(map.byPath.has('items[0].id')).toBe(true);
      expect(map.byPath.has('items[1].id')).toBe(true);
    });

    it('должен сохранять информацию о типах токенов', () => {
      const map = tracker.buildPositionMap(SIMPLE_JSON);
      const namePos = map.byPath.get('name');

      expect(namePos).toBeDefined();
      expect(namePos?.tokenType).toBe(TokenType.KEY);
      expect(namePos?.line).toBeGreaterThan(0);
      expect(namePos?.column).toBeGreaterThan(0);
    });

    it('должен работать с минифицированным JSON', () => {
      const map = tracker.buildPositionMap(MINIFIED_JSON);

      expect(map.byPath.has('name')).toBe(true);
      expect(map.byPath.has('nested.deep')).toBe(true);
      expect(map.totalLines).toBe(1);
    });
  });

  describe('findLineNumber', () => {
    beforeEach(() => {
      tracker.buildPositionMap(SIMPLE_JSON);
    });

    it('должен находить строку по точному пути', () => {
      const line = tracker.findLineNumber('name');
      expect(line).toBeGreaterThan(0);
    });

    it('должен находить строку для вложенного пути', () => {
      const line = tracker.findLineNumber('nested.deep');
      expect(line).toBeGreaterThan(0);
    });

    it('должен возвращать 1 для несуществующего пути без fallback', () => {
      const line = tracker.findLineNumber('nonexistent', '', {
        fallbackToParent: false
      });
      expect(line).toBe(1);
    });

    it('должен находить родительский путь при fallback', () => {
      const line = tracker.findLineNumber('nested.deep.nonexistent', '', {
        fallbackToParent: true
      });
      expect(line).toBeGreaterThan(0);
    });
  });

  describe('findPosition', () => {
    beforeEach(() => {
      tracker.buildPositionMap(SIMPLE_JSON);
    });

    it('должен возвращать полную информацию о позиции', () => {
      const pos = tracker.findPosition('name');

      expect(pos).toBeDefined();
      expect(pos?.line).toBeGreaterThan(0);
      expect(pos?.column).toBeGreaterThan(0);
      expect(pos?.offset).toBeGreaterThanOrEqual(0);
    });

    it('должен возвращать информацию о типе токена', () => {
      const pos = tracker.findPosition('name');
      expect(pos?.tokenType).toBe(TokenType.KEY);
    });
  });
});

// ============================================================================
// POSITION TRACKER - JSON5 ПОДДЕРЖКА
// ============================================================================

describe('PositionTracker - JSON5 поддержка', () => {
  let tracker: PositionTracker;

  beforeEach(() => {
    tracker = new PositionTracker({
      json5Support: true,
      enableCaching: false
    });
  });

  it('должен игнорировать однострочные комментарии', () => {
    const map = tracker.buildPositionMap(JSON5_SAMPLE);

    expect(map.byPath.has('name')).toBe(true);
    expect(map.byPath.has('value')).toBe(true);
    expect(map.stats.commentCount).toBeGreaterThan(0);
  });

  it('должен игнорировать многострочные комментарии', () => {
    const map = tracker.buildPositionMap(JSON5_SAMPLE);
    expect(map.stats.commentCount).toBeGreaterThanOrEqual(2);
  });

  it('должен обрабатывать trailing commas', () => {
    const jsonWithTrailing = `{
      "a": 1,
      "b": 2,
    }`;

    const map = tracker.buildPositionMap(jsonWithTrailing);
    expect(map.byPath.has('a')).toBe(true);
    expect(map.byPath.has('b')).toBe(true);
  });
});

// ============================================================================
// POSITION TRACKER - PATTERN MATCHING
// ============================================================================

describe('PositionTracker - Pattern Matching', () => {
  let tracker: PositionTracker;

  beforeEach(() => {
    tracker = new PositionTracker({
      buildPatternIndex: true,
      enableCaching: false
    });
  });

  it('должен строить индекс паттернов', () => {
    const map = tracker.buildPositionMap(ARRAY_JSON);
    expect(map.byPattern.size).toBeGreaterThan(0);
  });

  it('должен находить все позиции по паттерну', () => {
    tracker.buildPositionMap(ARRAY_JSON);
    const positions = tracker.findAllByPattern('items[*].id');

    expect(positions.length).toBe(3);
    positions.forEach(pos => {
      expect(pos.line).toBeGreaterThan(0);
    });
  });

  it('должен находить позиции по wildcard паттерну', () => {
    tracker.buildPositionMap(COMPLEX_JSON);
    const positions = tracker.findAllByPattern('*.type');

    expect(positions.length).toBeGreaterThan(0);
  });

  it('должен использовать pattern matching при поиске', () => {
    tracker.buildPositionMap(ARRAY_JSON);

    const line = tracker.findLineNumber('items[10].id', '', {
      usePatternMatching: true
    });

    expect(line).toBeGreaterThan(0);
  });
});

// ============================================================================
// POSITION TRACKER - КЭШИРОВАНИЕ
// ============================================================================

describe('PositionTracker - Кэширование', () => {
  beforeEach(() => {
    PositionTracker.clearCache();
  });

  it('должен кэшировать результаты', () => {
    const tracker1 = new PositionTracker({
      enableCaching: true,
      filePath: '/test/file1.json'
    });

    const map1 = tracker1.buildPositionMap(SIMPLE_JSON);

    const tracker2 = new PositionTracker({
      enableCaching: true,
      filePath: '/test/file1.json'
    });

    const map2 = tracker2.buildPositionMap(SIMPLE_JSON);

    // Должны быть одинаковые хеши
    expect(map1.sourceHash).toBe(map2.sourceHash);
  });

  it('должен инвалидировать кэш при изменении файла', () => {
    const tracker1 = new PositionTracker({
      enableCaching: true,
      filePath: '/test/file1.json'
    });

    const map1 = tracker1.buildPositionMap(SIMPLE_JSON);

    const tracker2 = new PositionTracker({
      enableCaching: true,
      filePath: '/test/file1.json'
    });

    const modifiedJson = SIMPLE_JSON + '\n// Modified';
    const map2 = tracker2.buildPositionMap(modifiedJson);

    // Хеши должны отличаться
    expect(map1.sourceHash).not.toBe(map2.sourceHash);
  });

  it('должен возвращать статистику кэша', () => {
    const stats = PositionTracker.getCacheStats();

    expect(stats).toBeDefined();
    expect(stats.size).toBeGreaterThanOrEqual(0);
    expect(stats.maxSize).toBeGreaterThan(0);
  });

  it('должен очищать кэш', () => {
    const tracker = new PositionTracker({
      enableCaching: true,
      filePath: '/test/file1.json'
    });

    tracker.buildPositionMap(SIMPLE_JSON);

    PositionTracker.clearCache();

    const stats = PositionTracker.getCacheStats();
    expect(stats.size).toBe(0);
  });
});

// ============================================================================
// POSITION TRACKER - ПРОИЗВОДИТЕЛЬНОСТЬ
// ============================================================================

describe('PositionTracker - Производительность', () => {
  it('должен обрабатывать большие файлы за разумное время', () => {
    // Генерируем большой JSON
    const largeJson = JSON.stringify({
      items: Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `Item ${i}`,
        data: {
          value: i * 2,
          label: `Label ${i}`
        }
      }))
    }, null, 2);

    const tracker = new PositionTracker({ enableCaching: false });

    const startTime = Date.now();
    const map = tracker.buildPositionMap(largeJson);
    const parseTime = Date.now() - startTime;

    // Должно занять меньше 1 секунды
    expect(parseTime).toBeLessThan(1000);
    expect(map.stats.tokenCount).toBeGreaterThan(1000);
  });

  it('должен эффективно находить позиции в больших файлах', () => {
    const largeJson = JSON.stringify({
      items: Array.from({ length: 1000 }, (_, i) => ({
        id: i,
        name: `Item ${i}`
      }))
    }, null, 2);

    const tracker = new PositionTracker({ enableCaching: false });
    tracker.buildPositionMap(largeJson);

    const startTime = Date.now();

    // 100 поисков
    for (let i = 0; i < 100; i++) {
      tracker.findLineNumber(`items[${i}].name`);
    }

    const searchTime = Date.now() - startTime;

    // Все поиски должны занять меньше 100ms (в среднем < 1ms на поиск)
    expect(searchTime).toBeLessThan(100);
  });
});

// ============================================================================
// POSITION TRACKER - EDGE CASES
// ============================================================================

describe('PositionTracker - Edge Cases', () => {
  let tracker: PositionTracker;

  beforeEach(() => {
    tracker = new PositionTracker({ enableCaching: false });
  });

  it('должен обрабатывать пустой JSON', () => {
    const map = tracker.buildPositionMap('{}');

    expect(map).toBeDefined();
    expect(map.totalLines).toBe(1);
  });

  it('должен обрабатывать JSON с unicode символами', () => {
    const unicodeJson = `{
      "name": "Тест",
      "emoji": "🚀",
      "chinese": "中文"
    }`;

    const map = tracker.buildPositionMap(unicodeJson);

    expect(map.byPath.has('name')).toBe(true);
    expect(map.byPath.has('emoji')).toBe(true);
    expect(map.byPath.has('chinese')).toBe(true);
  });

  it('должен обрабатывать глубоко вложенные структуры', () => {
    const deepJson = `{
      "a": {
        "b": {
          "c": {
            "d": {
              "e": {
                "f": "value"
              }
            }
          }
        }
      }
    }`;

    const map = tracker.buildPositionMap(deepJson);

    expect(map.byPath.has('a.b.c.d.e.f')).toBe(true);
  });

  it('должен обрабатывать escaped кавычки в строках', () => {
    const jsonWithEscapes = `{
      "text": "String with \\"quotes\\" inside"
    }`;

    const map = tracker.buildPositionMap(jsonWithEscapes);

    expect(map.byPath.has('text')).toBe(true);
  });

  it('должен обрабатывать массивы массивов', () => {
    const nestedArrays = `{
      "matrix": [
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9]
      ]
    }`;

    const map = tracker.buildPositionMap(nestedArrays);

    expect(map.byPath.has('matrix')).toBe(true);
    expect(map.byPath.has('matrix[0]')).toBe(true);
    expect(map.byPath.has('matrix[1]')).toBe(true);
  });

  it('должен выбрасывать ошибку если position map не построена', () => {
    const newTracker = new PositionTracker();

    expect(() => {
      newTracker.findLineNumber('test');
    }).toThrow('Position map not built');
  });
});

// ============================================================================
// ИНТЕГРАЦИОННЫЕ ТЕСТЫ
// ============================================================================

describe('PositionTracker - Интеграционные тесты', () => {
  it('должен корректно работать с реальным SDUI контрактом', () => {
    const sduiContract = `{
      "type": "StackView",
      "id": "mainStack",
      "children": [
        {
          "type": "ButtonView",
          "content": {
            "textContent": {
              "text": "Submit"
            }
          },
          "actions": [
            {
              "type": "HttpAction",
              "url": "/api/submit",
              "method": "POST"
            }
          ]
        }
      ]
    }`;

    const tracker = new PositionTracker({
      json5Support: false,
      buildPatternIndex: true,
      enableCaching: false
    });

    const map = tracker.buildPositionMap(sduiContract);

    // Проверяем базовые пути
    expect(map.byPath.has('type')).toBe(true);
    expect(map.byPath.has('children')).toBe(true);
    expect(map.byPath.has('children[0].type')).toBe(true);

    // Проверяем вложенные пути
    expect(map.byPath.has('children[0].content.textContent.text')).toBe(true);
    expect(map.byPath.has('children[0].actions[0].url')).toBe(true);

    // Проверяем pattern matching
    const actionPositions = tracker.findAllByPattern('*.type');
    expect(actionPositions.length).toBeGreaterThan(0);

    // Проверяем производительность
    expect(map.stats.parseTimeMs).toBeLessThan(100);
  });
});
