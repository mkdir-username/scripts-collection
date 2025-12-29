/**
 * Expression Language Validator
 * Validates ${data.x}, ${state.x}, ${computed.x} expressions
 */

import type {
  ValidationError,
  ExpressionValidation,
  SourceLocation,
} from '../types/report.js';

interface ExpressionResult {
  expressions: ExpressionValidation[];
  errors: ValidationError[];
}

// Regex to find EL expressions
const EL_REGEX = /\$\{([^}]+)\}/g;

export function validateExpressions(contract: unknown): ExpressionResult {
  const expressions: ExpressionValidation[] = [];
  const errors: ValidationError[] = [];
  let errorCounter = 100; // Start from E100 for EL errors

  // Collect all data/state/computed definitions
  const contractObj = contract as Record<string, unknown>;
  const dataFields = extractFields(contractObj['data']);
  const stateFields = extractFields(contractObj['state']);
  const computedFields = extractFields(contractObj['computed']);

  function walk(obj: unknown, path: string): void {
    if (obj === null || obj === undefined) return;

    if (typeof obj === 'string') {
      // Check for EL expressions
      const matches = [...obj.matchAll(EL_REGEX)];
      for (const match of matches) {
        const fullExpr = match[0]; // ${data.x}
        const innerExpr = match[1]; // data.x

        const exprValidation: ExpressionValidation = {
          expression: fullExpr,
          path,
          type: 'unknown',
          status: 'OK',
          issues: [],
        };

        // Determine type
        if (innerExpr.startsWith('data.')) {
          exprValidation.type = 'data';
          // Extract base field name (strip array access like [0], [i])
          const rawField = innerExpr.slice(5).split('.')[0];
          const field = rawField.replace(/\[.*\]$/, '');
          if (!dataFields.has(field)) {
            exprValidation.status = 'WARN';
            exprValidation.issues.push(`Undefined data field: ${field}`);
            errors.push(createUndefinedRefError(
              `E${++errorCounter}`,
              fullExpr,
              field,
              'data',
              path,
              dataFields
            ));
          }
        } else if (innerExpr.startsWith('state.')) {
          exprValidation.type = 'state';
          const rawField = innerExpr.slice(6).split('.')[0];
          const field = rawField.replace(/\[.*\]$/, '');
          if (!stateFields.has(field)) {
            exprValidation.status = 'WARN';
            exprValidation.issues.push(`Undefined state field: ${field}`);
            errors.push(createUndefinedRefError(
              `E${++errorCounter}`,
              fullExpr,
              field,
              'state',
              path,
              stateFields
            ));
          }
        } else if (innerExpr.startsWith('computed.')) {
          exprValidation.type = 'computed';
          const rawField = innerExpr.slice(9).split('.')[0];
          const field = rawField.replace(/\[.*\]$/, '');
          if (!computedFields.has(field)) {
            exprValidation.status = 'WARN';
            exprValidation.issues.push(`Undefined computed field: ${field}`);
            errors.push(createUndefinedRefError(
              `E${++errorCounter}`,
              fullExpr,
              field,
              'computed',
              path,
              computedFields
            ));
          }
        }

        expressions.push(exprValidation);
      }
      return;
    }

    if (Array.isArray(obj)) {
      obj.forEach((item, idx) => walk(item, `${path}[${idx}]`));
      return;
    }

    if (typeof obj === 'object') {
      const record = obj as Record<string, unknown>;

      // Check for computed functions with "if" that need boolean
      if (record['type'] === 'if' && record['if'] !== undefined) {
        const ifValue = record['if'];
        // If "if" is a string expression (not an object with type), it might be wrong
        if (typeof ifValue === 'string' && ifValue.startsWith('${')) {
          // This could be a non-boolean being used as boolean
          // We can't fully validate without runtime, but we can warn
          const match = ifValue.match(/\$\{(data|state|computed)\.(\w+)/);
          if (match) {
            const [, layer, field] = match;
            // Check if it's likely a number/string being used as boolean
            expressions.push({
              expression: ifValue,
              path: `${path}.if`,
              type: layer as 'data' | 'state' | 'computed',
              status: 'WARN',
              issues: ['Using variable directly in "if" - ensure it returns boolean'],
            });

            errors.push({
              id: `E${++errorCounter}`,
              severity: 'warning',
              category: 'EL_BOOLEAN_REQUIRED',
              blocking: false,
              location: createLocation(`${path}.if`, ifValue),
              message: `"if" condition may not be boolean: ${ifValue}`,
              expected: { type: 'boolean' },
              actual: { value: ifValue },
              fix: {
                action: 'Wrap in relational function (gt, lt, eq, etc.) if not boolean',
                suggestion: `{ "type": "gt", "left": "${ifValue}", "right": 0 }`,
                refs: ['SDUI/functions/logical/'],
              },
              aiHint: `If ${field} is not boolean, use: {"type":"gt","left":"${ifValue}","right":0} or {"type":"eq","left":"${ifValue}","right":true}`,
            });
          }
        }
      }

      for (const [key, value] of Object.entries(record)) {
        walk(value, `${path}.${key}`);
      }
    }
  }

  walk(contract, '$');

  return { expressions, errors };
}

function extractFields(obj: unknown): Set<string> {
  const fields = new Set<string>();
  if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
    for (const key of Object.keys(obj as object)) {
      fields.add(key);
    }
  }
  return fields;
}

function createUndefinedRefError(
  id: string,
  expression: string,
  field: string,
  layer: string,
  path: string,
  availableFields: Set<string>
): ValidationError {
  const available = Array.from(availableFields).slice(0, 5);

  return {
    id,
    severity: 'error',
    category: 'EL_UNDEFINED_REF',
    blocking: true,
    location: createLocation(path, expression),
    message: `Undefined ${layer} field: ${field}`,
    expected: {
      values: available,
    },
    actual: { value: field },
    fix: {
      action: `Define "${field}" in ${layer} section or fix the reference`,
      suggestion: available.length > 0
        ? `Available ${layer} fields: ${available.join(', ')}`
        : `No ${layer} fields defined. Add "${layer}": { "${field}": ... } to contract.`,
      refs: [`Check contract ${layer} section`],
    },
    aiHint: `${expression} references undefined field "${field}". Either add it to ${layer} or fix the typo.`,
  };
}

function createLocation(path: string, value: unknown): SourceLocation {
  const snippet = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
  return {
    jsonPath: path,
    jsonPointer: path.replace(/\$/g, '').replace(/\./g, '/').replace(/\[(\d+)\]/g, '/$1'),
    snippet: snippet.length > 200 ? snippet.slice(0, 200) + '...' : snippet,
  };
}
