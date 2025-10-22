#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// === Утилиты ===

function isTemplateRef(value) {
  return typeof value === 'string' && value.startsWith('${') && value.endsWith('}') && !value.slice(2, -1).includes('${');
}

function parsePath(pathStr) {
  if (!isTemplateRef(pathStr)) {
    throw new Error(`parsePath expects a template ref, got: ${pathStr}`);
  }

  let clean = pathStr.slice(2, -1);
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

function resolvePath(context, pathStr, resolutionStack = [], debug = false) {
  if (!isTemplateRef(pathStr)) return pathStr;

  // Защита от циклов
  if (resolutionStack.includes(pathStr)) {
    throw new Error(`🔄 Циклическая зависимость: ${resolutionStack.join(' → ')} → ${pathStr}`);
  }

  const parts = parsePath(pathStr);
  let current = context;

  if (debug) {
    console.log(`  🔍 Разрешение пути: ${pathStr} → [${parts.join(', ')}]`);
  }

  for (const part of parts) {
    if (current == null || (typeof current !== 'object' && typeof current !== 'function')) {
      throw new Error(`❌ Не удалось разрешить путь: ${pathStr} на части "${part}"`);
    }
    current = current[part];

    if (debug) {
      console.log(`    ├─ ${part} = ${JSON.stringify(current).slice(0, 50)}`);
    }
  }

  if (debug) {
    console.log(`    └─ Результат: ${JSON.stringify(current)}`);
  }

  return current;
}

// === Анализ зависимостей computed ===

/**
 * Строит граф зависимостей между computed-полями
 * @param {Object} computed - Объект computed из контракта
 * @returns {Map<string, Set<string>>} - Граф зависимостей (ключ → зависит от)
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
 * Рекурсивно извлекает все ${...} ссылки из объекта
 */
function extractRefs(obj, refs = new Set()) {
  if (typeof obj === 'string') {
    // ИСПРАВЛЕНИЕ: Полная ссылка ${...}
    if (isTemplateRef(obj)) {
      refs.add(obj);
    }
    // ИСПРАВЛЕНИЕ: Частичные подстановки "Hello ${name}!"
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
 * Топологическая сортировка для определения порядка вычисления
 * @param {Map<string, Set<string>>} graph - Граф зависимостей
 * @returns {string[]} - Порядок вычисления (без циклов)
 */
function topologicalSort(graph) {
  const sorted = [];
  const visited = new Set();
  const temp = new Set(); // для обнаружения циклов

  function visit(node) {
    if (temp.has(node)) {
      throw new Error(`🔄 Циклическая зависимость в computed: ${node}`);
    }
    if (visited.has(node)) {
      return;
    }

    temp.add(node);
    const deps = graph.get(node) || new Set();

    for (const dep of deps) {
      if (graph.has(dep)) {
        visit(dep);
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

// === Вычисление computed с правильным порядком разрешения ===

/**
 * Вычисляет computed поля в правильном порядке с учётом зависимостей
 * @param {Object} computed - Объект computed из контракта
 * @param {Object} context - Контекст (data, state)
 * @param {Object} options - Опции { debug, cache }
 * @returns {Object} - Вычисленные значения
 */
function evaluateComputed(computed, context, options = {}) {
  const { debug = false, cache = {} } = options;
  const result = {};

  // Шаг 1: Строим граф зависимостей
  if (debug) console.log('📊 Построение графа зависимостей...');
  const graph = buildDependencyGraph(computed);

  if (debug) {
    console.log('📊 Граф зависимостей:');
    for (const [key, deps] of graph.entries()) {
      if (deps.size > 0) {
        console.log(`  ${key} → [${Array.from(deps).join(', ')}]`);
      }
    }
  }

  // Шаг 2: Топологическая сортировка
  if (debug) console.log('🔄 Топологическая сортировка...');
  let order;
  try {
    order = topologicalSort(graph);
  } catch (err) {
    throw new Error(`❌ Ошибка при сортировке зависимостей: ${err.message}`);
  }

  if (debug) {
    console.log(`✅ Порядок вычисления: [${order.join(' → ')}]`);
  }

  // Шаг 3: Вычисляем в правильном порядке
  // Создаём расширенный контекст, который будет пополняться
  const extendedContext = {
    ...context,
    computed: {} // постепенно заполняем вычисленными значениями
  };

  for (const key of order) {
    // Проверяем кэш
    if (cache[key] !== undefined) {
      if (debug) console.log(`💾 Кэш: computed.${key} = ${JSON.stringify(cache[key])}`);
      result[key] = cache[key];
      extendedContext.computed[key] = cache[key];
      continue;
    }

    const node = computed[key];
    if (!node) continue; // может быть зависимость, которой нет в computed

    if (debug) console.log(`⚙️  Вычисление: computed.${key}`);

    let value;
    const resolutionStack = [`computed.${key}`];

    try {
      if (node.type === 'if') {
        const conditionPath = node.$if ?? node.if;
        if (debug) console.log(`  🔀 if-условие: ${conditionPath}`);

        const condition = resolvePath(extendedContext, conditionPath, resolutionStack, debug);
        const branchPath = condition ? (node.$then ?? node.then) : (node.$else ?? node.else);

        if (debug) console.log(`  🔀 Ветка: ${condition ? 'then' : 'else'} → ${branchPath}`);

        value = resolvePath(extendedContext, branchPath, resolutionStack, debug);
      } else if (typeof node === 'string') {
        // ИСПРАВЛЕНИЕ: Обработка template strings с частичными подстановками
        if (isTemplateRef(node)) {
          // Полная подстановка
          value = resolvePath(extendedContext, node, resolutionStack, debug);
        } else if (node.includes('${')) {
          // Частичная подстановка "Hello ${name}!"
          if (debug) console.log(`  🔀 Частичная подстановка: ${node}`);
          value = node.replace(/\$\{([^}]+)\}/g, (match, path) => {
            const fullRef = `\${${path}}`;
            if (debug) console.log(`    ├─ Подстановка: ${fullRef}`);
            const resolved = resolvePath(extendedContext, fullRef, resolutionStack, debug);
            return resolved != null ? String(resolved) : '';
          });
        } else {
          // Обычная строка
          value = node;
        }
      } else {
        // Объекты и другие типы
        value = resolvePath(extendedContext, node, resolutionStack, debug);
      }
    } catch (err) {
      throw new Error(`❌ Ошибка при вычислении computed.${key}: ${err.message}`);
    }

    if (debug) console.log(`  ✅ computed.${key} = ${JSON.stringify(value)}`);

    cache[key] = value;
    result[key] = value;
    // КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: добавляем в контекст сразу
    extendedContext.computed[key] = value;
  }

  return result;
}

// === Подстановка с поддержкой частичных шаблонов ===

function substitute(obj, context, resolutionStack = [], debug = false) {
  if (obj == null) return obj;

  if (Array.isArray(obj)) {
    return obj.map(item => substitute(item, context, resolutionStack, debug));
  }

  if (typeof obj === 'object') {
    // Обработка $children
    if (obj.$children) {
      const resolvedChildren = obj.$children.map(childRef => {
        const resolved = resolvePath(context, childRef, resolutionStack, debug);
        return substitute(resolved, context, resolutionStack, debug);
      });
      const newObj = { ...obj };
      delete newObj.$children;
      newObj.children = resolvedChildren;
      return substitute(newObj, context, resolutionStack, debug);
    }

    const newObj = {};
    for (const key in obj) {
      if (key.startsWith('$') && key !== 'type') continue;
      newObj[key] = substitute(obj[key], context, resolutionStack, debug);
    }
    return newObj;
  }

  // Частичные подстановки в строках
  if (typeof obj === 'string') {
    // Полная подстановка
    if (isTemplateRef(obj)) {
      return resolvePath(context, obj, resolutionStack, debug);
    }

    // Частичная подстановка "Hello ${name}!"
    if (obj.includes('${')) {
      return obj.replace(/\$\{([^}]+)\}/g, (match, path) => {
        const resolved = resolvePath(context, `\${${path}}`, resolutionStack, debug);
        return resolved != null ? String(resolved) : '';
      });
    }
  }

  return obj;
}

// === Основной запуск ===

function main() {
  const args = process.argv.slice(2);
  const contractPath = args[0] || './contract.json';
  const dataPath = args[1] || './data.json';
  const outputPath = args[2] || './pure.json';

  // Флаги
  const verbose = args.includes('--verbose') || args.includes('-v');
  const debug = args.includes('--debug') || args.includes('-d');

  try {
    if (verbose) console.log('📂 Загрузка контракта:', contractPath);
    const contract = JSON.parse(fs.readFileSync(contractPath, 'utf8'));

    if (verbose) console.log('📂 Загрузка данных:', dataPath);
    const externalData = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

    // Создаём контекст: data + state + внешние данные
    const context = {
      data: contract.data || {},
      state: { ...(contract.state || {}), ...externalData },
    };

    if (verbose) {
      console.log(`✅ Загружено: ${Object.keys(contract.computed || {}).length} computed, ${Object.keys(contract.data || {}).length} data, ${Object.keys(context.state).length} state`);
    }

    // Вычисляем computed с кэшированием и правильным порядком
    if (verbose || debug) console.log('\n⚙️  Вычисление computed...');
    const computedCache = {};
    const computed = evaluateComputed(
      contract.computed || {},
      context,
      { debug, cache: computedCache }
    );

    if (verbose || debug) {
      console.log(`\n✅ Computed вычислено: ${Object.keys(computed).length} полей`);
      if (debug) {
        console.log('📋 Значения computed:');
        for (const [key, value] of Object.entries(computed)) {
          console.log(`  ${key}: ${JSON.stringify(value)}`);
        }
      }
    }

    // Расширяем контекст
    const fullContext = { ...context, computed };

    // Подстановка в rootElement
    if (verbose || debug) console.log('\n🔧 Разрешение rootElement...');
    const pureRoot = substitute(contract.rootElement, fullContext, [], debug);

    // Формируем итог
    const output = { rootElement: pureRoot };

    // Сохраняем
    fs.writeFileSync(outputPath, JSON.stringify(output, null, 2), 'utf8');

    // Статистика
    const size = JSON.stringify(output).length;
    console.log(`\n✅ Готово! Результат сохранён в ${path.resolve(outputPath)}`);
    if (verbose) {
      console.log(`📊 Размер: ${size.toLocaleString()} символов (${(size / 1024).toFixed(1)} KB)`);
      console.log(`📈 Computed кэшировано: ${Object.keys(computedCache).length}`);
    }

  } catch (err) {
    console.error('\n❌ Ошибка:', err.message);
    if (verbose || debug) console.error(err.stack);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { substitute, evaluateComputed, resolvePath, buildDependencyGraph, topologicalSort };
