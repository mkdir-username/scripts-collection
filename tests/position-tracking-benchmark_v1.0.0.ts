#!/usr/bin/env node
/**
 * Position Tracking Benchmark v1.0.0
 *
 * Тесты производительности buildPositionMap() на различных размерах JSON
 *
 * Usage:
 *   npm install
 *   tsx tests/position-tracking-benchmark_v1.0.0.ts
 */

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

// ============================================================================
// MOCK DATA GENERATORS
// ============================================================================

/**
 * Генерация тестового JSON контракта заданного размера
 */
function generateMockContract(targetSizeKB: number): string {
  const components: any[] = [];

  // Примерный размер одного компонента ~500 байт
  const componentSize = 500;
  const componentsNeeded = Math.floor((targetSizeKB * 1024) / componentSize);

  for (let i = 0; i < componentsNeeded; i++) {
    components.push({
      type: 'ButtonView',
      id: `button_${i}`,
      text: `Button ${i}`,
      style: {
        backgroundColor: '#007AFF',
        textColor: '#FFFFFF',
        cornerRadius: 8,
        padding: { top: 12, bottom: 12, left: 16, right: 16 }
      },
      actions: [
        {
          type: 'navigate',
          destination: `/screen_${i}`,
          params: { id: i }
        }
      ],
      stateAware: {
        control: {
          disabled: { opacity: 0.5 },
          enabled: { opacity: 1.0 }
        }
      }
    });
  }

  const contract = {
    type: 'Screen',
    version: 'v1',
    components
  };

  return JSON.stringify(contract, null, 2);
}

// ============================================================================
// POSITION MAP IMPLEMENTATION (из v2.1.0)
// ============================================================================

interface PositionInfo {
  line: number;
  column: number;
  offset: number;
}

interface PositionMap {
  byPointer: Map<string, PositionInfo>;
  byPath: Map<string, PositionInfo>;
  totalLines: number;
}

function buildPositionMap(jsonText: string, parsedData: any): PositionMap {
  const byPointer = new Map<string, PositionInfo>();
  const byPath = new Map<string, PositionInfo>();

  let line = 1;
  let column = 1;
  let offset = 0;

  const pathStack: Array<string | number> = [];
  let inString = false;
  let escaped = false;
  let currentKey = '';
  let collectingKey = false;
  let arrayIndex = 0;
  let arrayStack: number[] = [];

  const savePosition = (path: Array<string | number>) => {
    if (path.length === 0) return;

    const pointer = '/' + path.map(p =>
      String(p).replace(/~/g, '~0').replace(/\//g, '~1')
    ).join('/');

    const propertyPath = path.reduce((acc, segment, i) => {
      if (typeof segment === 'number') {
        return `${acc}[${segment}]`;
      }
      return acc ? `${acc}.${segment}` : segment;
    }, '');

    const pos: PositionInfo = { line, column, offset };

    byPointer.set(pointer, pos);
    byPath.set(propertyPath, pos);
  };

  for (let i = 0; i < jsonText.length; i++) {
    const char = jsonText[i];
    const prevChar = i > 0 ? jsonText[i - 1] : '';
    const nextChar = i < jsonText.length - 1 ? jsonText[i + 1] : '';

    if (escaped) {
      escaped = false;
      column++;
      offset++;
      continue;
    }

    if (char === '\\' && inString) {
      escaped = true;
      column++;
      offset++;
      continue;
    }

    if (char === '"') {
      if (inString) {
        inString = false;
        if (collectingKey && nextChar === ':') {
          pathStack.push(currentKey);
          savePosition(pathStack);
          collectingKey = false;
          currentKey = '';
        }
      } else {
        inString = true;
        if (prevChar === '{' || prevChar === ',' || prevChar === '\n' || prevChar === ' ') {
          collectingKey = true;
          currentKey = '';
        }
      }
      column++;
      offset++;
      continue;
    }

    if (inString && collectingKey) {
      currentKey += char;
    }

    if (!inString) {
      if (char === '{') {
        // Начало объекта
      }

      if (char === '[') {
        arrayStack.push(arrayIndex);
        arrayIndex = 0;
      }

      if (char === '}') {
        if (pathStack.length > 0) {
          pathStack.pop();
        }
      }

      if (char === ']') {
        if (pathStack.length > 0) {
          pathStack.pop();
        }
        if (arrayStack.length > 0) {
          arrayIndex = arrayStack.pop()!;
        }
      }

      if (char === ',') {
        const parent = pathStack[pathStack.length - 1];
        if (typeof parent === 'number' ||
            (pathStack.length > 0 && jsonText.lastIndexOf('[', i) > jsonText.lastIndexOf('{', i))) {
          if (pathStack.length > 0 && typeof pathStack[pathStack.length - 1] === 'number') {
            pathStack.pop();
          }
          arrayIndex++;
          pathStack.push(arrayIndex);
          savePosition(pathStack);
        } else {
          if (pathStack.length > 0) {
            pathStack.pop();
          }
        }
      }

      if (char === ':' && pathStack.length > 0) {
        let j = i + 1;
        while (j < jsonText.length && (jsonText[j] === ' ' || jsonText[j] === '\n')) {
          j++;
        }

        if (j < jsonText.length && jsonText[j] === '[') {
          pathStack.push(0);
          savePosition(pathStack);
        }
      }
    }

    if (char === '\n') {
      line++;
      column = 1;
    } else {
      column++;
    }
    offset++;
  }

  return {
    byPointer,
    byPath,
    totalLines: line
  };
}

// ============================================================================
// BENCHMARK RUNNER
// ============================================================================

interface BenchmarkResult {
  sizeKB: number;
  parseTime: number;
  buildMapTime: number;
  totalTime: number;
  mapSize: number;
  overhead: number;
}

function runBenchmark(sizeKB: number, iterations: number = 3): BenchmarkResult {
  console.log(`\n📊 Benchmarking ${sizeKB}KB JSON (${iterations} iterations)...`);

  const jsonText = generateMockContract(sizeKB);
  const actualSizeKB = Buffer.byteLength(jsonText, 'utf-8') / 1024;

  const parseTimes: number[] = [];
  const buildMapTimes: number[] = [];
  let mapSize = 0;

  for (let i = 0; i < iterations; i++) {
    // JSON.parse() benchmark
    const parseStart = performance.now();
    const contract = JSON.parse(jsonText);
    const parseEnd = performance.now();
    parseTimes.push(parseEnd - parseStart);

    // buildPositionMap() benchmark
    const buildStart = performance.now();
    const posMap = buildPositionMap(jsonText, contract);
    const buildEnd = performance.now();
    buildMapTimes.push(buildEnd - buildStart);

    mapSize = posMap.byPointer.size;

    process.stdout.write(`   Iteration ${i + 1}/${iterations}... ✓\r`);
  }

  console.log(''); // Новая строка после итераций

  // Средние значения
  const avgParseTime = parseTimes.reduce((a, b) => a + b, 0) / iterations;
  const avgBuildMapTime = buildMapTimes.reduce((a, b) => a + b, 0) / iterations;
  const totalTime = avgParseTime + avgBuildMapTime;
  const overhead = (avgBuildMapTime / totalTime) * 100;

  return {
    sizeKB: actualSizeKB,
    parseTime: avgParseTime,
    buildMapTime: avgBuildMapTime,
    totalTime,
    mapSize,
    overhead
  };
}

// ============================================================================
// MAIN
// ============================================================================

async function main() {
  console.log('━'.repeat(80));
  console.log('🚀 Position Tracking Benchmark v1.0.0');
  console.log('━'.repeat(80));

  const testSizes = [10, 50, 100, 239, 500, 1000];
  const results: BenchmarkResult[] = [];

  for (const size of testSizes) {
    const result = runBenchmark(size, 5);
    results.push(result);
  }

  // Вывод результатов
  console.log('\n━'.repeat(80));
  console.log('📈 BENCHMARK RESULTS');
  console.log('━'.repeat(80));
  console.log('');

  console.log('┌─────────┬──────────┬─────────────┬────────────┬──────────┬───────────┐');
  console.log('│ Size    │ Parse    │ BuildMap    │ Total      │ Map Size │ Overhead  │');
  console.log('│ (KB)    │ (ms)     │ (ms)        │ (ms)       │ (paths)  │ (%)       │');
  console.log('├─────────┼──────────┼─────────────┼────────────┼──────────┼───────────┤');

  for (const result of results) {
    const size = result.sizeKB.toFixed(1).padStart(7);
    const parse = result.parseTime.toFixed(2).padStart(8);
    const build = result.buildMapTime.toFixed(2).padStart(11);
    const total = result.totalTime.toFixed(2).padStart(10);
    const mapSize = String(result.mapSize).padStart(8);
    const overhead = result.overhead.toFixed(1).padStart(9);

    console.log(`│ ${size} │ ${parse} │ ${build} │ ${total} │ ${mapSize} │ ${overhead} │`);
  }

  console.log('└─────────┴──────────┴─────────────┴────────────┴──────────┴───────────┘');
  console.log('');

  // Проверка целевого значения
  const target239 = results.find(r => Math.abs(r.sizeKB - 239) < 10);
  if (target239) {
    console.log('━'.repeat(80));
    console.log('🎯 TARGET CHECK (239KB file)');
    console.log('━'.repeat(80));
    console.log(`   Target:     < 100ms`);
    console.log(`   Actual:     ${target239.buildMapTime.toFixed(2)}ms`);
    console.log(`   Overhead:   ${target239.overhead.toFixed(1)}%`);

    if (target239.buildMapTime < 100) {
      console.log(`   Status:     ✅ PASS`);
    } else {
      console.log(`   Status:     ❌ FAIL`);
    }
    console.log('━'.repeat(80));
  }

  // Сохранение отчета
  const report = {
    timestamp: new Date().toISOString(),
    results,
    summary: {
      totalTestSizes: testSizes.length,
      avgOverhead: results.reduce((sum, r) => sum + r.overhead, 0) / results.length,
      maxBuildTime: Math.max(...results.map(r => r.buildMapTime)),
      targetCheckPassed: target239 ? target239.buildMapTime < 100 : false
    }
  };

  const reportPath = join(process.cwd(), 'benchmark-report.json');
  writeFileSync(reportPath, JSON.stringify(report, null, 2));
  console.log(`\n📝 Detailed report saved to: ${reportPath}`);
  console.log('');
}

main().catch(console.error);
