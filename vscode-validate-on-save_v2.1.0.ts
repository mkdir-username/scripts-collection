#!/usr/bin/env node
/**
 * VSCode On-Save Validator v2.1.0
 *
 * Автоматическая валидация SDUI контрактов при сохранении в VSCode
 * Использует новый дизайн вывода с прогресс-барами, группировкой и box drawing
 * + ОПТИМИЗАЦИЯ: Быстрое отслеживание позиций в JSON через position map
 *
 * Usage:
 *   node vscode-validate-on-save_v2.1.0.js path/to/contract.json
 */

import { readFileSync } from 'fs';
import { basename, relative } from 'path';

const PROJECT_ROOT =
  process.env.PROJECT_ROOT ||
  '/Users/username/Documents/front-middle-schema';

// Путь к MCP серверу с валидатором
const MCP_ROOT = '/Users/username/Documents/front-middle-schema/alfa-sdui-mcp';

// Получить путь к файлу из аргументов
const filePath = process.argv[2];

if (!filePath) {
  console.error('❌ ERROR: Путь к файлу не указан');
  console.error('Usage: node vscode-validate-on-save_v2.1.0.js <file>');
  process.exit(1);
}

// ============================================================================
// POSITION TRACKING - ОПТИМИЗИРОВАННАЯ ВЕРСИЯ
// ============================================================================

interface PositionInfo {
  line: number;
  column: number;
  offset: number;
}

interface PositionMap {
  /** Быстрый поиск по JSON Pointer */
  byPointer: Map<string, PositionInfo>;
  /** Быстрый поиск по property path */
  byPath: Map<string, PositionInfo>;
  /** Общее количество строк */
  totalLines: number;
}

/**
 * Строим position map за один проход по исходному тексту JSON
 *
 * Алгоритм:
 * 1. Проходим по тексту посимвольно
 * 2. Отслеживаем текущий JSON path через стек
 * 3. При встрече ключа/индекса сохраняем позицию
 * 4. Используем Map для O(1) поиска
 *
 * Сложность: O(n) где n - длина текста
 * Память: O(k) где k - количество ключей в JSON
 */
function buildPositionMap(jsonText: string, parsedData: any): PositionMap {
  const byPointer = new Map<string, PositionInfo>();
  const byPath = new Map<string, PositionInfo>();

  let line = 1;
  let column = 1;
  let offset = 0;

  // Стек для отслеживания текущего пути
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

    // Обработка escape-последовательностей
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

    // Обработка строк
    if (char === '"') {
      if (inString) {
        inString = false;
        if (collectingKey && nextChar === ':') {
          // Завершили сбор ключа, сохраняем позицию
          pathStack.push(currentKey);
          savePosition(pathStack);
          collectingKey = false;
          currentKey = '';
        }
      } else {
        inString = true;
        // Начинаем собирать ключ, если предыдущий символ { или ,
        if (prevChar === '{' || prevChar === ',' || prevChar === '\n' || prevChar === ' ') {
          collectingKey = true;
          currentKey = '';
        }
      }
      column++;
      offset++;
      continue;
    }

    // Собираем имя ключа
    if (inString && collectingKey) {
      currentKey += char;
    }

    if (!inString) {
      // Начало объекта
      if (char === '{') {
        // Текущий ключ уже добавлен в стек
      }

      // Начало массива
      if (char === '[') {
        arrayStack.push(arrayIndex);
        arrayIndex = 0;
      }

      // Конец объекта
      if (char === '}') {
        if (pathStack.length > 0) {
          pathStack.pop();
        }
      }

      // Конец массива
      if (char === ']') {
        if (pathStack.length > 0) {
          pathStack.pop();
        }
        if (arrayStack.length > 0) {
          arrayIndex = arrayStack.pop()!;
        }
      }

      // Запятая в массиве
      if (char === ',') {
        const parent = pathStack[pathStack.length - 1];
        // Проверяем, находимся ли в массиве
        if (typeof parent === 'number' ||
            (pathStack.length > 0 && jsonText.lastIndexOf('[', i) > jsonText.lastIndexOf('{', i))) {
          if (pathStack.length > 0 && typeof pathStack[pathStack.length - 1] === 'number') {
            pathStack.pop();
          }
          arrayIndex++;
          pathStack.push(arrayIndex);
          savePosition(pathStack);
        } else {
          // Запятая в объекте - убираем последний ключ
          if (pathStack.length > 0) {
            pathStack.pop();
          }
        }
      }

      // Двоеточие после ключа
      if (char === ':' && pathStack.length > 0) {
        // Ключ уже в стеке, проверяем следующий символ
        let j = i + 1;
        while (j < jsonText.length && (jsonText[j] === ' ' || jsonText[j] === '\n')) {
          j++;
        }

        if (j < jsonText.length && jsonText[j] === '[') {
          // Массив - добавляем индекс 0
          pathStack.push(0);
          savePosition(pathStack);
        }
      }
    }

    // Обновление позиции
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

/**
 * Быстрый поиск номера строки по пути
 * Сначала пробуем точное совпадение, затем ищем ближайший родительский путь
 */
function findLineNumber(
  positionMap: PositionMap,
  path: string,
  pointer: string
): number {
  // 1. Прямой поиск по JSON Pointer (самый точный)
  if (positionMap.byPointer.has(pointer)) {
    return positionMap.byPointer.get(pointer)!.line;
  }

  // 2. Прямой поиск по property path
  if (positionMap.byPath.has(path)) {
    return positionMap.byPath.get(path)!.line;
  }

  // 3. Ищем ближайший родительский путь
  const segments = path.split(/[.\[\]]/).filter(Boolean);

  for (let i = segments.length - 1; i >= 0; i--) {
    const parentPath = segments.slice(0, i).reduce((acc, seg, idx) => {
      if (!acc) return seg;
      // Проверяем, является ли сегмент числом (индекс массива)
      if (/^\d+$/.test(seg)) {
        return `${acc}[${seg}]`;
      }
      return `${acc}.${seg}`;
    }, '');

    if (positionMap.byPath.has(parentPath)) {
      return positionMap.byPath.get(parentPath)!.line;
    }
  }

  // 4. Fallback - первая строка
  return 1;
}

// ============================================================================
// ФОРМАТТЕРЫ
// ============================================================================

/**
 * Прогресс-бар
 */
function renderProgressBar(current: number, total: number, width: number = 20): string {
  const percentage = total === 0 ? 0 : Math.floor((current / total) * 100);
  const filledBlocks = total === 0 ? 0 : Math.floor((current / total) * width);
  const filled = '█'.repeat(filledBlocks);
  const empty = ' '.repeat(width - filledBlocks);
  return `[${filled}${empty}] ${percentage}% (${current}/${total} components)`;
}

/**
 * Конвертация path -> JSON Pointer (RFC 6901)
 */
function pathToJsonPointer(path: string): string {
  if (!path) return '';

  // Разбиваем путь на сегменты
  const segments: string[] = [];
  let current = '';
  let inBracket = false;

  for (let i = 0; i < path.length; i++) {
    const char = path[i];

    if (char === '[' && path[i + 1] === "'") {
      // Начало ['key']
      if (current) {
        segments.push(current);
        current = '';
      }
      inBracket = true;
      i++; // skip '
      continue;
    }

    if (char === "'" && path[i + 1] === ']' && inBracket) {
      // Конец ['key']
      segments.push(current);
      current = '';
      inBracket = false;
      i++; // skip ]
      continue;
    }

    if (char === '[' && !inBracket) {
      // Начало [0]
      if (current) {
        segments.push(current);
        current = '';
      }
      continue;
    }

    if (char === ']' && !inBracket) {
      // Конец [0]
      segments.push(current);
      current = '';
      continue;
    }

    if (char === '.' && !inBracket) {
      if (current) {
        segments.push(current);
        current = '';
      }
      continue;
    }

    current += char;
  }

  if (current) {
    segments.push(current);
  }

  // Экранирование по RFC 6901: ~ -> ~0, / -> ~1
  const escaped = segments.map(seg =>
    seg.replace(/~/g, '~0').replace(/\//g, '~1')
  );

  return '/' + escaped.join('/');
}

/**
 * Группировка errors/warnings по компонентам
 */
interface ParsedIssue {
  path: string;
  message: string;
  component: string | null;
  raw: string;
}

function parseIssue(text: string): ParsedIssue | null {
  // Пропускаем дочерние warnings (начинаются с пробелов)
  if (text.startsWith('  ')) {
    return null;
  }

  const match = text.match(/^(.*?):\s*(.+)$/);
  if (!match) {
    return { path: '', message: text, component: null, raw: text };
  }

  const path = match[1];
  const message = match[2];

  // Извлекаем компонент из сообщения
  let component: string | null = null;

  // "in ComponentName (v1):"
  const compMatch1 = message.match(/in\s+(\w+)(?:\s+\(v\d+\))?/);
  if (compMatch1) {
    component = compMatch1[1];
  }

  // "ComponentName is notReleased"
  const compMatch2 = message.match(/^(\w+)\s+is\s+notReleased/);
  if (compMatch2) {
    component = compMatch2[1];
  }

  // "Unexpected fields found in ... pattern"
  if (message.includes('pattern') && !component) {
    component = 'StateAware pattern';
  }

  return { path, message, component, raw: text };
}

function groupIssuesByComponent(issues: string[]): Map<string, ParsedIssue[]> {
  const grouped = new Map<string, ParsedIssue[]>();

  for (const issue of issues) {
    const parsed = parseIssue(issue);
    if (!parsed) continue; // пропускаем дочерние warnings

    const key = parsed.component || 'Other';
    if (!grouped.has(key)) {
      grouped.set(key, []);
    }
    grouped.get(key)!.push(parsed);
  }

  return grouped;
}

/**
 * Форматирование box для компонента
 */
function formatComponentBox(componentName: string, count: number, additionalInfo?: string): void {
  const maxWidth = 78;
  const title = additionalInfo
    ? `${componentName} · ${additionalInfo}`
    : componentName;
  const info = `${count} issue${count !== 1 ? 's' : ''}`;

  // Top border: "┌─ title ─...─┐"
  const titleLine = `┌─ ${title} `;
  const titlePadding = maxWidth - titleLine.length - 1;
  console.log(titleLine + '─'.repeat(titlePadding) + '┐');

  // Middle line: "│ info      ...      │"
  const infoLine = `│ ${info} `;
  const infoPadding = maxWidth - infoLine.length - 1;
  console.log(infoLine + ' '.repeat(infoPadding) + '│');

  // Bottom border: "└─...─┘"
  console.log('└' + '─'.repeat(maxWidth) + '┘');
}

/**
 * Форматирование issue с Path, JSON Pointer и Link (с реальным номером строки)
 */
function formatIssue(
  issue: ParsedIssue,
  index: number,
  icon: string,
  filePath: string,
  positionMap: PositionMap
): void {
  const pointer = pathToJsonPointer(issue.path);
  const lineNumber = findLineNumber(positionMap, issue.path, pointer);

  console.log('');
  console.log(`  ${icon} [${index}] ${issue.message}`);
  console.log('');
  console.log(`      Path: ${issue.path}`);
  console.log(`      JSON Pointer: ${pointer}`);
  console.log(`      Link: file://${filePath}#L${lineNumber}`);
  console.log('');
}

// ============================================================================
// ОСНОВНОЙ ФОРМАТТЕР ВЫВОДА
// ============================================================================

function formatOutput(
  filePath: string,
  report: any | null,
  parseError?: string,
  stats?: { duration: number; totalComponents: number; positionMapBuildTime: number },
  positionMap?: PositionMap
): void {
  const fileName = basename(filePath);
  const relativePath = relative(PROJECT_ROOT, filePath);

  // PROCESSING HEADER
  console.log('━'.repeat(80));
  console.log(`🔄 PROCESSING: ${fileName}`);
  console.log('━'.repeat(80));
  console.log('');

  // PARSE ERROR
  if (parseError) {
    console.log('📂 Reading file...');
    console.log('');
    console.log('🔍 Parsing JSON...');
    console.log('   ❌ Parse failed');
    console.log('');
    console.log('━'.repeat(80));
    console.log('📄 File:', fileName);
    console.log('📁 Path:', relativePath);
    console.log('━'.repeat(80));
    console.log('');
    console.log('❌ PARSE ERROR');
    console.log('━'.repeat(80));
    console.log(parseError);
    console.log('');
    console.log('💡 Исправьте синтаксические ошибки JSON');
    console.log('━'.repeat(80));
    console.log('');
    return;
  }

  // PROGRESS BAR (если есть статистика)
  if (stats) {
    console.log('🔬 Validating contract...');
    console.log('   ' + renderProgressBar(stats.totalComponents, stats.totalComponents));
    console.log(`   ✅ Completed in ${stats.duration.toFixed(2)}s`);
    if (stats.positionMapBuildTime > 0) {
      console.log(`   📍 Position map built in ${stats.positionMapBuildTime.toFixed(2)}ms`);
    }
    console.log('');
  }

  // FILE INFO
  console.log('━'.repeat(80));
  console.log(`📄 File: ${fileName}`);
  console.log(`📁 Path: ${relativePath}`);
  console.log('━'.repeat(80));
  console.log('');

  // STATUS
  if (report.valid) {
    console.log('✅ CONTRACT VALID');
  } else {
    console.log('❌ CONTRACT INVALID');
  }
  console.log('');

  // SUMMARY (компактный формат с точками)
  console.log('📊 SUMMARY');

  const webCompat = `${report.webCompatibility.toFixed(1)}%`;
  console.log(`   🌐 Web Compatibility ${''.padEnd(5, '.')} ${webCompat}`);

  if (report.dataBindings?.hasBindings) {
    const bindings = `${report.dataBindings.totalBindings} found (state: ${report.dataBindings.byType.state}, data: ${report.dataBindings.byType.data}, computed: ${report.dataBindings.byType.computed})`;
    console.log(`   🔗 Data Bindings ${''.padEnd(9, '.')} ${bindings}`);
  }

  if (report.versions) {
    const totalComps = `${report.versions.totalComponents} total (${Object.entries(report.versions.byVersion).map(([v, c]) => `${v}: ${c}`).join(', ')})`;
    console.log(`   📦 Components ${''.padEnd(12, '.')} ${totalComps}`);
  }

  console.log('');

  // ERRORS
  if (report.errors && report.errors.length > 0) {
    console.log('━'.repeat(80));
    console.log(`❌ ERRORS: ${report.errors.length} critical issue${report.errors.length !== 1 ? 's' : ''}`);
    console.log('━'.repeat(80));
    console.log('');

    const grouped = groupIssuesByComponent(report.errors);
    let issueIndex = 1;

    for (const [component, issues] of grouped) {
      formatComponentBox(component, issues.length);

      for (const issue of issues) {
        formatIssue(issue, issueIndex++, '❌', filePath, positionMap!);
        if (issueIndex <= issues.length + 1) {
          console.log('─'.repeat(80));
        }
      }

      console.log('━'.repeat(80));
      console.log('');
    }
  }

  // WARNINGS
  if (report.warnings && report.warnings.length > 0) {
    console.log('━'.repeat(80));
    console.log(`⚠️  WARNINGS: ${report.warnings.length} issue${report.warnings.length !== 1 ? 's' : ''}`);
    console.log('━'.repeat(80));
    console.log('');

    const grouped = groupIssuesByComponent(report.warnings);
    let issueIndex = 1;

    for (const [component, issues] of grouped) {
      formatComponentBox(component, issues.length);

      for (const issue of issues) {
        formatIssue(issue, issueIndex++, '⚠️ ', filePath, positionMap!);
        if (issueIndex <= issues.length + 1) {
          console.log('─'.repeat(80));
        }
      }

      console.log('━'.repeat(80));
      console.log('');
    }
  }

  // FOOTER
  console.log('━'.repeat(80));
  if (report.valid) {
    console.log('✅ Контракт готов к использованию');
  } else {
    console.log('❌ Контракт требует исправления');
  }
  console.log('━'.repeat(80));
  console.log('');
}

// ============================================================================
// ОСНОВНАЯ ФУНКЦИЯ ВАЛИДАЦИИ
// ============================================================================

async function validateFile(filePath: string): Promise<void> {
  const startTime = Date.now();

  try {
    // Динамический импорт модулей
    const { IncrementalValidator } = await import(
      `file://${MCP_ROOT}/dist/validators/incremental-validator.js`
    );
    const { SDUISchemaIndex } = await import(
      `file://${MCP_ROOT}/dist/schema-utils/schema-index.js`
    );

    const fileName = basename(filePath);

    // Progress: Reading
    console.log('📂 Reading file...');
    const content = readFileSync(filePath, 'utf-8');
    const fileSizeKB = (Buffer.byteLength(content, 'utf-8') / 1024).toFixed(2);
    console.log(`   Size: ${fileSizeKB} KB`);
    console.log('');

    // Progress: Parsing
    console.log('🔍 Parsing JSON...');
    let contract;
    try {
      contract = JSON.parse(content);
      console.log('   ✅ Parsed successfully');
    } catch (parseError) {
      console.log('   ❌ Parse failed');
      console.log('');
      formatOutput(filePath, null, (parseError as Error).message);
      process.exit(1);
    }
    console.log('');

    // Progress: Building position map
    console.log('📍 Building position map...');
    const posMapStart = Date.now();
    const positionMap = buildPositionMap(content, contract);
    const posMapEnd = Date.now();
    const posMapTime = posMapEnd - posMapStart;
    console.log(`   ✅ Mapped ${positionMap.byPointer.size} locations in ${posMapTime}ms`);
    console.log('');

    // Progress: Initializing
    console.log('⚙️  Initializing validator...');
    const schemaIndex = new SDUISchemaIndex(PROJECT_ROOT);
    console.log(`   • Indexed ${schemaIndex.getComponentCount?.()} components`);
    console.log('   ✅ Validator ready');
    console.log('');

    // Validation
    const validator = new IncrementalValidator(PROJECT_ROOT, schemaIndex);
    const report = validator.validateIncremental(contract);

    const endTime = Date.now();
    const duration = (endTime - startTime) / 1000;

    // Output
    formatOutput(
      filePath,
      report,
      undefined,
      {
        duration,
        totalComponents: report.versions?.totalComponents || 0,
        positionMapBuildTime: posMapTime
      },
      positionMap
    );

    // Exit code
    process.exit(report.valid ? 0 : 1);
  } catch (error) {
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);

    console.error('━'.repeat(80));
    console.error(`❌ VALIDATION ERROR (after ${duration}s)`);
    console.error('━'.repeat(80));
    console.error(error);
    console.error('━'.repeat(80));
    process.exit(1);
  }
}

// Запуск
validateFile(filePath);
