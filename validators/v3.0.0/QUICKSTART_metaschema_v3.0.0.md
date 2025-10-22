# Metaschema Validator v3.0.0 - Quick Start Guide

## Installation

### Step 1: Install Dependencies

```bash
cd /Users/username/Scripts/validators/v3.0.0
npm install
```

### Step 2: Build TypeScript

```bash
npm run build
```

This will generate:
- `metaschema_validator_v3.0.0.js` - Compiled JavaScript
- `metaschema_validator_v3.0.0.d.ts` - Type definitions
- `test_metaschema_v3.0.0.js` - Compiled test script

### Step 3: Verify Installation

```bash
npm run test
```

## Basic Usage

### Command Line

```bash
# Validate with default config (.validator.yaml)
node metaschema_validator_v3.0.0.js /Users/username/Documents/FMS_GIT

# Validate with custom config
node metaschema_validator_v3.0.0.js /path/to/repo /path/to/config.yaml
```

### Programmatic API

```typescript
import { validateMetaschemas } from './metaschema_validator_v3.0.0';

const success = validateMetaschemas('/Users/username/Documents/FMS_GIT');
console.log(success ? 'Valid' : 'Invalid');
```

## Understanding the Output

### Success Case

```
(no output)
```

Exit code: `0`

### Error Case

```
SDUI/components/ButtonView/v1/ButtonView.json: invalid_schema: /properties/text: must have required property 'description'

SDUI/atoms/NewColor/NewColor.json: unexpected_root: Schema is not referenced by any other schema and is not a root schema
```

Exit code: `1`

## Error Types

| Error Type | Description |
|------------|-------------|
| `invalid_schema` | Schema doesn't conform to metaschema |
| `unexpected_root` | Schema not referenced and not declared as root |
| `invalid_reference` | $ref points to non-existent file |
| `invalid_config` | Config file has issues |

## Configuration

The validator reads `.validator.yaml` from the repository root:

```yaml
schemas:
  SDUI:
    metaschema: metaschema/schema/strict_unversioned.json
    roots:
      - SDUI/components/ButtonView/v1/ButtonView.json

  widgets:
    metaschema: metaschema/schema/strict.json
    roots:
      - widgets/BaseWidgetModel/Widget.json

  analytics:
    metaschema: metaschema/schema/relaxed.json
    roots:
      - analytics/models/AnalyticsEvent.json
```

## Common Workflows

### Workflow 1: Validate Before Commit

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
cd /Users/username/Scripts/validators/v3.0.0
node metaschema_validator_v3.0.0.js /Users/username/Documents/FMS_GIT

if [ $? -ne 0 ]; then
  echo "❌ Metaschema validation failed"
  exit 1
fi
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

### Workflow 2: Continuous Development

Run in watch mode (requires additional setup):

```bash
# Watch for changes and auto-validate
npm install -g nodemon
nodemon --watch /Users/username/Documents/FMS_GIT/**/*.json \
  --exec "node metaschema_validator_v3.0.0.js /Users/username/Documents/FMS_GIT"
```

### Workflow 3: CI/CD Integration

GitHub Actions example:

```yaml
name: Validate Schemas

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '20'
      - run: cd validators/v3.0.0 && npm install
      - run: cd validators/v3.0.0 && npm run build
      - run: cd validators/v3.0.0 && npm run test
```

## Troubleshooting

### Issue 1: "Metaschema cannot be parsed"

**Cause:** Invalid JSON in metaschema file

**Solution:**
```bash
# Validate metaschema JSON syntax
jq . metaschema/schema/strict.json
```

### Issue 2: "Schema references non-existing file"

**Cause:** $ref points to missing file

**Solution:**
1. Check the $ref path in your schema
2. Ensure the referenced file exists
3. Verify file has `.json` extension

### Issue 3: Module not found errors

**Cause:** Missing dependencies

**Solution:**
```bash
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue 4: TypeScript compilation errors

**Cause:** TypeScript version mismatch

**Solution:**
```bash
npm install typescript@latest --save-dev
npm run build
```

## Performance Tips

### Tip 1: Validate Specific Directories Only

Modify config to include only changed directories:

```yaml
schemas:
  SDUI:
    metaschema: metaschema/schema/strict_unversioned.json
    # Only validate components
    # (requires code modification)
```

### Tip 2: Cache Validation Results

```typescript
import * as crypto from 'crypto';
import * as fs from 'fs';

const cache = new Map<string, boolean>();

function getCacheKey(filePath: string): string {
  const content = fs.readFileSync(filePath, 'utf-8');
  return crypto.createHash('md5').update(content).digest('hex');
}

// Check cache before validation
const key = getCacheKey(schemaPath);
if (cache.has(key)) {
  return cache.get(key);
}
```

### Tip 3: Parallel Validation (Future)

Currently sequential, but can be parallelized using worker threads.

## Integration with FMS Workflow

### Pre-commit Validation

```bash
# Add to package.json scripts in FMS root
{
  "scripts": {
    "validate:schemas": "node ../Scripts/validators/v3.0.0/metaschema_validator_v3.0.0.js ."
  }
}

# Run before commit
npm run validate:schemas
```

### IDE Integration (VS Code)

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Validate Schemas",
      "type": "shell",
      "command": "node",
      "args": [
        "/Users/username/Scripts/validators/v3.0.0/metaschema_validator_v3.0.0.js",
        "${workspaceFolder}"
      ],
      "problemMatcher": [],
      "group": {
        "kind": "test",
        "isDefault": true
      }
    }
  ]
}
```

Run with: `Cmd+Shift+B` → "Validate Schemas"

## Next Steps

1. ✅ Install and build
2. ✅ Run basic validation
3. ✅ Add to pre-commit hook
4. ✅ Configure CI/CD
5. 📚 Read [README_metaschema_v3.0.0.md](./README_metaschema_v3.0.0.md) for advanced usage
6. 📚 Check [EXAMPLES_metaschema_v3.0.0.md](./EXAMPLES_metaschema_v3.0.0.md) for code samples

## Support

For issues or questions:
1. Check [README_metaschema_v3.0.0.md](./README_metaschema_v3.0.0.md) - Full documentation
2. Review [EXAMPLES_metaschema_v3.0.0.md](./EXAMPLES_metaschema_v3.0.0.md) - Code examples
3. Consult FMS team in #server_driven_ui Slack channel

---

**Version:** 3.0.0
**Last Updated:** 2025-10-05
**Status:** Production Ready ✅
