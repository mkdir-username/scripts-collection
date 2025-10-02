#!/usr/bin/env node
"use strict";
/**
 * VSCode On-Save Validator v2.0.0
 *
 * Автоматическая валидация SDUI контрактов при сохранении в VSCode
 * Использует новый дизайн вывода с прогресс-барами, группировкой и box drawing
 *
 * Usage:
 *   node vscode-validate-on-save_v2.0.0.js path/to/contract.json
 *
 * Dependencies:
 *   npm install jsonc-parser
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const fs_1 = require("fs");
const path_1 = require("path");
const jsoncParser = __importStar(require("jsonc-parser"));
const PROJECT_ROOT = process.env.PROJECT_ROOT ||
    '/Users/username/Documents/front-middle-schema';
// Путь к MCP серверу с валидатором
const MCP_ROOT = '/Users/username/Scripts/alfa-sdui-mcp';
// Получить путь к файлу из аргументов
const filePath = process.argv[2];
if (!filePath) {
    console.error('❌ ERROR: Путь к файлу не указан');
    console.error('Usage: node vscode-validate-on-save_v2.0.0.js <file>');
    process.exit(1);
}
// ============================================================================
// ФОРМАТТЕРЫ
// ============================================================================
/**
 * Прогресс-бар
 */
function renderProgressBar(current, total, width = 20) {
    const percentage = total === 0 ? 0 : Math.floor((current / total) * 100);
    const filledBlocks = total === 0 ? 0 : Math.floor((current / total) * width);
    const filled = '█'.repeat(filledBlocks);
    const empty = ' '.repeat(width - filledBlocks);
    return `[${filled}${empty}] ${percentage}% (${current}/${total} components)`;
}
/**
 * Конвертация path -> JSON Pointer (RFC 6901)
 */
function pathToJsonPointer(path) {
    if (!path)
        return '';
    // Разбиваем путь на сегменты
    const segments = [];
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
    const escaped = segments.map(seg => seg.replace(/~/g, '~0').replace(/\//g, '~1'));
    return '/' + escaped.join('/');
}
function parseIssue(text) {
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
    let component = null;
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
function groupIssuesByComponent(issues) {
    const grouped = new Map();
    for (const issue of issues) {
        const parsed = parseIssue(issue);
        if (!parsed)
            continue; // пропускаем дочерние warnings
        const key = parsed.component || 'Other';
        if (!grouped.has(key)) {
            grouped.set(key, []);
        }
        grouped.get(key).push(parsed);
    }
    return grouped;
}
/**
 * Форматирование box для компонента
 */
function formatComponentBox(componentName, count, additionalInfo) {
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
 * Построение карты позиций (путь -> номер строки) с обработкой ошибок
 */
function buildPositionMap(content, contract) {
    try {
        // Edge case: пустой файл
        if (!content || content.trim().length === 0) {
            console.warn('⚠️  Line resolution: empty file');
            return null;
        }
        // Edge case: single-line JSON
        const lines = content.split('\n');
        if (lines.length === 1) {
            console.warn('⚠️  Line resolution: single-line JSON, using #L1 for all paths');
            return null;
        }
        const positionMap = new Map();
        // Используем jsonc-parser для получения позиций
        const tree = jsoncParser.parseTree(content);
        if (!tree) {
            console.warn('⚠️  Line resolution: failed to parse JSON tree');
            return null;
        }
        // Вспомогательная функция: конвертация offset в номер строки
        function offsetToLine(offset) {
            if (offset < 0)
                return 1;
            let line = 1;
            for (let i = 0; i < offset && i < content.length; i++) {
                if (content[i] === '\n')
                    line++;
            }
            return line;
        }
        // Рекурсивный обход дерева
        function traverse(node, path = '') {
            if (!node || node.offset === undefined)
                return;
            // Вычисляем номер строки из offset
            const lineNumber = offsetToLine(node.offset);
            // Сохраняем позицию
            if (path) {
                positionMap.set(path, lineNumber);
            }
            // Обход потомков
            if (node.type === 'object' && node.children) {
                for (const child of node.children) {
                    if (child.type === 'property' && child.children) {
                        const key = child.children[0]?.value;
                        const valueNode = child.children[1];
                        const childPath = path ? `${path}.${key}` : key;
                        if (valueNode) {
                            traverse(valueNode, childPath);
                        }
                    }
                }
            }
            else if (node.type === 'array' && node.children) {
                node.children.forEach((child, index) => {
                    const childPath = `${path}[${index}]`;
                    traverse(child, childPath);
                });
            }
        }
        traverse(tree);
        console.log(`   ℹ️  Built position map: ${positionMap.size} paths indexed`);
        return positionMap;
    }
    catch (error) {
        // Graceful degradation: продолжаем без карты позиций
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.warn(`⚠️  Line resolution unavailable: ${errorMessage}`);
        return null;
    }
}
/**
 * Нормализация пути из валидатора к единому формату
 * Преобразует root['content'][0]['props']['text'] -> root.content[0].props.text
 */
function normalizePath(path) {
    if (!path)
        return '';
    // Заменяем ['key'] на .key
    let normalized = path.replace(/\['([^']+)'\]/g, '.$1');
    // Убираем начальную точку, если она есть
    if (normalized.startsWith('.')) {
        normalized = normalized.substring(1);
    }
    return normalized;
}
/**
 * Парсит путь в сегменты для fallback поиска
 * "elements[0].type" -> ["elements", "elements[0]", "elements[0].type"]
 */
function getPathHierarchy(path) {
    if (!path)
        return [];
    const hierarchy = [];
    let current = '';
    let inBracket = false;
    for (let i = 0; i < path.length; i++) {
        const char = path[i];
        if (char === '[') {
            inBracket = true;
            current += char;
            continue;
        }
        if (char === ']') {
            inBracket = false;
            current += char;
            hierarchy.push(current);
            continue;
        }
        if (char === '.' && !inBracket) {
            if (current) {
                hierarchy.push(current);
            }
            current += char;
            continue;
        }
        current += char;
    }
    if (current && !hierarchy.includes(current)) {
        hierarchy.push(current);
    }
    return hierarchy;
}
/**
 * Получить номер строки для пути с обработкой ошибок и fallback
 */
function getLineNumber(path, positionMap) {
    // Fallback: если карта недоступна
    if (!positionMap)
        return 1;
    // Нормализуем путь для единообразия
    const normalizedPath = normalizePath(path);
    // Прямое совпадение с нормализованным путем
    if (positionMap.has(normalizedPath)) {
        return positionMap.get(normalizedPath);
    }
    // Прямое совпадение с оригинальным путем
    if (positionMap.has(path)) {
        return positionMap.get(path);
    }
    // Fallback: поиск по иерархии нормализованного пути
    const hierarchy = getPathHierarchy(normalizedPath);
    for (let i = hierarchy.length - 1; i >= 0; i--) {
        const partialPath = hierarchy[i];
        if (positionMap.has(partialPath)) {
            return positionMap.get(partialPath);
        }
    }
    // Финальный fallback
    return 1;
}
/**
 * Форматирование issue с Path, JSON Pointer и Link
 */
function formatIssue(issue, index, icon, filePath, positionMap = null) {
    const lineNumber = getLineNumber(issue.path, positionMap);
    console.log('');
    console.log(`  ${icon} [${index}] ${issue.message}`);
    console.log('');
    console.log(`      Path: ${issue.path}`);
    console.log(`      JSON Pointer: ${pathToJsonPointer(issue.path)}`);
    console.log(`      Link: file://${filePath}#L${lineNumber}`);
    console.log('');
}
// ============================================================================
// ОСНОВНОЙ ФОРМАТТЕР ВЫВОДА
// ============================================================================
function formatOutput(filePath, report, parseError, stats, positionMap = null) {
    const fileName = (0, path_1.basename)(filePath);
    const relativePath = (0, path_1.relative)(PROJECT_ROOT, filePath);
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
    }
    else {
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
                formatIssue(issue, issueIndex++, '❌', filePath, positionMap);
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
                formatIssue(issue, issueIndex++, '⚠️ ', filePath, positionMap);
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
    }
    else {
        console.log('❌ Контракт требует исправления');
    }
    console.log('━'.repeat(80));
    console.log('');
}
// ============================================================================
// ОСНОВНАЯ ФУНКЦИЯ ВАЛИДАЦИИ
// ============================================================================
async function validateFile(filePath) {
    const startTime = Date.now();
    try {
        // Динамический импорт модулей
        const { IncrementalValidator } = await import(`file://${MCP_ROOT}/dist/validators/incremental-validator.js`);
        const { SDUISchemaIndex } = await import(`file://${MCP_ROOT}/dist/schema-utils/schema-index.js`);
        const fileName = (0, path_1.basename)(filePath);
        // PROCESSING HEADER
        console.log('━'.repeat(80));
        console.log(`🔄 PROCESSING: ${fileName}`);
        console.log('━'.repeat(80));
        console.log('');
        // Progress: Reading
        console.log('📂 Reading file...');
        const content = (0, fs_1.readFileSync)(filePath, 'utf-8');
        const fileSizeKB = (Buffer.byteLength(content, 'utf-8') / 1024).toFixed(2);
        console.log(`   Size: ${fileSizeKB} KB`);
        console.log('');
        // Progress: Parsing
        console.log('🔍 Parsing JSON...');
        let contract;
        try {
            contract = JSON.parse(content);
            console.log('   ✅ Parsed successfully');
        }
        catch (parseError) {
            console.log('   ❌ Parse failed');
            console.log('');
            formatOutput(filePath, null, parseError.message);
            process.exit(1);
        }
        console.log('');
        // Progress: Initializing
        console.log('⚙️  Initializing validator...');
        const schemaIndex = new SDUISchemaIndex(PROJECT_ROOT);
        console.log(`   • Indexed ${schemaIndex.getComponentCount?.()} components`);
        console.log('   ✅ Validator ready');
        console.log('');
        // Progress: Building position map for accurate line numbers
        console.log('🗺️  Building position map...');
        let positionMap = null;
        try {
            positionMap = buildPositionMap(content, contract);
            if (positionMap) {
                console.log('   ✅ Position map ready');
            }
            else {
                console.log('   ⚠️  Position map unavailable, using fallback (#L1)');
            }
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : String(error);
            console.warn(`   ⚠️  Position map build failed: ${errorMessage}`);
            console.log('   ℹ️  Continuing with fallback (#L1)');
            positionMap = null;
        }
        console.log('');
        // Validation
        const validator = new IncrementalValidator(PROJECT_ROOT, schemaIndex);
        const report = validator.validateIncremental(contract);
        const endTime = Date.now();
        const duration = (endTime - startTime) / 1000;
        // Output
        formatOutput(filePath, report, undefined, {
            duration,
            totalComponents: report.versions?.totalComponents || 0,
        }, positionMap);
        // Exit code
        process.exit(report.valid ? 0 : 1);
    }
    catch (error) {
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
