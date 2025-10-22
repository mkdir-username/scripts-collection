#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// === Утилиты ===

function isTemplateRef(value) {
  return typeof value === 'string' && value.startsWith('${') && value.endsWith('}');
}

function parsePath(pathStr) {
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

function resolvePath(context, pathStr, resolutionStack = []) {
  if (!isTemplateRef(pathStr)) return pathStr;
  
  // ✨ УЛУЧШЕНИЕ 1: Защита от циклов
  if (resolutionStack.includes(pathStr)) {
    throw new Error(`🔄 Циклическая зависимость: ${resolutionStack.join(' → ')} → ${pathStr}`);
  }
  
  const parts = parsePath(pathStr);
  let current = context;
  
  for (const part of parts) {
    if (current == null || (typeof current !== 'object' && typeof current !== 'function')) {
      // ✨ УЛУЧШЕНИЕ 2: Более информативная ошибка
      throw new Error(`❌ Не удалось разрешить путь: ${pathStr} на части "${part}"`);
    }
    current = current[part];
  }
  
  return current;
}

// === Вычисление computed с кэшированием ===

function evaluateComputed(computed, context, cache = {}, resolutionStack = []) {
  const result = {};
  
  for (const key in computed) {
    // ✨ УЛУЧШЕНИЕ 3: Кэширование computed
    if (cache[key] !== undefined) {
      result[key] = cache[key];
      continue;
    }

    const node = computed[key];
    let value;
    
    // Добавляем в стек для отслеживания циклов
    resolutionStack.push(`computed.${key}`);

    try {
      if (node.type === 'if') {
        const conditionPath = node.$if ?? node.if;
        const condition = resolvePath(context, conditionPath, resolutionStack);
        const branchPath = condition ? (node.$then ?? node.then) : (node.$else ?? node.else);
        value = resolvePath(context, branchPath, resolutionStack);
      } else {
        value = resolvePath(context, node, resolutionStack);
      }
    } finally {
      resolutionStack.pop();
    }

    cache[key] = value;
    result[key] = value;
  }
  
  return result;
}

// === Подстановка с поддержкой частичных шаблонов ===

function substitute(obj, context, resolutionStack = []) {
  if (obj == null) return obj;

  if (Array.isArray(obj)) {
    return obj.map(item => substitute(item, context, resolutionStack));
  }

  if (typeof obj === 'object') {
    // Обработка $children
    if (obj.$children) {
      const resolvedChildren = obj.$children.map(childRef => {
        const resolved = resolvePath(context, childRef, resolutionStack);
        return substitute(resolved, context, resolutionStack);
      });
      const newObj = { ...obj };
      delete newObj.$children;
      newObj.children = resolvedChildren;
      return substitute(newObj, context, resolutionStack);
    }

    // ✨ ВАЖНО: Пустые объекты {} сохраняются как есть
    // Это корректный паттерн для SDUI компонентов, например:
    // { "type": "Spacer", "content": {}, "hidden": false }
    // Пустой content: {} указывает на отсутствие содержимого, но поле должно присутствовать
    const newObj = {};
    for (const key in obj) {
      if (key.startsWith('$') && key !== 'type') continue;
      newObj[key] = substitute(obj[key], context, resolutionStack);
    }
    return newObj;
  }

  // ✨ УЛУЧШЕНИЕ 4: Частичные подстановки в строках
  if (typeof obj === 'string') {
    // Полная подстановка
    if (isTemplateRef(obj)) {
      return resolvePath(context, obj, resolutionStack);
    }
    
    // Частичная подстановка "Hello ${name}!"
    if (obj.includes('${')) {
      return obj.replace(/\$\{([^}]+)\}/g, (match, path) => {
        const resolved = resolvePath(context, `\${${path}}`, resolutionStack);
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
  
  // ✨ УЛУЧШЕНИЕ 5: Флаг verbose
  const verbose = args.includes('--verbose') || args.includes('-v');

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

    // Вычисляем computed с кэшированием
    if (verbose) console.log('⚙️  Вычисление computed...');
    const computedCache = {};
    const computed = evaluateComputed(contract.computed || {}, context, computedCache);

    // Расширяем контекст
    const fullContext = { ...context, computed };

    // Подстановка в rootElement
    if (verbose) console.log('🔧 Разрешение rootElement...');
    const pureRoot = substitute(contract.rootElement, fullContext);

    // Формируем итог
    const output = { rootElement: pureRoot };

    // Сохраняем
    fs.writeFileSync(outputPath, JSON.stringify(output, null, 2), 'utf8');
    
    // ✨ УЛУЧШЕНИЕ 6: Статистика
    const size = JSON.stringify(output).length;
    console.log(`✅ Готово! Результат сохранён в ${path.resolve(outputPath)}`);
    if (verbose) {
      console.log(`📊 Размер: ${size.toLocaleString()} символов (${(size / 1024).toFixed(1)} KB)`);
      console.log(`📈 Computed кэшировано: ${Object.keys(computedCache).length}`);
    }

  } catch (err) {
    console.error('❌ Ошибка:', err.message);
    if (verbose) console.error(err.stack);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = { substitute, evaluateComputed, resolvePath };
