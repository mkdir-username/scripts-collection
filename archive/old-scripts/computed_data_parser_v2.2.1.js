#!/usr/bin/env node

/**
 * JSON Contract Parser v2.2.1
 * ===========================
 *
 * Автоматический парсер для разрешения сложных JSON-контрактов с:
 * - Computed выражениями (условия if-then-else)
 * - Подстановками ${computed.xxx}, ${data.xxx}, ${state.xxx}
 * - Специальными полями $children, $if, $then, $else
 * - Интеграцией моковых данных
 *
 * Основные возможности:
 * 1. Рекурсивное разрешение всех ссылок и подстановок
 * 2. Вычисление условных выражений
 * 3. Интеграция данных из внешнего файла
 * 4. Защита от циклических зависимостей
 * 5. Топологическая сортировка computed-зависимостей
 * 6. Подробное логирование процесса
 * 7. Поддержка частичных template strings "Hello ${name}!"
 * 8. Performance tracking и детальная статистика
 * 9. Автоматическая фильтрация пустых объектов {} и null в массивах
 *
 * @version 2.2.1
 * @author Claude Code
 */

const fs = require('fs');
const path = require('path');

// ============================================================================
// Custom Exceptions
// ============================================================================

/**
 * Ошибка при разрешении значения
 */
class ResolutionError extends Error {
  constructor(message, context = {}) {
    super(message);
    this.name = 'ResolutionError';
    this.context = context;
  }
}

/**
 * Ошибка циклической зависимости
 */
class CircularDependencyError extends Error {
  constructor(message, cycle = []) {
    super(message);
    this.name = 'CircularDependencyError';
    this.cycle = cycle;
  }
}

// ============================================================================
// Performance Tracker
// ============================================================================

/**
 * Трекер производительности для метрик парсинга
 */
class PerformanceTracker {
  constructor() {
    this.timings = new Map();
    this.counters = {
      computed_resolved: 0,
      substitutions: 0,
      if_expressions: 0,
      children_expanded: 0,
      cache_hits: 0
    };
  }

  startTimer(label) {
    this.timings.set(label, Date.now());
  }

  stopTimer(label) {
    const start = this.timings.get(label);
    if (!start) return 0;
    const duration = Date.now() - start;
    this.timings.delete(label);
    return duration;
  }

  increment(counter, amount = 1) {
    if (this.counters.hasOwnProperty(counter)) {
      this.counters[counter] += amount;
    }
  }

  getStats() {
    return { ...this.counters };
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Проверяет, является ли значение template reference вида ${...}
 * @param {*} value - Значение для проверки
 * @returns {boolean}
 */
function isTemplateRef(value) {
  return typeof value === 'string' &&
         value.startsWith('${') &&
         value.endsWith('}') &&
         !value.slice(2, -1).includes('${'); // не вложенные
}

/**
 * Парсит путь из template reference
 * Поддерживает: data.key, state.array[0], computed.nested.field
 * @param {string} pathStr - Template reference вида "${path.to.value}"
 * @returns {string[]} Массив частей пути
 */
function parsePath(pathStr) {
  if (!isTemplateRef(pathStr)) {
    throw new ResolutionError(`parsePath expects a template ref, got: ${pathStr}`);
  }

  let clean = pathStr.slice(2, -1); // убираем ${ и }
  const parts = [];
  let current = '';
  let inBrackets = false;

  for (let i = 0; i < clean.length; i++) {
    const char = clean[i];
    if (char === '[') {
      if (current) parts.push(current);
      current = '';
      inBrackets = true;
    } else if (char === ']') {
      if (current) {
        const num = current.replace(/['"]/g, '');
        parts.push(isNaN(num) ? num : parseInt(num, 10));
      }
      current = '';
      inBrackets = false;
    } else if (char === '.' && !inBrackets) {
      if (current) parts.push(current);
      current = '';
    } else {
      current += char;
    }
  }
  if (current) parts.push(current);
  return parts;
}

/**
 * Разрешает путь в контексте с защитой от циклов
 * @param {Object} context - Контекст с data, state, computed
 * @param {string} pathStr - Template reference
 * @param {string[]} resolutionStack - Стек для отслеживания циклов
 * @param {boolean} debug - Включить отладку
 * @returns {*} Разрешенное значение
 */
function resolvePath(context, pathStr, resolutionStack = [], debug = false) {
  if (!isTemplateRef(pathStr)) return pathStr;

  // Защита от циклических зависимостей
  if (resolutionStack.includes(pathStr)) {
    throw new CircularDependencyError(
      `Циклическая зависимость: ${resolutionStack.join(' → ')} → ${pathStr}`,
      [...resolutionStack, pathStr]
    );
  }

  const parts = parsePath(pathStr);
  let current = context;

  if (debug) {
    console.log(`  🔍 Разрешение пути: ${pathStr} → [${parts.join(', ')}]`);
  }

  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];

    if (current == null || (typeof current !== 'object' && typeof current !== 'function')) {
      // Улучшенное сообщение об ошибке с доступными ключами
      const availableKeys = typeof current === 'object' && current !== null
        ? Object.keys(current).slice(0, 5).join(', ')
        : 'none';

      throw new ResolutionError(
        `Не удалось разрешить путь: ${pathStr} на части "${part}"\n` +
        `Путь: ${parts.slice(0, i).join('.')} → "${part}"\n` +
        `Доступные ключи: ${availableKeys}`,
        { path: pathStr, failedAt: part, availableKeys }
      );
    }

    current = current[part];

    if (debug) {
      const preview = JSON.stringify(current).slice(0, 50);
      console.log(`    ├─ ${part} = ${preview}${preview.length === 50 ? '...' : ''}`);
    }
  }

  if (debug) {
    console.log(`    └─ Результат: ${JSON.stringify(current)}`);
  }

  return current;
}

// ============================================================================
// Dependency Graph Analysis
// ============================================================================

/**
 * Рекурсивно извлекает все ${...} ссылки из объекта
 * @param {*} obj - Объект для анализа
 * @param {Set<string>} refs - Накопитель ссылок
 * @returns {Set<string>} Множество найденных ссылок
 */
function extractRefs(obj, refs = new Set()) {
  if (typeof obj === 'string') {
    // Полная ссылка ${...}
    if (isTemplateRef(obj)) {
      refs.add(obj);
    }
    // Частичные подстановки "Hello ${name}!"
    else if (obj.includes('${')) {
      const matches = obj.matchAll(/\$\{([^}]+)\}/g);
      for (const match of matches) {
        refs.add(`\${${match[1]}}`);
      }
    }
  } else if (Array.isArray(obj)) {
    obj.forEach(item => extractRefs(item, refs));
  } else if (typeof obj === 'object' && obj !== null) {
    for (const key in obj) {
      extractRefs(obj[key], refs);
    }
  }
  return refs;
}

/**
 * Строит граф зависимостей между computed-полями
 * @param {Object} computed - Объект computed из контракта
 * @returns {Map<string, Set<string>>} Граф зависимостей (ключ → зависит от)
 */
function buildDependencyGraph(computed) {
  const graph = new Map();

  for (const key in computed) {
    const dependencies = new Set();
    const node = computed[key];

    // Извлекаем все ${...} ссылки из узла
    const refs = extractRefs(node);

    for (const ref of refs) {
      try {
        const parts = parsePath(ref);
        // Ищем ссылки на computed (первая часть пути = 'computed')
        if (parts[0] === 'computed' && parts[1]) {
          dependencies.add(parts[1]);
        }
      } catch (e) {
        // Игнорируем некорректные ссылки при построении графа
        console.warn(`⚠️  Предупреждение при анализе ${key}: ${e.message}`);
      }
    }

    graph.set(key, dependencies);
  }

  return graph;
}

/**
 * Топологическая сортировка для определения порядка вычисления
 * @param {Map<string, Set<string>>} graph - Граф зависимостей
 * @returns {string[]} Порядок вычисления (без циклов)
 */
function topologicalSort(graph) {
  const sorted = [];
  const visited = new Set();
  const temp = new Set(); // для обнаружения циклов

  function visit(node, path = []) {
    if (temp.has(node)) {
      throw new CircularDependencyError(
        `Циклическая зависимость в computed: ${[...path, node].join(' → ')}`,
        [...path, node]
      );
    }
    if (visited.has(node)) {
      return;
    }

    temp.add(node);
    const deps = graph.get(node) || new Set();

    for (const dep of deps) {
      if (graph.has(dep)) {
        visit(dep, [...path, node]);
      }
    }

    temp.delete(node);
    visited.add(node);
    sorted.push(node);
  }

  for (const node of graph.keys()) {
    if (!visited.has(node)) {
      visit(node);
    }
  }

  return sorted;
}

// ============================================================================
// JSON Contract Parser (Main Class)
// ============================================================================

/**
 * Парсер для разрешения сложных JSON-контрактов
 *
 * Архитектура:
 * 1. Загрузка контракта и данных
 * 2. Интеграция моковых данных в state
 * 3. Построение графа зависимостей computed
 * 4. Топологическая сортировка для правильного порядка вычисления
 * 5. Вычисление computed с кэшированием
 * 6. Рекурсивное разрешение rootElement
 * 7. Обработка computed, data, state ссылок
 * 8. Вычисление условных выражений (if-then-else)
 * 9. Развертывание $children массивов
 */
class JSONContractParser {
  /**
   * Инициализация парсера
   * @param {string} contractPath - Путь к файлу с контрактом
   * @param {string} dataPath - Путь к файлу с моковыми данными
   * @param {Object} options - Опции { verbose, debug }
   */
  constructor(contractPath, dataPath, options = {}) {
    this.options = {
      verbose: false,
      debug: false,
      ...options
    };

    this.tracker = new PerformanceTracker();
    this.tracker.startTimer('total');

    // Загрузка файлов
    this.log('info', `📂 Загрузка контракта: ${contractPath}`);
    this.contract = JSON.parse(fs.readFileSync(contractPath, 'utf8'));

    this.log('info', `📂 Загрузка моковых данных: ${dataPath}`);
    this.mockData = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

    // Извлечение секций
    this.computed = this.contract.computed || {};
    this.data = this.contract.data || {};
    this.state = this.contract.state || {};
    this.rootElement = this.contract.rootElement || {};

    this.log('info',
      `✅ Загружено: ${Object.keys(this.computed).length} computed, ` +
      `${Object.keys(this.data).length} data, ` +
      `${Object.keys(this.state).length} state`
    );

    // Кэш для computed значений
    this.computedCache = {};

    // Стек для отслеживания циклов
    this.resolutionStack = [];
  }

  /**
   * Логирование с учетом уровня verbose/debug
   * @param {string} level - Уровень: 'info', 'debug', 'warn', 'error'
   * @param {string} message - Сообщение
   */
  log(level, message) {
    if (level === 'error' || level === 'warn') {
      console[level](message);
    } else if (level === 'debug' && this.options.debug) {
      console.log(message);
    } else if (level === 'info' && (this.options.verbose || this.options.debug)) {
      console.log(message);
    }
  }

  /**
   * Основной метод парсинга
   * @returns {Object} Полностью распарсенный JSON с единственным ключом rootElement
   */
  parse() {
    try {
      this.log('info', '\n🚀 Начало парсинга контракта...');

      // Шаг 1: Интеграция моковых данных
      this.log('info', '\n📊 Интеграция моковых данных...');
      this.integrateMonkey();

      // Шаг 2: Построение графа зависимостей
      this.log('debug', '\n📊 Построение графа зависимостей...');
      const graph = buildDependencyGraph(this.computed);

      if (this.options.debug) {
        console.log('📊 Граф зависимостей:');
        for (const [key, deps] of graph.entries()) {
          if (deps.size > 0) {
            console.log(`  ${key} → [${Array.from(deps).join(', ')}]`);
          }
        }
      }

      // Шаг 3: Топологическая сортировка
      this.log('debug', '\n🔄 Топологическая сортировка...');
      const order = topologicalSort(graph);

      if (this.options.debug) {
        console.log(`✅ Порядок вычисления: [${order.join(' → ')}]`);
      }

      // Шаг 4: Вычисление computed
      this.log('info', '\n⚙️  Вычисление computed...');
      this.tracker.startTimer('computed');
      this.evaluateComputedOrdered(order);
      const computedTime = this.tracker.stopTimer('computed');
      this.log('info', `✅ Computed вычислено за ${computedTime}ms`);

      // Шаг 5: Разрешение rootElement
      this.log('info', '\n🔧 Разрешение rootElement...');
      this.tracker.startTimer('resolution');
      const resolvedRoot = this.resolveValue(this.rootElement, 'rootElement');
      const resolutionTime = this.tracker.stopTimer('resolution');
      this.log('info', `✅ RootElement разрешен за ${resolutionTime}ms`);

      // Формируем результат
      const result = { rootElement: resolvedRoot };

      // Статистика
      const totalTime = this.tracker.stopTimer('total');
      this.printStats(result, totalTime);

      return result;

    } catch (error) {
      if (error instanceof CircularDependencyError) {
        console.error(`\n🔄 Обнаружена циклическая зависимость:`);
        console.error(`   ${error.cycle.join(' → ')}`);
      } else if (error instanceof ResolutionError) {
        console.error(`\n❌ Ошибка разрешения: ${error.message}`);
        if (error.context) {
          console.error(`   Контекст:`, JSON.stringify(error.context, null, 2));
        }
      } else {
        console.error(`\n❌ Неожиданная ошибка: ${error.message}`);
      }

      if (this.options.debug) {
        console.error('\nStack trace:');
        console.error(error.stack);
      }

      throw error;
    }
  }

  /**
   * Интегрирует моковые данные в state
   */
  integrateMonkey() {
    let count = 0;
    for (const [key, value] of Object.entries(this.mockData)) {
      if (!this.state.hasOwnProperty(key)) {
        this.state[key] = value;
        count++;
        this.log('debug', `  + Добавлено в state: ${key}`);
      }
    }
    this.log('info', `  ✓ Интегрировано полей: ${count}`);
  }

  /**
   * Вычисляет computed поля в правильном порядке с учётом зависимостей
   * @param {string[]} order - Порядок вычисления из топологической сортировки
   */
  evaluateComputedOrdered(order) {
    // Создаём расширенный контекст
    const context = {
      data: this.data,
      state: this.state,
      computed: {} // постепенно заполняем
    };

    for (const key of order) {
      // Проверяем кэш
      if (this.computedCache[key] !== undefined) {
        this.log('debug', `💾 Кэш: computed.${key}`);
        this.tracker.increment('cache_hits');
        context.computed[key] = this.computedCache[key];
        continue;
      }

      const node = this.computed[key];
      if (!node) continue;

      this.log('debug', `⚙️  Вычисление: computed.${key}`);

      let value;
      try {
        // Обработка if-выражений
        if (typeof node === 'object' && node !== null && node.type === 'if') {
          value = this.resolveIfExpression(node, context, `computed.${key}`);
        }
        // Обработка строк с template strings
        else if (typeof node === 'string') {
          value = this.resolveString(node, context, `computed.${key}`);
        }
        // Остальные типы
        else {
          value = this.resolveValue(node, `computed.${key}`, context);
        }
      } catch (error) {
        throw new ResolutionError(
          `Ошибка при вычислении computed.${key}: ${error.message}`,
          { key, node }
        );
      }

      this.log('debug', `  ✅ computed.${key} = ${JSON.stringify(value).slice(0, 100)}`);

      this.computedCache[key] = value;
      context.computed[key] = value;
      this.tracker.increment('computed_resolved');
    }

    // Обновляем computed в парсере
    this.computed = context.computed;
  }

  /**
   * Разрешает условное выражение if-then-else
   * @param {Object} expr - Объект с type: 'if'
   * @param {Object} context - Контекст разрешения
   * @param {string} path - Путь для логирования
   * @returns {*} Результат вычисления условия
   */
  resolveIfExpression(expr, context, path = '') {
    this.tracker.increment('if_expressions');

    // Получаем условие (может быть в 'if' или '$if')
    const conditionRef = expr.$if ?? expr.if;
    const thenValue = expr.$then ?? expr.then;
    const elseValue = expr.$else ?? expr.else;

    this.log('debug', `  ❓ IF-выражение at ${path}`);
    this.log('debug', `    Условие: ${conditionRef}`);

    // Разрешаем условие
    let condition;
    if (typeof conditionRef === 'string') {
      condition = this.resolveString(conditionRef, context, `${path}.if`);
    } else {
      condition = conditionRef;
    }

    this.log('debug', `    Результат условия: ${condition}`);

    // Выбираем ветку и разрешаем её
    const branchValue = condition ? thenValue : elseValue;

    if (condition) {
      this.log('debug', `    ✓ THEN ветка`);
    } else {
      this.log('debug', `    ✗ ELSE ветка`);
    }

    // ИСПРАВЛЕНИЕ: используем логику из v2.1.0 - разрешаем путь напрямую
    return this.resolveValue(branchValue, `${path}.${condition ? '$then' : '$else'}`, context);
  }

  /**
   * Разрешает строковые подстановки вида ${...}
   * Поддерживает как полные "${data.x}", так и частичные "Hello ${data.name}!"
   * @param {string} string - Строка для обработки
   * @param {Object} context - Контекст разрешения
   * @param {string} path - Путь для логирования
   * @returns {*} Разрешенное значение (может быть не строкой)
   */
  resolveString(string, context, path = '') {
    // Случай 1: Полная подстановка "${...}"
    if (isTemplateRef(string)) {
      this.log('debug', `  🔗 Подстановка: ${path} → ${string}`);
      this.tracker.increment('substitutions');
      return resolvePath(context, string, this.resolutionStack, this.options.debug);
    }

    // Случай 2: Частичная подстановка "text ${...} text"
    if (string.includes('${')) {
      this.log('debug', `  🔗 Частичная подстановка в: ${path}`);

      const result = string.replace(/\$\{([^}]+)\}/g, (match, refPath) => {
        const fullRef = `\${${refPath}}`;
        this.log('debug', `    ├─ ${fullRef}`);
        const resolved = resolvePath(context, fullRef, this.resolutionStack, this.options.debug);
        this.tracker.increment('substitutions');
        return resolved != null ? String(resolved) : '';
      });

      return result;
    }

    // Случай 3: Обычная строка
    return string;
  }

  /**
   * Рекурсивно разрешает значение
   * @param {*} value - Значение для разрешения
   * @param {string} path - Путь для отладки
   * @param {Object} context - Контекст (по умолчанию создается из парсера)
   * @returns {*} Разрешенное значение
   */
  resolveValue(value, path = '', context = null) {
    // Создаем контекст если не передан
    if (!context) {
      context = {
        data: this.data,
        state: this.state,
        computed: this.computed
      };
    }

    // Проверка на циклы
    if (this.resolutionStack.includes(path)) {
      throw new CircularDependencyError(
        `Циклическая зависимость в ${path}`,
        [...this.resolutionStack, path]
      );
    }

    this.resolutionStack.push(path);

    try {
      // Строки - проверяем на подстановки
      if (typeof value === 'string') {
        return this.resolveString(value, context, path);
      }

      // Списки - обрабатываем каждый элемент и фильтруем артефакты
      if (Array.isArray(value)) {
        const resolved = value.map((item, i) =>
          this.resolveValue(item, `${path}[${i}]`, context)
        );

        // Фильтруем пустые объекты {} и null значения
        return resolved.filter(item => {
          // Удаляем null и undefined
          if (item == null) return false;

          // Удаляем пустые объекты {}
          if (typeof item === 'object' && !Array.isArray(item) && Object.keys(item).length === 0) {
            return false;
          }

          return true;
        });
      }

      // Словари - обрабатываем специальные случаи
      if (typeof value === 'object' && value !== null) {
        return this.resolveDict(value, path, context);
      }

      // Остальные типы возвращаем как есть
      return value;

    } finally {
      this.resolutionStack.pop();
    }
  }

  /**
   * Разрешает словарь, обрабатывая специальные ключи
   * @param {Object} obj - Словарь для обработки
   * @param {string} path - Путь для логирования
   * @param {Object} context - Контекст разрешения
   * @returns {Object} Разрешенный словарь
   */
  resolveDict(obj, path = '', context) {
    // Проверяем на условное выражение
    if (obj.type === 'if') {
      return this.resolveIfExpression(obj, context, path);
    }

    const result = {};

    for (const [key, value] of Object.entries(obj)) {
      // Обрабатываем $children - специальный массив с подстановками
      if (key === '$children') {
        const children = this.resolveValue(value, `${path}.$children`, context);
        if (Array.isArray(children)) {
          result.children = children;
          this.tracker.increment('children_expanded');
          this.log('debug', `  📦 $children развернуто в ${children.length} элементов`);
        } else {
          result.children = [children];
        }
      }
      // ИСПРАВЛЕНИЕ: Пропускаем все служебные ключи с $ кроме type (как в v2.1.0)
      else if (key.startsWith('$') && key !== 'type') {
        continue;
      }
      // Обычные ключи
      else {
        result[key] = this.resolveValue(value, `${path}.${key}`, context);
      }
    }

    return result;
  }

  /**
   * Выводит детальную статистику парсинга
   * @param {Object} result - Результат парсинга
   * @param {number} totalTime - Общее время выполнения
   */
  printStats(result, totalTime) {
    const stats = this.tracker.getStats();
    const size = JSON.stringify(result).length;

    console.log('\n' + '='.repeat(60));
    console.log('📈 СТАТИСТИКА ПАРСИНГА');
    console.log('='.repeat(60));
    console.log(`⏱️  Общее время:          ${totalTime}ms`);
    console.log(`📊 Размер результата:     ${size.toLocaleString()} символов (${(size / 1024).toFixed(1)} KB)`);
    console.log(`⚙️  Computed разрешено:    ${stats.computed_resolved}`);
    console.log(`💾 Кэш использован:       ${stats.cache_hits} раз`);
    console.log(`🔗 Подстановок выполнено: ${stats.substitutions}`);
    console.log(`❓ IF-выражений:          ${stats.if_expressions}`);
    console.log(`📦 $children развернуто:  ${stats.children_expanded}`);
    console.log('='.repeat(60));
  }
}

// ============================================================================
// CLI Entry Point
// ============================================================================

/**
 * Основная функция для запуска парсера
 */
function main() {
  const args = process.argv.slice(2);

  // Справка
  if (args.includes('--help') || args.includes('-h')) {
    console.log(`
JSON Contract Parser v2.2.1
============================

Использование:
  node computed_data_parser_v2.2.1.js <contract.json> <data.json> [output.json] [options]

Аргументы:
  contract.json    Файл с JSON-контрактом
  data.json        Файл с моковыми данными
  output.json      Файл для сохранения результата (по умолчанию: pure.json в директории контракта)

Опции:
  -v, --verbose    Подробное логирование
  -d, --debug      Отладочная информация (включает verbose)
  -h, --help       Показать эту справку

Примеры:
  node computed_data_parser_v2.2.1.js contract.json data.json
  node computed_data_parser_v2.2.1.js contract.json data.json result.json -v
  node computed_data_parser_v2.2.1.js contract.json data.json result.json --debug
`);
    process.exit(0);
  }

  // Парсинг аргументов
  const contractPath = args[0] || './contract.json';
  const dataPath = args[1] || './data.json';

  // Выходной файл сохраняется в директорию первого входного файла, если не указан явно
  const outputPath = args[2] && !args[2].startsWith('-')
    ? args[2]
    : path.join(path.dirname(contractPath), 'pure.json');

  const options = {
    verbose: args.includes('--verbose') || args.includes('-v'),
    debug: args.includes('--debug') || args.includes('-d')
  };

  try {
    // Проверка существования файлов
    if (!fs.existsSync(contractPath)) {
      console.error(`❌ Файл не найден: ${contractPath}`);
      process.exit(1);
    }

    if (!fs.existsSync(dataPath)) {
      console.error(`❌ Файл не найден: ${dataPath}`);
      process.exit(1);
    }

    // Создаем парсер и выполняем парсинг
    const parser = new JSONContractParser(contractPath, dataPath, options);
    const result = parser.parse();

    // Сохраняем результат
    fs.writeFileSync(outputPath, JSON.stringify(result, null, 2), 'utf8');

    console.log(`\n✅ Парсинг успешно завершен!`);
    console.log(`📄 Результат сохранен в: ${path.resolve(outputPath)}`);

  } catch (error) {
    console.error(`\n❌ Парсинг завершился с ошибкой`);
    process.exit(1);
  }
}

// Запуск CLI если модуль вызван напрямую
if (require.main === module) {
  main();
}

// ============================================================================
// Module Exports
// ============================================================================

module.exports = {
  JSONContractParser,
  ResolutionError,
  CircularDependencyError,
  PerformanceTracker,
  // Utility functions
  isTemplateRef,
  parsePath,
  resolvePath,
  extractRefs,
  buildDependencyGraph,
  topologicalSort
};
