#!/usr/bin/env node
/**
 * Вспомогательный скрипт для точного поиска позиции JSON элемента
 * Использует тот же алгоритм, что и расширение JSON Path в VS Code
 */

const fs = require('fs');
const path = require('path');

function findJsonPathPosition(filePath, jsonPath) {
    try {
        const content = fs.readFileSync(filePath, 'utf-8');
        const lines = content.split('\n');
        const json = JSON.parse(content);

        // Навигация по JSON пути
        let current = json;
        const pathParts = parseJsonPath(jsonPath);

        for (const part of pathParts) {
            if (typeof part === 'number') {
                if (Array.isArray(current) && part < current.length) {
                    current = current[part];
                } else {
                    return { line: 1, column: 1 };
                }
            } else {
                if (current && typeof current === 'object' && part in current) {
                    current = current[part];
                } else {
                    return { line: 1, column: 1 };
                }
            }
        }

        // Сериализуем найденный объект для поиска
        const targetJson = JSON.stringify(current);

        // Ищем точное вхождение в тексте
        let position = findExactMatch(content, current, pathParts);

        if (position) {
            // Конвертируем позицию в номер строки
            const lineNumber = content.substring(0, position).split('\n').length;
            return { line: lineNumber, column: 1 };
        }

        return { line: 1, column: 1 };

    } catch (error) {
        console.error('Error:', error);
        return { line: 1, column: 1 };
    }
}

function parseJsonPath(path) {
    const parts = [];
    let current = '';
    let i = 0;

    while (i < path.length) {
        if (path[i] === '[') {
            if (current) {
                parts.push(current);
                current = '';
            }
            // Извлекаем индекс
            let j = i + 1;
            while (j < path.length && path[j] !== ']') {
                j++;
            }
            if (j < path.length) {
                parts.push(parseInt(path.substring(i + 1, j)));
                i = j;
            }
        } else if (path[i] === '.') {
            if (current) {
                parts.push(current);
                current = '';
            }
        } else {
            current += path[i];
        }
        i++;
    }

    if (current) {
        parts.push(current);
    }

    return parts;
}

function findExactMatch(content, target, pathParts) {
    // Для объектов с type ищем по type
    if (target && target.type) {
        const pattern = `"type"\\s*:\\s*"${target.type}"`;
        const regex = new RegExp(pattern, 'g');
        let match;
        const matches = [];

        while ((match = regex.exec(content)) !== null) {
            matches.push(match.index);
        }

        // Если несколько совпадений, используем контекст пути
        if (matches.length > 1) {
            // Ищем родительские ключи для уточнения
            const parentKeys = pathParts.filter(p => typeof p === 'string');

            for (const pos of matches) {
                let score = 0;
                const before = content.substring(Math.max(0, pos - 1000), pos);

                for (const key of parentKeys) {
                    if (before.includes(`"${key}"`)) {
                        score++;
                    }
                }

                if (score === parentKeys.length) {
                    return pos;
                }
            }
        }

        return matches[0] || null;
    }

    return null;
}

// Обработка аргументов командной строки
if (process.argv.length < 4) {
    console.log('Usage: node vscode_json_path_helper.js <file> <jsonpath>');
    process.exit(1);
}

const filePath = process.argv[2];
const jsonPath = process.argv[3];

const result = findJsonPathPosition(filePath, jsonPath);
console.log(result.line);