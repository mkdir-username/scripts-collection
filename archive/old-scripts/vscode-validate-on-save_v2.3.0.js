#!/usr/bin/env node
"use strict";
/**
 * VSCode On-Save Validator v2.3.0
 *
 * Автоматическая валидация SDUI контрактов при сохранении в VSCode
 * + Поддержка .j2.java файлов с Jinja2/Java шаблонами
 * + Резолвинг модулей через // [...](file://path) импорты
 * + Точное таргетирование на поле ошибки (type, required fields и др.)
 * + Кликабельные ссылки в формате "-> path:line:col"
 * + Обратная совместимость с .json файлами
 *
 * Usage:
 *   node vscode-validate-on-save_v2.3.0.js path/to/contract.json
 *   node vscode-validate-on-save_v2.3.0.js path/to/contract.j2.java
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
const PROJECT_ROOT = process.env.PROJECT_ROOT || '/Users/username/Documents/FMS_GIT';
// Путь к MCP серверу с валидатором
const MCP_ROOT = '/Users/username/Scripts/alfa-sdui-mcp';
// Парсинг CLI аргументов
const args = process.argv.slice(2);
let filePath;
const flags = {
    jinjaAware: false,
    verbose: false
};
for (const arg of args) {
    if (arg.startsWith('--')) {
        // Обработка флагов
        if (arg === '--jinja-aware') {
            flags.jinjaAware = true;
        }
        else if (arg === '--verbose' || arg === '-v') {
            flags.verbose = true;
        }
    }
    else {
        // Первый аргумент без -- это путь к файлу
        if (!filePath) {
            filePath = arg;
        }
    }
}
if (!filePath) {
    console.error('❌ ERROR: Путь к файлу не указан');
    console.error('Usage: node vscode-validate-on-save_v2.3.0.js [options] <file>');
    console.error('');
    console.error('Options:');
    console.error('  --jinja-aware    Force Jinja2/Java parsing mode');
    console.error('  --verbose, -v    Verbose output');
    process.exit(1);
}
/**
 * Определяет формат файла по расширению
 */
function detectFileFormat(filePath) {
    const ext = (0, path_1.extname)(filePath).toLowerCase();
    if (ext === '.java' && filePath.includes('.j2.java')) {
        return 'j2.java';
    }
    if (filePath.endsWith('.jinja.java')) {
        return 'j2.java';
    }
    return 'json';
}
/**
 * Парсит Jinja2/Java шаблон (упрощенная встроенная версия)
 */
async function parseJinjaTemplate(filePath) {
    const startTime = Date.now();
    try {
        // Динамический импорт Jinja парсера
        const { JinjaParser } = await Promise.resolve().then(() => __importStar(require(`/Users/username/Scripts/validators/v3.0.0/jinja_parser_v1.0.0.js`)));
        const parser = new JinjaParser({
            allowRecursiveImports: false,
            maxImportDepth: 10,
            basePath: require('path').dirname(filePath),
            buildSourceMap: true
        });
        return parser.parse(filePath);
    }
    catch (error) {
        // Fallback на встроенную простую реализацию
        return parseJinjaTemplateFallback(filePath, startTime);
    }
}
/**
 * Fallback парсер Jinja (упрощенный)
 */
function parseJinjaTemplateFallback(filePath, startTime) {
    const content = (0, fs_1.readFileSync)(filePath, 'utf-8');
    const lines = content.split('\n');
    const processedLines = [];
    const errors = [];
    const imports = [];
    const sourceMap = [];
    let totalSizeBytes = Buffer.byteLength(content);
    let importCount = 0;
    let variableCount = 0;
    let controlCount = 0;
    const basePath = require('path').dirname(filePath);
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        const lineNumber = i + 1;
        let processedLine = line;
        // Обработка комментариев с импортами: // [Описание](file://path)
        const importMatch = line.match(/^\s*\/\/\s*\[(.*?)\]\((file:\/\/.*?)\)\s*$/);
        if (importMatch) {
            const description = importMatch[1];
            const importPath = importMatch[2].replace('file://', '');
            const column = line.indexOf('//') + 1;
            sourceMap.push({
                jinjaLine: lineNumber,
                jinjaColumn: column,
                jsonPointer: '',
                sourceFile: filePath,
                tokenType: 'import'
            });
            try {
                const resolvedPath = require('path').isAbsolute(importPath)
                    ? importPath
                    : require('path').resolve(basePath, importPath);
                if (require('fs').existsSync(resolvedPath)) {
                    const importedContent = (0, fs_1.readFileSync)(resolvedPath, 'utf-8');
                    totalSizeBytes += Buffer.byteLength(importedContent);
                    let importedJson;
                    try {
                        importedJson = JSON.parse(importedContent);
                    }
                    catch (e) {
                        errors.push({
                            type: 'parse_error',
                            message: `Ошибка парсинга импортированного файла: ${resolvedPath}`,
                            line: lineNumber,
                            column,
                            filePath: resolvedPath
                        });
                        continue;
                    }
                    imports.push({
                        path: importMatch[2],
                        resolvedPath,
                        content: importedJson,
                        line: lineNumber,
                        column,
                        description,
                        isRecursive: false
                    });
                    importCount++;
                    // Встраивание импортированного содержимого
                    const importedJsonStr = JSON.stringify(importedJson, null, 2);
                    const indentMatch = line.match(/^(\s*)/);
                    const indent = indentMatch ? indentMatch[1] : '';
                    const indentedJson = importedJsonStr
                        .split('\n')
                        .map((l, idx) => (idx === 0 ? indent + l : indent + l))
                        .join('\n');
                    processedLines.push(indentedJson + (i < lines.length - 1 ? ',' : ''));
                }
                else {
                    errors.push({
                        type: 'file_not_found',
                        message: `Импортируемый файл не найден: ${resolvedPath}`,
                        line: lineNumber,
                        column,
                        filePath
                    });
                }
            }
            catch (e) {
                errors.push({
                    type: 'parse_error',
                    message: `Ошибка обработки импорта: ${e}`,
                    line: lineNumber,
                    column,
                    filePath
                });
            }
            continue;
        }
        // Обработка Jinja переменных: {{ variable }}
        const variableRegex = /\{\{\s*([^}]+?)\s*\}\}/g;
        let match;
        while ((match = variableRegex.exec(line)) !== null) {
            const variableName = match[1].trim();
            const column = match.index + 1;
            sourceMap.push({
                jinjaLine: lineNumber,
                jinjaColumn: column,
                jsonPointer: '',
                sourceFile: filePath,
                tokenType: 'variable'
            });
            variableCount++;
            // Замена переменной на значение по умолчанию
            const defaultValue = inferDefaultValue(variableName);
            processedLine = processedLine.replace(match[0], JSON.stringify(defaultValue));
        }
        // Обработка управляющих конструкций: {% ... %}
        const controlMatch = processedLine.match(/\{%\s*(\w+)\s*(.*?)\s*%\}/);
        if (controlMatch) {
            const column = processedLine.indexOf('{%') + 1;
            sourceMap.push({
                jinjaLine: lineNumber,
                jinjaColumn: column,
                jsonPointer: '',
                sourceFile: filePath,
                tokenType: 'control'
            });
            controlCount++;
            processedLine = processedLine.replace(/\{%.*?%\}/g, '');
        }
        // Удаление обычных комментариев (не импортов)
        processedLine = processedLine.replace(/\/\/(?!\s*\[).*$/, '').trim();
        if (processedLine) {
            processedLines.push(processedLine);
        }
    }
    // Объединение строк и парсинг JSON
    const jsonText = processedLines.join('\n');
    let extractedJson;
    try {
        extractedJson = JSON.parse(jsonText);
    }
    catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        const lineMatch = errorMessage.match(/at position (\d+)/);
        const position = lineMatch ? parseInt(lineMatch[1], 10) : 0;
        const linesUpToError = jsonText.substring(0, position).split('\n');
        const errorLine = linesUpToError.length;
        const errorColumn = linesUpToError[linesUpToError.length - 1].length + 1;
        errors.push({
            type: 'parse_error',
            message: `Ошибка парсинга JSON: ${errorMessage}`,
            line: errorLine,
            column: errorColumn,
            filePath
        });
        extractedJson = null;
    }
    return {
        extractedJson,
        imports,
        sourceMap,
        errors,
        stats: {
            parseTimeMs: Date.now() - startTime,
            importCount,
            variableCount,
            controlCount,
            totalSizeBytes
        }
    };
}
/**
 * Выводит значение по умолчанию на основе имени переменной
 */
function inferDefaultValue(variableName) {
    const lowerName = variableName.toLowerCase();
    if (lowerName.startsWith('is') ||
        lowerName.startsWith('has') ||
        lowerName.includes('enabled') ||
        lowerName.includes('show')) {
        return false;
    }
    if (lowerName.includes('count') ||
        lowerName.includes('size') ||
        lowerName.includes('length') ||
        lowerName.includes('index')) {
        return 0;
    }
    if (lowerName.includes('list') ||
        lowerName.includes('items') ||
        lowerName.includes('array')) {
        return [];
    }
    if (lowerName.includes('data') ||
        lowerName.includes('config') ||
        lowerName.includes('options')) {
        return {};
    }
    if (lowerName.includes('null') || lowerName === 'none') {
        return null;
    }
    return '';
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
function buildPositionMap(jsonText) {
    const byPointer = new Map();
    const byPath = new Map();
    let line = 1;
    let column = 1;
    let offset = 0;
    // Стек для отслеживания текущего пути
    const pathStack = [];
    let inString = false;
    let escaped = false;
    let currentKey = '';
    let collectingKey = false;
    let arrayIndex = 0;
    let arrayStack = [];
    const savePosition = (path) => {
        if (path.length === 0)
            return;
        const pointer = '/' +
            path.map((p) => String(p).replace(/~/g, '~0').replace(/\//g, '~1')).join('/');
        const propertyPath = path.reduce((acc, segment) => {
            if (typeof segment === 'number') {
                return `${acc}[${segment}]`;
            }
            return acc ? `${acc}.${segment}` : String(segment);
        }, '');
        const pos = { line, column, offset };
        byPointer.set(pointer, pos);
        byPath.set(propertyPath, pos);
    };
    for (let i = 0; i < jsonText.length; i++) {
        const char = jsonText[i];
        const prevChar = jsonText[i - 1] || '';
        const nextChar = jsonText[i + 1] || '';
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
            }
            else {
                inString = true;
                // Начинаем собирать ключ, если предыдущий символ { или ,
                if (prevChar === '{' ||
                    prevChar === ',' ||
                    prevChar === '\n' ||
                    prevChar === ' ') {
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
                    arrayIndex = arrayStack.pop();
                }
            }
            // Запятая в массиве
            if (char === ',') {
                const parent = pathStack[pathStack.length - 1];
                // Проверяем, находимся ли в массиве
                if (typeof parent === 'number' ||
                    (pathStack.length > 0 &&
                        jsonText.lastIndexOf('[', i) > jsonText.lastIndexOf('{', i))) {
                    if (pathStack.length > 0 &&
                        typeof pathStack[pathStack.length - 1] === 'number') {
                        pathStack.pop();
                    }
                    arrayIndex++;
                    pathStack.push(arrayIndex);
                    savePosition(pathStack);
                }
                else {
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
                while (j < jsonText.length &&
                    (jsonText[j] === ' ' || jsonText[j] === '\n')) {
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
        }
        else {
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
function findLineNumber(positionMap, path, pointer) {
    // 1. Прямой поиск по JSON Pointer (самый точный)
    if (positionMap.byPointer.has(pointer)) {
        return positionMap.byPointer.get(pointer).line;
    }
    // 2. Прямой поиск по property path
    if (positionMap.byPath.has(path)) {
        return positionMap.byPath.get(path).line;
    }
    // 3. Ищем ближайший родительский путь
    const segments = path.split(/[.\[\]]/).filter(Boolean);
    for (let i = segments.length - 1; i >= 0; i--) {
        const parentPath = segments.slice(0, i).reduce((acc, seg) => {
            if (!acc)
                return seg;
            // Проверяем, является ли сегмент числом (индекс массива)
            if (/^\d+$/.test(seg)) {
                return `${acc}[${seg}]`;
            }
            return `${acc}.${seg}`;
        }, '');
        if (positionMap.byPath.has(parentPath)) {
            return positionMap.byPath.get(parentPath).line;
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
    const escaped = segments.map((seg) => seg.replace(/~/g, '~0').replace(/\//g, '~1'));
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
 * Определяет точное поле ошибки из сообщения
 */
function extractErrorField(message) {
    // "Component XXX not found" -> поле type
    if (message.includes('Component') && message.includes('not found')) {
        return 'type';
    }
    // "Missing required field 'xxx'"
    const requiredMatch = message.match(/Missing required field ['"](\w+)['"]/i);
    if (requiredMatch) {
        return requiredMatch[1];
    }
    // "Invalid value for 'xxx'"
    const invalidMatch = message.match(/Invalid value for ['"](\w+)['"]/i);
    if (invalidMatch) {
        return invalidMatch[1];
    }
    // "Unexpected field 'xxx'"
    const unexpectedMatch = message.match(/Unexpected field(?:s)? (?:found )?['"]?(\w+)['"]?/i);
    if (unexpectedMatch) {
        return unexpectedMatch[1];
    }
    return null;
}
/**
 * Форматирование issue с Path, JSON Pointer и Link (с реальным номером строки)
 */
function formatIssue(issue, index, icon, filePath, positionMap) {
    const pointer = pathToJsonPointer(issue.path);
    // Пытаемся найти точное поле ошибки
    const errorField = extractErrorField(issue.message);
    let targetPath = issue.path;
    let targetPointer = pointer;
    if (errorField) {
        targetPath = issue.path ? `${issue.path}.${errorField}` : errorField;
        targetPointer = pointer ? `${pointer}/${errorField}` : `/${errorField}`;
    }
    const lineNumber = findLineNumber(positionMap, targetPath, targetPointer);
    // Определяем исходный файл (если это модульная ошибка)
    const displayFilePath = issue.sourceFile || filePath;
    console.log('');
    console.log(`  ${icon} [${index}] ${issue.message}`);
    console.log('');
    console.log(`      Path: ${issue.path}`);
    console.log(`      JSON Pointer: ${pointer}`);
    if (issue.sourceFile) {
        console.log(`      Module: ${(0, path_1.basename)(issue.sourceFile)}`);
    }
    console.log(`      -> ${displayFilePath}:${lineNumber}:1`);
    console.log('');
}
// ============================================================================
// ОСНОВНОЙ ФОРМАТТЕР ВЫВОДА
// ============================================================================
function formatOutput(filePath, report, parseError, jinjaParseResult, stats, positionMap) {
    const fileName = (0, path_1.basename)(filePath);
    const relativePath = (0, path_1.relative)(PROJECT_ROOT, filePath);
    const fileFormat = detectFileFormat(filePath);
    // PROCESSING HEADER
    console.log('━'.repeat(80));
    console.log(`🔄 PROCESSING: ${fileName}${fileFormat === 'j2.java' ? ' [Jinja2/Java Template]' : ''}`);
    console.log('━'.repeat(80));
    console.log('');
    // JINJA PARSE STATS
    if (jinjaParseResult) {
        console.log('🔧 Jinja2 Template Processing...');
        console.log(`   • Imports resolved: ${jinjaParseResult.stats.importCount}`);
        console.log(`   • Variables replaced: ${jinjaParseResult.stats.variableCount}`);
        console.log(`   • Control structures: ${jinjaParseResult.stats.controlCount}`);
        console.log(`   • Total size: ${(jinjaParseResult.stats.totalSizeBytes / 1024).toFixed(2)} KB`);
        console.log(`   • Parse time: ${jinjaParseResult.stats.parseTimeMs.toFixed(2)}ms`);
        // Показываем импортированные модули
        if (jinjaParseResult.imports.length > 0) {
            console.log('   • Modules:');
            for (const imp of jinjaParseResult.imports) {
                console.log(`     - ${imp.description} (${(0, path_1.basename)(imp.resolvedPath)})`);
            }
        }
        // Показываем ошибки парсинга Jinja
        if (jinjaParseResult.errors.length > 0) {
            console.log('');
            console.log('   ⚠️  Jinja Parse Errors:');
            for (const err of jinjaParseResult.errors) {
                console.log(`     - ${err.message} at line ${err.line}`);
            }
        }
        console.log('');
    }
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
    console.log(`📋 Format: ${fileFormat === 'j2.java' ? 'Jinja2/Java Template' : 'JSON'}`);
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
        const totalComps = `${report.versions.totalComponents} total (${Object.entries(report.versions.byVersion)
            .map(([v, c]) => `${v}: ${c}`)
            .join(', ')})`;
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
    const fileFormat = detectFileFormat(filePath);
    try {
        // Динамический импорт модулей (без file:// для CommonJS совместимости)
        const { IncrementalValidator } = await Promise.resolve(`${`${MCP_ROOT}/dist/validators/incremental-validator.js`}`).then(s => __importStar(require(s)));
        const { SDUISchemaIndex } = await Promise.resolve(`${`${MCP_ROOT}/dist/schema-utils/schema-index.js`}`).then(s => __importStar(require(s)));
        let contract;
        let jinjaParseResult;
        let content;
        // Определяем обработку файла по формату
        if (fileFormat === 'j2.java') {
            // Обработка Jinja2/Java шаблона
            console.log('🔧 Processing Jinja2/Java template...');
            jinjaParseResult = await parseJinjaTemplate(filePath);
            if (jinjaParseResult.errors.length > 0) {
                const criticalError = jinjaParseResult.errors.find((e) => e.type === 'parse_error');
                if (criticalError) {
                    formatOutput(filePath, null, criticalError.message, jinjaParseResult);
                    process.exit(1);
                }
            }
            contract = jinjaParseResult.extractedJson;
            content = JSON.stringify(contract, null, 2);
            console.log(`   ✅ Extracted JSON (${(Buffer.byteLength(content) / 1024).toFixed(2)} KB)`);
            console.log('');
        }
        else {
            // Обработка обычного JSON
            console.log('📂 Reading file...');
            content = (0, fs_1.readFileSync)(filePath, 'utf-8');
            const fileSizeKB = (Buffer.byteLength(content, 'utf-8') / 1024).toFixed(2);
            console.log(`   Size: ${fileSizeKB} KB`);
            console.log('');
            // Progress: Parsing
            console.log('🔍 Parsing JSON...');
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
        }
        // Progress: Building position map
        console.log('📍 Building position map...');
        const posMapStart = Date.now();
        const positionMap = buildPositionMap(content);
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
        formatOutput(filePath, report, undefined, jinjaParseResult, {
            duration,
            totalComponents: report.versions?.totalComponents || 0,
            positionMapBuildTime: posMapTime
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
