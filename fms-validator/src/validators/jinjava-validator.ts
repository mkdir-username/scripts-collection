/**
 * Jinjava Template Validator
 * Validates [JJ_*] files for Jinjava syntax errors
 *
 * Jinjava is Java-based Jinja implementation used in FMS.
 * Key differences from Jinja2:
 * - Some filters/functions may differ
 * - Error messages format differs
 * - Strict mode behavior differs
 */

import { readFileSync, existsSync } from 'fs';
import { dirname, join } from 'path';
import type { ValidationError, SourceLocation } from '../types/report.js';

interface JinjavaResult {
  errors: ValidationError[];
  includes: string[];
  macros: string[];
  variables: string[];
}

// Jinjava syntax patterns
const PATTERNS = {
  // Expression: {{ variable }}
  expression: /\{\{([^}]*)\}\}/g,
  // Statement: {% tag %}
  statement: /\{%([^%]*?)%\}/g,
  // Comment: {# comment #}
  comment: /\{#([^#]*?)#\}/g,
  // Include statement
  include: /\{%\s*include\s+['"]([^'"]+)['"]\s*%\}/g,
  // Macro definition
  macro: /\{%\s*macro\s+(\w+)\s*\([^)]*\)\s*%\}/g,
  // Block tags that need closing
  blockTags: /\{%\s*(if|for|macro|block|filter|set|call)\s/g,
  endBlockTags: /\{%\s*end(if|for|macro|block|filter|set|call)\s*%\}/g,
};

export function validateJinjava(
  templatePath: string,
  basePath?: string
): JinjavaResult {
  const errors: ValidationError[] = [];
  const includes: string[] = [];
  const macros: string[] = [];
  const variables: string[] = [];

  let errorCounter = 300; // J3xx for Jinjava errors

  if (!existsSync(templatePath)) {
    errors.push({
      id: `J${++errorCounter}`,
      severity: 'critical',
      category: 'SCHEMA_REF',
      blocking: true,
      location: createLocation(templatePath, 0, ''),
      message: `Template file not found: ${templatePath}`,
      fix: {
        action: 'Check file path',
        refs: [],
      },
      aiHint: `File ${templatePath} does not exist`,
    });
    return { errors, includes, macros, variables };
  }

  const content = readFileSync(templatePath, 'utf-8');
  const lines = content.split('\n');

  // 1. Check balanced braces
  const balanceErrors = checkBalancedBraces(content, templatePath, () => `J${++errorCounter}`);
  errors.push(...balanceErrors);

  // 2. Check block tag balance (if/endif, for/endfor, etc.)
  const blockErrors = checkBlockBalance(content, templatePath, () => `J${++errorCounter}`);
  errors.push(...blockErrors);

  // 3. Collect includes
  let match;
  while ((match = PATTERNS.include.exec(content)) !== null) {
    const includePath = match[1];
    includes.push(includePath);

    // Check if included file exists
    const resolvedPath = basePath
      ? join(basePath, includePath)
      : join(dirname(templatePath), includePath);

    if (!existsSync(resolvedPath)) {
      const lineNum = findLineNumber(content, match.index);
      errors.push({
        id: `J${++errorCounter}`,
        severity: 'error',
        category: 'SCHEMA_REF',
        blocking: true,
        location: createLocation(templatePath, lineNum, lines[lineNum - 1] || ''),
        message: `Included file not found: ${includePath}`,
        expected: { type: 'existing file' },
        actual: { value: resolvedPath },
        fix: {
          action: `Create file ${includePath} or fix the include path`,
          refs: [dirname(templatePath)],
        },
        aiHint: `Include "${includePath}" references non-existent file. Check path relative to template.`,
      });
    }
  }

  // 4. Collect macros
  while ((match = PATTERNS.macro.exec(content)) !== null) {
    macros.push(match[1]);
  }

  // 5. Collect variables from expressions
  while ((match = PATTERNS.expression.exec(content)) !== null) {
    const expr = match[1].trim();
    // Extract variable name (first identifier)
    const varMatch = expr.match(/^(\w+)/);
    if (varMatch) {
      variables.push(varMatch[1]);
    }
  }

  // 6. Check for common Jinjava mistakes
  const syntaxErrors = checkCommonMistakes(content, templatePath, () => `J${++errorCounter}`);
  errors.push(...syntaxErrors);

  return { errors, includes, macros, variables };
}

function checkBalancedBraces(
  content: string,
  filePath: string,
  nextId: () => string
): ValidationError[] {
  const errors: ValidationError[] = [];
  const lines = content.split('\n');

  // Check {{ }} balance
  let openExpr = 0;
  let openStmt = 0;
  let openComment = 0;

  for (let i = 0; i < content.length; i++) {
    const char = content[i];
    const next = content[i + 1];

    if (char === '{' && next === '{') {
      openExpr++;
      i++;
    } else if (char === '}' && next === '}') {
      openExpr--;
      i++;
      if (openExpr < 0) {
        const lineNum = findLineNumber(content, i);
        errors.push({
          id: nextId(),
          severity: 'critical',
          category: 'EL_SYNTAX',
          blocking: true,
          location: createLocation(filePath, lineNum, lines[lineNum - 1] || ''),
          message: 'Unmatched closing }}',
          fix: {
            action: 'Remove extra }} or add missing {{',
            refs: [],
          },
          aiHint: 'Unbalanced expression braces. Check for extra }} at this line.',
        });
        openExpr = 0;
      }
    } else if (char === '{' && next === '%') {
      openStmt++;
      i++;
    } else if (char === '%' && next === '}') {
      openStmt--;
      i++;
      if (openStmt < 0) {
        const lineNum = findLineNumber(content, i);
        errors.push({
          id: nextId(),
          severity: 'critical',
          category: 'EL_SYNTAX',
          blocking: true,
          location: createLocation(filePath, lineNum, lines[lineNum - 1] || ''),
          message: 'Unmatched closing %}',
          fix: {
            action: 'Remove extra %} or add missing {%',
            refs: [],
          },
          aiHint: 'Unbalanced statement braces. Check for extra %} at this line.',
        });
        openStmt = 0;
      }
    } else if (char === '{' && next === '#') {
      openComment++;
      i++;
    } else if (char === '#' && next === '}') {
      openComment--;
      i++;
    }
  }

  if (openExpr > 0) {
    errors.push({
      id: nextId(),
      severity: 'critical',
      category: 'EL_SYNTAX',
      blocking: true,
      location: createLocation(filePath, lines.length, ''),
      message: `Unclosed expression: ${openExpr} {{ without matching }}`,
      fix: {
        action: 'Add missing }} to close expression',
        refs: [],
      },
      aiHint: 'Template has unclosed {{ expression. Search for {{ and ensure each has }}.',
    });
  }

  if (openStmt > 0) {
    errors.push({
      id: nextId(),
      severity: 'critical',
      category: 'EL_SYNTAX',
      blocking: true,
      location: createLocation(filePath, lines.length, ''),
      message: `Unclosed statement: ${openStmt} {% without matching %}`,
      fix: {
        action: 'Add missing %} to close statement',
        refs: [],
      },
      aiHint: 'Template has unclosed {% statement. Search for {% and ensure each has %}.',
    });
  }

  return errors;
}

function checkBlockBalance(
  content: string,
  filePath: string,
  nextId: () => string
): ValidationError[] {
  const errors: ValidationError[] = [];
  const lines = content.split('\n');

  // Track open blocks
  const stack: Array<{ tag: string; line: number }> = [];

  // Find all block openings
  const blockPattern = /\{%[-+]?\s*(if|for|macro|block|filter|call)\s/g;
  const endPattern = /\{%[-+]?\s*end(if|for|macro|block|filter|call)\s*[-+]?%\}/g;

  let match;
  while ((match = blockPattern.exec(content)) !== null) {
    const lineNum = findLineNumber(content, match.index);
    stack.push({ tag: match[1], line: lineNum });
  }

  while ((match = endPattern.exec(content)) !== null) {
    const endTag = match[1];
    const lineNum = findLineNumber(content, match.index);

    if (stack.length === 0) {
      errors.push({
        id: nextId(),
        severity: 'error',
        category: 'EL_SYNTAX',
        blocking: true,
        location: createLocation(filePath, lineNum, lines[lineNum - 1] || ''),
        message: `Unexpected {% end${endTag} %} without matching {% ${endTag} %}`,
        fix: {
          action: `Remove orphan {% end${endTag} %} or add opening {% ${endTag} %}`,
          refs: [],
        },
        aiHint: `Found end${endTag} without opening ${endTag}. Check block structure.`,
      });
      continue;
    }

    const last = stack.pop()!;
    if (last.tag !== endTag) {
      errors.push({
        id: nextId(),
        severity: 'error',
        category: 'EL_SYNTAX',
        blocking: true,
        location: createLocation(filePath, lineNum, lines[lineNum - 1] || ''),
        message: `Mismatched block: expected {% end${last.tag} %} but found {% end${endTag} %}`,
        expected: { type: `end${last.tag}` },
        actual: { value: `end${endTag}` },
        fix: {
          action: `Change to {% end${last.tag} %} or fix block structure`,
          refs: [],
        },
        aiHint: `Block mismatch: opened "${last.tag}" at line ${last.line}, closed with "end${endTag}".`,
      });
    }
  }

  // Check for unclosed blocks
  for (const unclosed of stack) {
    errors.push({
      id: nextId(),
      severity: 'error',
      category: 'EL_SYNTAX',
      blocking: true,
      location: createLocation(filePath, unclosed.line, lines[unclosed.line - 1] || ''),
      message: `Unclosed {% ${unclosed.tag} %} block`,
      fix: {
        action: `Add {% end${unclosed.tag} %} to close the block`,
        refs: [],
      },
      aiHint: `Block "${unclosed.tag}" opened at line ${unclosed.line} is never closed. Add {% end${unclosed.tag} %}.`,
    });
  }

  return errors;
}

function checkCommonMistakes(
  content: string,
  filePath: string,
  nextId: () => string
): ValidationError[] {
  const errors: ValidationError[] = [];
  const lines = content.split('\n');

  // Check for Jinja2 syntax that doesn't work in Jinjava
  const jinja2Only = [
    { pattern: /\{%\s*extends\s/g, message: '{% extends %} not supported in Jinjava' },
    { pattern: /\{%\s*import\s+['"][^'"]+['"]\s+as\s/g, message: 'import...as syntax differs in Jinjava' },
  ];

  for (const check of jinja2Only) {
    let match;
    while ((match = check.pattern.exec(content)) !== null) {
      const lineNum = findLineNumber(content, match.index);
      errors.push({
        id: nextId(),
        severity: 'warning',
        category: 'EL_SYNTAX',
        blocking: false,
        location: createLocation(filePath, lineNum, lines[lineNum - 1] || ''),
        message: check.message,
        fix: {
          action: 'Check Jinjava documentation for equivalent syntax',
          refs: ['/Users/username/Documents/jinjava-jinjava-2.8.2/README.md'],
        },
        aiHint: `Jinja2-specific syntax may not work in Jinjava. ${check.message}`,
      });
    }
  }

  // Check for mixing Jinjava and Expression Language
  const mixedPattern = /\$\{\{|\{\{\$/g;
  let match;
  while ((match = mixedPattern.exec(content)) !== null) {
    const lineNum = findLineNumber(content, match.index);
    errors.push({
      id: nextId(),
      severity: 'critical',
      category: 'EL_SYNTAX',
      blocking: true,
      location: createLocation(filePath, lineNum, lines[lineNum - 1] || ''),
      message: 'Mixed Jinjava {{ and Expression Language ${ syntax',
      fix: {
        action: 'Use {{ }} for Jinjava (compile-time) OR ${ } for EL (runtime), never both together',
        refs: [],
      },
      aiHint: 'Never mix Jinjava {{ }} with EL ${ }. Jinjava runs at compile time, EL at runtime.',
    });
  }

  return errors;
}

function findLineNumber(content: string, index: number): number {
  return content.slice(0, index).split('\n').length;
}

function createLocation(filePath: string, line: number, lineContent: string): SourceLocation {
  return {
    jsonPath: `${filePath}:${line}`,
    jsonPointer: `/line/${line}`,
    snippet: lineContent.trim().slice(0, 100),
    lineHint: line,
  };
}

/**
 * Validate all Jinjava templates in a directory
 */
export function validateJinjavaDirectory(
  dirPath: string
): JinjavaResult {
  // This would scan for [JJ_*] files and validate each
  // Implementation left for expansion
  return { errors: [], includes: [], macros: [], variables: [] };
}
