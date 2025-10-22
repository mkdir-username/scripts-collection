/**
 * Import Resolver Tests
 * @version 1.0.0
 * @created 2025-10-07
 */

import { describe, it, expect, beforeEach } from '@jest/globals';
import { ImportResolver } from '../../src/parsers/import-resolver_v1.0.0.js';
import { ParseErrorType } from '../../src/parsers/types_v1.0.0.js';
import { writeFileSync, unlinkSync, mkdirSync } from 'fs';
import { join } from 'path';

describe('ImportResolver', () => {
  let resolver: ImportResolver;
  const testDir = join(__dirname, '.tmp');

  beforeEach(() => {
    resolver = new ImportResolver({ basePath: testDir });
    mkdirSync(testDir, { recursive: true });
  });

  describe('parse()', () => {
    it('должен резолвить простой импорт', async () => {
      const importFile = join(testDir, 'import.json');
      const mainFile = join(testDir, 'main.j2.java');

      writeFileSync(importFile, '{"data": true}');
      writeFileSync(mainFile, `// [Data](file://${importFile})`);

      const result = await resolver.parse(mainFile);

      expect(result.success).toBe(true);
      expect(result.data!.imports).toHaveLength(1);
      expect(result.data!.imports[0].resolvedPath).toBe(importFile);
    });

    it('должен резолвить вложенные импорты', async () => {
      const level3 = join(testDir, 'level3.json');
      const level2 = join(testDir, 'level2.json');
      const level1 = join(testDir, 'level1.json');

      writeFileSync(level3, '{"level": 3}');
      writeFileSync(level2, `// [Level 3](file://${level3})`);
      writeFileSync(level1, `// [Level 2](file://${level2})`);

      const result = await resolver.parse(level1);

      expect(result.success).toBe(true);
      expect(result.data!.imports.length).toBeGreaterThan(0);
    });

    it('должен обнаруживать циклические зависимости', async () => {
      const file1 = join(testDir, 'file1.json');
      const file2 = join(testDir, 'file2.json');

      writeFileSync(file1, `// [File 2](file://${file2})`);
      writeFileSync(file2, `// [File 1](file://${file1})`);

      const result = await resolver.parse(file1);

      expect(result.success).toBe(false);
      expect(result.errors.some(e => e.type === ParseErrorType.CIRCULAR_IMPORT)).toBe(
        true
      );
    });

    it('должен строить граф зависимостей', async () => {
      const a = join(testDir, 'a.json');
      const b = join(testDir, 'b.json');
      const c = join(testDir, 'c.json');

      writeFileSync(c, '{"data": "c"}');
      writeFileSync(b, `// [C](file://${c})`);
      writeFileSync(a, `// [B](file://${b})\n// [C](file://${c})`);

      const result = await resolver.parse(a);

      expect(result.success).toBe(true);
      expect(result.data!.dependencyGraph.nodes.size).toBeGreaterThan(0);
      expect(result.data!.dependencyGraph.edges.length).toBeGreaterThan(0);
    });

    it('должен вычислять общий размер', async () => {
      const import1 = join(testDir, 'import1.json');
      const import2 = join(testDir, 'import2.json');
      const main = join(testDir, 'main.json');

      writeFileSync(import1, '{"size": 1}');
      writeFileSync(import2, '{"size": 2}');
      writeFileSync(
        main,
        `// [Import1](file://${import1})\n// [Import2](file://${import2})`
      );

      const result = await resolver.parse(main);

      expect(result.success).toBe(true);
      expect(result.data!.totalSize).toBeGreaterThan(0);
    });
  });

  describe('Circular Dependencies', () => {
    it('должен находить простой цикл', async () => {
      const file1 = join(testDir, 'cycle1.json');
      const file2 = join(testDir, 'cycle2.json');

      writeFileSync(file1, `// [Cycle 2](file://${file2})`);
      writeFileSync(file2, `// [Cycle 1](file://${file1})`);

      const result = await resolver.parse(file1);

      expect(result.data!.circularDependencies.length).toBeGreaterThan(0);
    });

    it('должен находить сложный цикл', async () => {
      const a = join(testDir, 'a.json');
      const b = join(testDir, 'b.json');
      const c = join(testDir, 'c.json');

      writeFileSync(a, `// [B](file://${b})`);
      writeFileSync(b, `// [C](file://${c})`);
      writeFileSync(c, `// [A](file://${a})`);

      const result = await resolver.parse(a);

      expect(result.data!.circularDependencies.length).toBeGreaterThan(0);
      expect(result.data!.circularDependencies[0].cycle.length).toBe(4); // A->B->C->A
    });

    it('должен разрешать циклы при allowCircular', async () => {
      const circularResolver = new ImportResolver({
        basePath: testDir,
        allowCircular: true,
      });

      const file1 = join(testDir, 'circular1.json');
      const file2 = join(testDir, 'circular2.json');

      writeFileSync(file1, `// [File2](file://${file2})`);
      writeFileSync(file2, `// [File1](file://${file1})`);

      const result = await circularResolver.parse(file1);

      // Не должно быть ошибок, только предупреждения
      expect(result.errors.length).toBe(0);
      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });

  describe('Import Patterns', () => {
    it('должен распознавать file:// protocol', async () => {
      const importFile = join(testDir, 'import.json');
      const mainFile = join(testDir, 'main.json');

      writeFileSync(importFile, '{"protocol": "file"}');
      writeFileSync(mainFile, `// [Import](file://${importFile})`);

      const result = await resolver.parse(mainFile);

      expect(result.success).toBe(true);
      expect(result.data!.imports).toHaveLength(1);
    });

    it('должен распознавать относительные пути', async () => {
      const importFile = join(testDir, 'relative.json');
      const mainFile = join(testDir, 'main.json');

      writeFileSync(importFile, '{"type": "relative"}');
      writeFileSync(mainFile, 'import "./relative.json"');

      const result = await resolver.parse(mainFile);

      expect(result.success).toBe(true);
    });

    it('должен поддерживать require() синтаксис', async () => {
      const importFile = join(testDir, 'required.json');
      const mainFile = join(testDir, 'main.json');

      writeFileSync(importFile, '{"required": true}');
      writeFileSync(mainFile, `require("./required.json")`);

      const result = await resolver.parse(mainFile);

      expect(result.success).toBe(true);
    });
  });

  describe('Caching', () => {
    it('должен кэшировать импорты', async () => {
      const importFile = join(testDir, 'cached.json');
      const mainFile = join(testDir, 'main.json');

      writeFileSync(importFile, '{"cached": true}');
      writeFileSync(
        mainFile,
        `// [Import1](file://${importFile})\n// [Import2](file://${importFile})`
      );

      const result = await resolver.parse(mainFile);

      expect(result.success).toBe(true);
      expect(result.warnings.some(w => w.message.includes('cached'))).toBe(true);
    });

    it('должен очищать кэш', async () => {
      const importFile = join(testDir, 'cache-test.json');
      const mainFile = join(testDir, 'main.json');

      writeFileSync(importFile, '{"data": 1}');
      writeFileSync(mainFile, `// [Import](file://${importFile})`);

      await resolver.parse(mainFile);

      const statsBefore = resolver.getCacheStats();
      expect(statsBefore.size).toBeGreaterThan(0);

      resolver.clearCache();

      const statsAfter = resolver.getCacheStats();
      expect(statsAfter.size).toBe(0);
    });
  });

  describe('validate()', () => {
    it('должен валидировать существующие импорты', async () => {
      const importFile = join(testDir, 'valid-import.json');
      const mainFile = join(testDir, 'main.json');

      writeFileSync(importFile, '{"valid": true}');
      writeFileSync(mainFile, `// [Import](file://${importFile})`);

      const isValid = await resolver.validate(mainFile);

      expect(isValid).toBe(true);
    });

    it('должен отклонять несуществующие импорты', async () => {
      const mainFile = join(testDir, 'invalid.json');

      writeFileSync(mainFile, '// [Missing](file:///nonexistent.json)');

      const isValid = await resolver.validate(mainFile);

      expect(isValid).toBe(false);
    });
  });

  describe('Configuration', () => {
    it('должен использовать кастомные расширения', async () => {
      const customResolver = new ImportResolver({
        basePath: testDir,
        extensions: ['.custom', '.json'],
      });

      const importFile = join(testDir, 'file.custom');
      const mainFile = join(testDir, 'main.json');

      writeFileSync(importFile, '{"custom": true}');
      writeFileSync(mainFile, `import "./file"`);

      const result = await customResolver.parse(mainFile);

      expect(result.success).toBe(true);
    });

    it('должен ограничивать глубину импортов', async () => {
      const shallowResolver = new ImportResolver({
        basePath: testDir,
        maxDepth: 2,
      });

      const level3 = join(testDir, 'level3.json');
      const level2 = join(testDir, 'level2.json');
      const level1 = join(testDir, 'level1.json');

      writeFileSync(level3, '{"level": 3}');
      writeFileSync(level2, `// [Level3](file://${level3})`);
      writeFileSync(level1, `// [Level2](file://${level2})`);

      const result = await shallowResolver.parse(level1);

      // Должен достичь лимита глубины
      expect(result.errors.some(e => e.message.includes('depth'))).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('должен обрабатывать отсутствующие файлы', async () => {
      const mainFile = join(testDir, 'main.json');
      writeFileSync(mainFile, '// [Missing](file:///nonexistent.json)');

      const result = await resolver.parse(mainFile);

      expect(result.success).toBe(false);
      expect(result.errors[0].type).toBe(ParseErrorType.FILE_NOT_FOUND);
    });

    it('должен обрабатывать ошибки парсинга импортов', async () => {
      const importFile = join(testDir, 'invalid.json');
      const mainFile = join(testDir, 'main.json');

      writeFileSync(importFile, '{invalid json}');
      writeFileSync(mainFile, `// [Invalid](file://${importFile})`);

      const result = await resolver.parse(mainFile);

      expect(result.success).toBe(false);
      expect(result.errors.some(e => e.type === ParseErrorType.INVALID_JSON)).toBe(
        true
      );
    });
  });
});
