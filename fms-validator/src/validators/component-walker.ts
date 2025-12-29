/**
 * Component Tree Walker
 * Iterates through contract and validates each component against SDUI schemas
 */

import { existsSync, readFileSync, readdirSync } from 'fs';
import { join } from 'path';
import type {
  ValidationError,
  ComponentNode,
  SourceLocation,
  ErrorCategory,
} from '../types/report.js';

interface WalkResult {
  tree: ComponentNode;
  errors: ValidationError[];
}

// Cache for loaded schemas
const schemaCache = new Map<string, object>();

// Known SDUI component locations
const COMPONENT_DIRS = ['components', 'layouts', 'actions', 'atoms', 'models'];

// Function types used in computed section (not components)
const FUNCTION_TYPES = new Set([
  // Logical
  'if', 'and', 'or', 'not', 'eq', 'neq', 'gt', 'gte', 'lt', 'lte',
  // String
  'concat', 'replace', 'substring', 'length', 'split', 'join', 'trim',
  'toLowerCase', 'toUpperCase', 'startsWith', 'endsWith', 'contains',
  // Math
  'sum', 'subtract', 'multiply', 'divide', 'mod', 'abs', 'round', 'floor', 'ceil',
  // Array
  'get', 'first', 'last', 'size', 'isEmpty', 'filter', 'map', 'find', 'reduce',
  // Format
  'formatAmount', 'formatDate', 'formatNumber', 'formatPhone', 'formatCard',
  // Template
  'applyTemplate', 'template',
  // Other
  'coalesce', 'defaultValue', 'toString', 'toNumber', 'toBoolean',
]);

// Type discriminators (not components, used inside properties)
const TYPE_DISCRIMINATORS = new Set([
  'name',       // Icon format: { "type": "name", "name": "glyph_..." }
  'url',        // Image format: { "type": "url", "url": "https://..." }
  'base64',     // Image format: { "type": "base64", "base64": "..." }
  'resource',   // Resource format: { "type": "resource", "resource": "..." }
]);

// Paths that contain function types, not component types
const FUNCTION_PATHS = ['$.computed', '$.data', '$.state'];

export function walkComponents(
  contract: unknown,
  fmsGitPath: string,
  platform: 'web' | 'ios' | 'android'
): WalkResult {
  const errors: ValidationError[] = [];
  let errorCounter = 0;

  const sduiPath = join(fmsGitPath, 'SDUI');

  // Build component index with platform preference
  const componentIndex = buildComponentIndex(sduiPath, platform);

  function walk(obj: unknown, path: string, parent: ComponentNode): ComponentNode {
    if (obj === null || typeof obj !== 'object') {
      return parent;
    }

    if (Array.isArray(obj)) {
      obj.forEach((item, idx) => {
        walk(item, `${path}[${idx}]`, parent);
      });
      return parent;
    }

    const record = obj as Record<string, unknown>;

    // Check if this is a component (has "type" field)
    if (typeof record['type'] === 'string') {
      const componentType = record['type'] as string;
      const node: ComponentNode = {
        path,
        type: componentType,
        status: 'OK',
        children: [],
      };

      // Skip Expression Language references
      if (componentType.startsWith('${')) {
        parent.children.push(node);
        return parent;
      }

      // Skip function types (used in computed/data/state sections)
      if (FUNCTION_TYPES.has(componentType)) {
        // Still walk children for nested structures
        for (const [key, value] of Object.entries(record)) {
          if (key !== 'type') {
            walk(value, `${path}.${key}`, parent);
          }
        }
        return parent;
      }

      // Skip type discriminators (used inside properties like icon, image)
      if (TYPE_DISCRIMINATORS.has(componentType)) {
        return parent;
      }

      // Skip validation in computed/data/state paths (they contain functions, not components)
      const isInFunctionPath = FUNCTION_PATHS.some(fp => path.startsWith(fp));
      if (isInFunctionPath) {
        // Still walk children
        for (const [key, value] of Object.entries(record)) {
          if (key !== 'type') {
            walk(value, `${path}.${key}`, parent);
          }
        }
        return parent;
      }

      // Validate component exists
      const componentInfo = componentIndex.get(componentType);
      if (!componentInfo) {
        errorCounter++;
        const error = createUnknownComponentError(
          `E${String(errorCounter).padStart(3, '0')}`,
          componentType,
          path,
          record,
          Array.from(componentIndex.keys())
        );
        errors.push(error);
        node.status = 'FAIL';
        node.errorId = error.id;
      } else {
        // Validate against schema
        const schemaErrors = validateAgainstSchema(
          record,
          componentInfo,
          path,
          platform,
          () => {
            errorCounter++;
            return `E${String(errorCounter).padStart(3, '0')}`;
          }
        );
        if (schemaErrors.length > 0) {
          errors.push(...schemaErrors);
          node.status = schemaErrors.some(e => e.blocking) ? 'FAIL' : 'WARN';
          node.errorId = schemaErrors[0].id;
        }
      }

      parent.children.push(node);

      // Walk children in "content", "children", "$children"
      if (record['content']) {
        walk(record['content'], `${path}.content`, node);
      }
      if (record['children']) {
        walk(record['children'], `${path}.children`, node);
      }
      if (record['$children']) {
        walk(record['$children'], `${path}.$children`, node);
      }

      return parent;
    }

    // Walk all object properties
    for (const [key, value] of Object.entries(record)) {
      walk(value, `${path}.${key}`, parent);
    }

    return parent;
  }

  const rootNode: ComponentNode = {
    path: '$',
    type: 'root',
    status: 'OK',
    children: [],
  };

  walk(contract, '$', rootNode);

  // Update root status based on children
  if (rootNode.children.some(c => c.status === 'FAIL')) {
    rootNode.status = 'FAIL';
  } else if (rootNode.children.some(c => c.status === 'WARN')) {
    rootNode.status = 'WARN';
  }

  return { tree: rootNode, errors };
}

function buildComponentIndex(sduiPath: string, platform: string): Map<string, ComponentInfo> {
  const index = new Map<string, ComponentInfo>();

  for (const dir of COMPONENT_DIRS) {
    const dirPath = join(sduiPath, dir);
    if (!existsSync(dirPath)) continue;

    const components = readdirSync(dirPath, { withFileTypes: true });
    for (const comp of components) {
      if (!comp.isDirectory()) continue;

      const componentPath = join(dirPath, comp.name);

      // Find versions
      const versions = readdirSync(componentPath, { withFileTypes: true })
        .filter(v => v.isDirectory() && v.name.startsWith('v'))
        .map(v => v.name)
        .sort(); // v1, v2, v3...

      if (versions.length === 0) continue;

      // Process all versions and prefer released for platform
      for (const version of versions) {
        const versionPath = join(componentPath, version);

        const jsonFiles = readdirSync(versionPath)
          .filter(f => f.endsWith('.json') && !f.startsWith('_'));

        for (const jsonFile of jsonFiles) {
          const componentName = jsonFile.replace('.json', '');
          const schemaPath = join(versionPath, jsonFile);

          // Check if this version is released for platform
          let isReleased = false;
          try {
            const schema = JSON.parse(readFileSync(schemaPath, 'utf-8'));
            const rv = schema.releaseVersion?.[platform];
            isReleased = rv && rv !== 'notReleased' && rv !== 'willNotBeReleased';
          } catch { /* ignore parse errors */ }

          const existing = index.get(componentName);
          // Index if: not indexed yet, OR current is released and existing is not
          if (!existing || (isReleased && !existing.released)) {
            index.set(componentName, {
              name: componentName,
              version,
              schemaPath,
              samplesPath: join(versionPath, 'samples'),
              category: dir,
              released: isReleased,
            });
          }
        }
      }
    }
  }

  return index;
}

interface ComponentInfo {
  name: string;
  version: string;
  schemaPath: string;
  samplesPath: string;
  category: string;
  released: boolean;
}

function loadSchema(schemaPath: string): object | null {
  if (schemaCache.has(schemaPath)) {
    return schemaCache.get(schemaPath)!;
  }

  try {
    const content = readFileSync(schemaPath, 'utf-8');
    const schema = JSON.parse(content);
    schemaCache.set(schemaPath, schema);
    return schema;
  } catch {
    return null;
  }
}

function validateAgainstSchema(
  component: Record<string, unknown>,
  info: ComponentInfo,
  path: string,
  platform: string,
  nextId: () => string
): ValidationError[] {
  const errors: ValidationError[] = [];
  const schema = loadSchema(info.schemaPath);

  if (!schema) {
    return errors;
  }

  const schemaObj = schema as Record<string, unknown>;

  // Check releaseVersion (only warn if no released version exists at all)
  if (!info.released) {
    errors.push({
      id: nextId(),
      severity: 'warning',
      category: 'RELEASE_VERSION',
      blocking: false,
      location: createLocation(path, component),
      message: `Component ${info.name} has no released version for ${platform}`,
      component: {
        type: info.name,
        version: info.version,
        schemaPath: info.schemaPath,
        samplesPath: info.samplesPath,
      },
      expected: { type: 'released' },
      actual: { value: 'notReleased' },
      fix: {
        action: `Check if ${info.name} should be used on ${platform} or find alternative`,
        refs: [info.schemaPath],
      },
      aiHint: `${info.name} has no released version for ${platform}. May work but not officially supported.`,
    });
  }

  // Check required properties
  const properties = schemaObj['properties'] as Record<string, unknown> | undefined;
  if (properties) {
    for (const [propName, propDef] of Object.entries(properties)) {
      const prop = propDef as Record<string, unknown>;
      const isRequired = prop['required'] === true;

      // Check in component.content (where most props live)
      const content = component['content'] as Record<string, unknown> | undefined;
      const hasInContent = content && propName in content;
      const hasDirectly = propName in component;

      if (isRequired && !hasInContent && !hasDirectly) {
        // Skip children/axis/alignment which are common and checked elsewhere
        if (['children', 'axis', 'alignment'].includes(propName)) continue;

        errors.push({
          id: nextId(),
          severity: 'warning',
          category: 'MISSING_REQUIRED',
          blocking: false,
          location: createLocation(`${path}.content`, component),
          message: `Missing required property: ${propName}`,
          component: {
            type: info.name,
            version: info.version,
            schemaPath: info.schemaPath,
            samplesPath: info.samplesPath,
          },
          expected: { type: String(prop['$ref'] || prop['type']) },
          fix: {
            action: `Add required property "${propName}" to ${info.name}`,
            refs: [info.schemaPath, info.samplesPath],
          },
          aiHint: `Add "${propName}" to content. See ${info.samplesPath} for examples.`,
        });
      }
    }
  }

  return errors;
}

function createUnknownComponentError(
  id: string,
  componentType: string,
  path: string,
  component: Record<string, unknown>,
  validTypes: string[]
): ValidationError {
  // Find similar component names
  const similar = validTypes
    .filter(t => {
      const lower = t.toLowerCase();
      const search = componentType.toLowerCase();
      return lower.includes(search) || search.includes(lower) ||
        levenshteinDistance(lower, search) <= 3;
    })
    .slice(0, 3);

  return {
    id,
    severity: 'critical',
    category: 'UNKNOWN_COMPONENT',
    blocking: true,
    location: createLocation(path, component),
    message: `Unknown component type: ${componentType}`,
    expected: {
      values: similar.length > 0 ? similar : validTypes.slice(0, 10),
    },
    actual: { value: componentType },
    fix: {
      action: `Replace "${componentType}" with a valid SDUI component`,
      suggestion: similar.length > 0
        ? `Did you mean: ${similar.join(', ')}?`
        : undefined,
      refs: ['SDUI/common/LayoutElement/LayoutElementContent.json'],
    },
    aiHint: similar.length > 0
      ? `Unknown type "${componentType}". Similar: ${similar.join(', ')}. Check LayoutElementContent.json for all valid types.`
      : `Unknown type "${componentType}". See LayoutElementContent.json for valid component types.`,
  };
}

function createLocation(path: string, obj: unknown): SourceLocation {
  const snippet = JSON.stringify(obj, null, 2).split('\n').slice(0, 5).join('\n');
  return {
    jsonPath: path,
    jsonPointer: path.replace(/\$/g, '').replace(/\./g, '/').replace(/\[(\d+)\]/g, '/$1'),
    snippet: snippet.length > 200 ? snippet.slice(0, 200) + '...' : snippet,
  };
}

function levenshteinDistance(a: string, b: string): number {
  const matrix: number[][] = [];

  for (let i = 0; i <= b.length; i++) {
    matrix[i] = [i];
  }
  for (let j = 0; j <= a.length; j++) {
    matrix[0][j] = j;
  }

  for (let i = 1; i <= b.length; i++) {
    for (let j = 1; j <= a.length; j++) {
      if (b.charAt(i - 1) === a.charAt(j - 1)) {
        matrix[i][j] = matrix[i - 1][j - 1];
      } else {
        matrix[i][j] = Math.min(
          matrix[i - 1][j - 1] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j] + 1
        );
      }
    }
  }

  return matrix[b.length][a.length];
}
