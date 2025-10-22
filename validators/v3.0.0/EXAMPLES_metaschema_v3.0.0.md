# Metaschema Validator v3.0.0 - Usage Examples

## Example 1: Basic Validation

```typescript
import { validateMetaschemas } from './metaschema_validator_v3.0.0';

// Validate FMS repository
const rootPath = '/Users/username/Documents/FMS_GIT';
const success = validateMetaschemas(rootPath);

if (success) {
  console.log('✅ All schemas are valid');
} else {
  console.log('❌ Validation failed');
  process.exit(1);
}
```

## Example 2: Validate Specific Schema

```typescript
import { MetaschemaValidator } from './metaschema_validator_v3.0.0';

const validator = new MetaschemaValidator(
  'metaschema/schema/strict_unversioned.json'
);

const errors = validator.validate('SDUI/components/ButtonView/v1/ButtonView.json');

if (errors.length > 0) {
  console.error('Schema validation errors:');
  errors.forEach((err) => console.error(`  - ${err}`));
}
```

## Example 3: Find Root Schemas

```typescript
import { RootSchemaFinder } from './metaschema_validator_v3.0.0';

const finder = new RootSchemaFinder('/Users/username/Documents/FMS_GIT/SDUI');

console.log('Root schemas (not referenced by others):');
finder.rootSchemaPaths.forEach((path) => {
  console.log(`  - ${path}`);
});

if (finder.invalidReferencePaths.length > 0) {
  console.log('\nInvalid references:');
  finder.invalidReferencePaths.forEach(([from, to]) => {
    console.log(`  ${from} -> ${to}`);
  });
}
```

## Example 4: Custom Configuration

```typescript
import { Rules, loadValidatorConfig } from './metaschema_validator_v3.0.0';

// Load custom config
const config = loadValidatorConfig('./my-validator.yaml');

// Run validation
const success = Rules.run(
  '/path/to/repo',
  config,
  './my-validator.yaml'
);
```

## Example 5: Programmatic Rule Execution

```typescript
import {
  RootSchemaFinder,
  UnreferencedSchemaRule,
  MetaschemaValidationRule,
  loadValidatorConfig,
} from './metaschema_validator_v3.0.0';

const config = loadValidatorConfig('.validator.yaml');
const schemaConfig = config.schemas.SDUI;
const rootPath = '/Users/username/Documents/FMS_GIT/SDUI';

// Find root schemas
const finder = new RootSchemaFinder(rootPath);

// Check unreferenced schemas
const unreferencedRule = new UnreferencedSchemaRule(finder, schemaConfig);
const unreferencedErrors = unreferencedRule.run();

// Validate against metaschema
const validationRule = new MetaschemaValidationRule(rootPath, schemaConfig);
const validationErrors = validationRule.run();

// Combine errors
const allErrors = [...unreferencedErrors, ...validationErrors];

if (allErrors.length > 0) {
  console.error('Validation failed:');
  allErrors.forEach((err) => {
    console.error(`${err.path}: ${err.ruleName}: ${err.error}`);
  });
}
```

## Example 6: Pre-commit Hook Script

```typescript
#!/usr/bin/env node
/**
 * Pre-commit hook for metaschema validation
 * Save as: .git/hooks/pre-commit
 */

import { validateMetaschemas } from './metaschema_validator_v3.0.0';
import { execSync } from 'child_process';

// Get staged files
const stagedFiles = execSync('git diff --cached --name-only --diff-filter=ACM')
  .toString()
  .trim()
  .split('\n')
  .filter((file) => file.endsWith('.json'));

if (stagedFiles.length === 0) {
  console.log('No JSON files staged, skipping validation');
  process.exit(0);
}

console.log(`Validating ${stagedFiles.length} JSON schemas...`);

const success = validateMetaschemas('/Users/username/Documents/FMS_GIT');

if (!success) {
  console.error('\n❌ Metaschema validation failed');
  console.error('Fix the errors above before committing');
  process.exit(1);
}

console.log('✅ Metaschema validation passed');
process.exit(0);
```

## Example 7: CI/CD Integration

```typescript
/**
 * CI/CD validation script
 */

import { validateMetaschemas } from './metaschema_validator_v3.0.0';
import * as fs from 'fs';

const rootPath = process.env.CI_PROJECT_DIR || '/Users/username/Documents/FMS_GIT';
const reportPath = process.env.CI_REPORT_PATH || './validation-report.json';

console.log(`Validating schemas in: ${rootPath}`);

const startTime = Date.now();
const success = validateMetaschemas(rootPath);
const duration = Date.now() - startTime;

// Generate report
const report = {
  timestamp: new Date().toISOString(),
  success,
  duration,
  repository: rootPath,
};

fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

console.log(`\nValidation completed in ${duration}ms`);
console.log(`Report saved to: ${reportPath}`);

process.exit(success ? 0 : 1);
```

## Example 8: Watch Mode for Development

```typescript
import { validateMetaschemas } from './metaschema_validator_v3.0.0';
import * as chokidar from 'chokidar';

const rootPath = '/Users/username/Documents/FMS_GIT';

console.log('👀 Watching for schema changes...');

// Initial validation
validateMetaschemas(rootPath);

// Watch for changes
const watcher = chokidar.watch('**/*.json', {
  cwd: rootPath,
  ignored: /(^|[\/\\])\../,
});

watcher.on('change', (path) => {
  console.log(`\n📝 File changed: ${path}`);
  console.log('Running validation...\n');
  validateMetaschemas(rootPath);
});
```

## Example 9: Custom Error Handler

```typescript
import {
  Rules,
  loadValidatorConfig,
  ValidationError,
} from './metaschema_validator_v3.0.0';

class CustomErrorHandler {
  private errors: ValidationError[] = [];

  addError(error: ValidationError) {
    this.errors.push(error);
  }

  getErrorsByRule(ruleName: string): ValidationError[] {
    return this.errors.filter((err) => err.ruleName === ruleName);
  }

  formatReport(): string {
    const grouped = this.errors.reduce((acc, err) => {
      if (!acc[err.ruleName]) {
        acc[err.ruleName] = [];
      }
      acc[err.ruleName].push(err);
      return acc;
    }, {} as Record<string, ValidationError[]>);

    let report = 'Validation Report\n';
    report += '='.repeat(80) + '\n\n';

    Object.entries(grouped).forEach(([ruleName, errors]) => {
      report += `${ruleName} (${errors.length} errors):\n`;
      errors.forEach((err) => {
        report += `  - ${err.path}: ${err.error}\n`;
      });
      report += '\n';
    });

    return report;
  }
}

// Usage
const handler = new CustomErrorHandler();
// ... collect errors
console.log(handler.formatReport());
```

## Example 10: Parallel Validation (Future)

```typescript
/**
 * Note: This is a future enhancement idea
 * Current implementation is sequential
 */

import { MetaschemaValidator } from './metaschema_validator_v3.0.0';
import { Worker } from 'worker_threads';

async function parallelValidate(
  schemas: string[],
  metaschemaPath: string
): Promise<Map<string, string[]>> {
  const workers = [];
  const results = new Map<string, string[]>();

  for (const schema of schemas) {
    const worker = new Worker('./validator-worker.js', {
      workerData: { schema, metaschemaPath },
    });

    workers.push(
      new Promise((resolve) => {
        worker.on('message', (errors) => {
          results.set(schema, errors);
          resolve(null);
        });
      })
    );
  }

  await Promise.all(workers);
  return results;
}
```

## Example 11: Integration with Jest

```typescript
/**
 * Jest test suite for schemas
 */

import { MetaschemaValidator } from './metaschema_validator_v3.0.0';
import * as glob from 'glob';

describe('SDUI Schemas', () => {
  const validator = new MetaschemaValidator(
    'metaschema/schema/strict_unversioned.json'
  );

  const schemas = glob.sync('SDUI/components/**/v*/*.json');

  schemas.forEach((schemaPath) => {
    test(`${schemaPath} should be valid`, () => {
      const errors = validator.validate(schemaPath);
      expect(errors).toHaveLength(0);
    });
  });
});
```

## Example 12: Custom Metaschema

```typescript
import { MetaschemaValidator } from './metaschema_validator_v3.0.0';
import * as fs from 'fs';

// Create custom metaschema
const customMetaschema = {
  type: 'object',
  required: ['type', 'name', 'description'],
  properties: {
    type: { type: 'string' },
    name: { type: 'string' },
    description: { type: 'string' },
    customField: { type: 'string' },
  },
};

// Save to file
const metaschemaPath = './custom-metaschema.json';
fs.writeFileSync(metaschemaPath, JSON.stringify(customMetaschema, null, 2));

// Use for validation
const validator = new MetaschemaValidator(metaschemaPath);
const errors = validator.validate('./my-schema.json');
```

## Common Patterns

### Pattern 1: Validate Before Commit

```bash
#!/bin/bash
# .git/hooks/pre-commit

node -e "
  const { validateMetaschemas } = require('./metaschema_validator_v3.0.0');
  const success = validateMetaschemas('.');
  process.exit(success ? 0 : 1);
"
```

### Pattern 2: Generate Validation Report

```typescript
import { validateMetaschemas } from './metaschema_validator_v3.0.0';
import * as fs from 'fs';

// Redirect console output to capture errors
const originalLog = console.log;
const logs: string[] = [];

console.log = (...args) => {
  logs.push(args.join(' '));
  originalLog(...args);
};

const success = validateMetaschemas('.');

console.log = originalLog;

// Save report
fs.writeFileSync(
  'validation-report.txt',
  logs.join('\n')
);
```

### Pattern 3: Validate Specific Categories

```typescript
import { Rules, loadValidatorConfig } from './metaschema_validator_v3.0.0';

const config = loadValidatorConfig('.validator.yaml');

// Validate only SDUI schemas
const sduiConfig = {
  schemas: {
    SDUI: config.schemas.SDUI,
  },
};

const success = Rules.run('.', sduiConfig, '.validator.yaml');
```

---

## Additional Resources

- [README_metaschema_v3.0.0.md](./README_metaschema_v3.0.0.md) - Full documentation
- [Ajv Documentation](https://ajv.js.org/) - JSON Schema validator
- [FMS CLAUDE.md](../../CLAUDE.md) - Project guidelines
