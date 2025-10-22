#!/usr/bin/env node

/**
 * Test Suite: Обработка пустых объектов в SDUI контрактах
 * 
 * Пустые объекты {} являются валидным паттерном в SDUI:
 * - content: {} - компонент без содержимого
 * - params: {} - параметры по умолчанию
 * - data: {} - пустой data payload
 * 
 * Парсер ДОЛЖЕН сохранять эти пустые объекты в выходных данных.
 * 
 * @version 1.0.0
 * @date 2025-01-07
 */

const { substitute, evaluateComputed, resolvePath } = require('../computed_data_parser_v2.js');

// Утилиты
function assert(condition, message) {
  if (!condition) {
    throw new Error(`❌ ${message}`);
  }
}

function testCase(name, fn) {
  try {
    fn();
    console.log(`✅  ${name}`);
    return true;
  } catch (error) {
    console.log(`❌  ${name}`);
    console.log(`    ${error.message}`);
    return false;
  }
}

console.log('╭─────────────────────────────────────────────────────────────╮');
console.log('│  Test Suite: Обработка пустых объектов {}                  │');
console.log('╰─────────────────────────────────────────────────────────────╯\n');

const context = { data: {}, state: {} };
let passed = 0;
let failed = 0;

// TEST GROUP 1: Spacer компоненты
console.log('🧪  Test Group 1: Spacer компоненты\n');

if (testCase('Spacer с пустым content сохраняется полностью', () => {
  const spacer = {
    type: "Spacer",
    size: { height: 4 },
    content: {},
    hidden: false,
    version: 1
  };
  
  const result = substitute(spacer, context);
  
  assert(result.type === 'Spacer', 'type должен быть Spacer');
  assert('content' in result, 'content должен присутствовать');
  assert(typeof result.content === 'object', 'content должен быть объектом');
  assert(Object.keys(result.content).length === 0, 'content должен быть пустым');
  assert(result.hidden === false, 'hidden должен быть false');
  assert(result.version === 1, 'version должен быть 1');
})) passed++; else failed++;

if (testCase('Spacer без content остается без content', () => {
  const spacer = {
    type: "Spacer",
    size: { height: 30 }
  };
  
  const result = substitute(spacer, context);
  
  assert(result.type === 'Spacer', 'type должен быть Spacer');
  assert(!('content' in result), 'content НЕ должен присутствовать');
  assert('size' in result, 'size должен присутствовать');
})) passed++; else failed++;

// TEST GROUP 2: Вложенные пустые объекты
console.log('\n🧪  Test Group 2: Вложенные пустые объекты\n');

if (testCase('Глубоко вложенные пустые объекты сохраняются', () => {
  const nested = {
    level1: {
      level2: {
        level3: {
          data: {}
        }
      }
    }
  };
  
  const result = substitute(nested, context);
  
  assert('data' in result.level1.level2.level3, 'data должен присутствовать');
  assert(Object.keys(result.level1.level2.level3.data).length === 0, 'data должен быть пустым');
})) passed++; else failed++;

// TEST GROUP 3: Массивы с пустыми объектами
console.log('\n🧪  Test Group 3: Массивы с пустыми объектами\n');

if (testCase('Массив с пустыми объектами сохраняется', () => {
  const arr = {
    items: [
      {},
      { id: 1 },
      {},
      { id: 2, data: {} }
    ]
  };
  
  const result = substitute(arr, context);
  
  assert(Array.isArray(result.items), 'items должен быть массивом');
  assert(result.items.length === 4, 'длина массива должна быть 4');
  assert(Object.keys(result.items[0]).length === 0, 'items[0] должен быть пустым');
  assert(Object.keys(result.items[2]).length === 0, 'items[2] должен быть пустым');
  assert('data' in result.items[3], 'items[3] должен иметь data');
  assert(Object.keys(result.items[3].data).length === 0, 'items[3].data должен быть пустым');
})) passed++; else failed++;

// TEST GROUP 4: Реальный кейс из продакшна
console.log('\n🧪  Test Group 4: Реальный продакшн кейс\n');

if (testCase('Полный SDUI компонент с пустыми полями', () => {
  const component = {
    type: "Container",
    content: {
      children: [
        {
          type: "Text",
          content: { value: "Hello" }
        },
        {
          type: "Spacer",
          size: { height: 4 },
          content: {},
          hidden: false,
          version: 1
        },
        {
          type: "Button",
          content: {
            title: "Click",
            params: {}
          }
        }
      ]
    }
  };
  
  const result = substitute(component, context);
  
  const spacer = result.content.children[1];
  assert('content' in spacer, 'Spacer должен иметь content');
  assert(Object.keys(spacer.content).length === 0, 'Spacer.content должен быть пустым');
  
  const button = result.content.children[2];
  assert('params' in button.content, 'Button должен иметь params');
  assert(Object.keys(button.content.params).length === 0, 'Button.params должен быть пустым');
})) passed++; else failed++;

// FINAL REPORT
console.log('\n╭─────────────────────────────────────────────────────────────╮');
console.log('│  ИТОГОВЫЙ ОТЧЕТ                                             │');
console.log('╰─────────────────────────────────────────────────────────────╯\n');

console.log(`Всего тестов:  ${passed + failed}`);
console.log(`Пройдено:      ${passed} ✅`);
console.log(`Провалено:     ${failed} ❌`);
console.log(`Успешность:    ${((passed / (passed + failed)) * 100).toFixed(1)}%\n`);

if (failed === 0) {
  console.log('🎉  Все тесты пройдены! Парсер корректно обрабатывает пустые объекты.\n');
  process.exit(0);
} else {
  console.log('⚠️   Некоторые тесты провалились. Требуется исправление.\n');
  process.exit(1);
}
