/**
 * Test script for Metaschema Validator v3.0.0
 *
 * @version 3.0.0
 */

import {
  MetaschemaValidator,
  RootSchemaFinder,
  UnreferencedSchemaRule,
  MetaschemaValidationRule,
  loadValidatorConfig,
  validateMetaschemas,
} from './metaschema_validator_v3.0.0';

import * as path from 'path';

// Test configuration
const FMS_ROOT = '/Users/username/Documents/FMS_GIT';
const CONFIG_PATH = path.join(FMS_ROOT, '.validator.yaml');

console.log('='.repeat(80));
console.log('Metaschema Validator v3.0.0 - Test Suite');
console.log('='.repeat(80));

// Test 1: Load configuration
console.log('\n[Test 1] Loading validator configuration...');
try {
  const config = loadValidatorConfig(CONFIG_PATH);
  console.log('✅ Configuration loaded successfully');
  console.log(`   Found ${Object.keys(config.schemas).length} schema directories:`);
  Object.keys(config.schemas).forEach((dir) => {
    console.log(`   - ${dir}`);
  });
} catch (error) {
  console.error('❌ Failed to load configuration:', error);
  process.exit(1);
}

// Test 2: MetaschemaValidator
console.log('\n[Test 2] Testing MetaschemaValidator...');
try {
  const metaschemaPath = path.join(
    FMS_ROOT,
    'metaschema/schema/strict_unversioned.json'
  );
  const validator = new MetaschemaValidator(metaschemaPath);
  console.log('✅ MetaschemaValidator initialized');

  // Test with a known schema
  const testSchemaPath = path.join(
    FMS_ROOT,
    'SDUI/components/ButtonView/v1/ButtonView.json'
  );
  const errors = validator.validate(testSchemaPath);

  if (errors.length === 0) {
    console.log(`✅ ButtonView schema is valid`);
  } else {
    console.log(`⚠️  ButtonView schema has errors:`);
    errors.forEach((err) => console.log(`   ${err}`));
  }
} catch (error) {
  console.error('❌ MetaschemaValidator test failed:', error);
}

// Test 3: RootSchemaFinder
console.log('\n[Test 3] Testing RootSchemaFinder...');
try {
  const sduiPath = path.join(FMS_ROOT, 'SDUI');
  const finder = new RootSchemaFinder(sduiPath);

  console.log(`✅ Found ${finder.rootSchemaPaths.length} root schemas`);
  if (finder.rootSchemaPaths.length > 0) {
    console.log(`   First root: ${finder.rootSchemaPaths[0]}`);
  }

  if (finder.invalidReferencePaths.length > 0) {
    console.log(
      `⚠️  Found ${finder.invalidReferencePaths.length} invalid references`
    );
    finder.invalidReferencePaths.slice(0, 3).forEach(([from, to]) => {
      console.log(`   ${from} -> ${to}`);
    });
  } else {
    console.log(`✅ No invalid references found`);
  }
} catch (error) {
  console.error('❌ RootSchemaFinder test failed:', error);
}

// Test 4: UnreferencedSchemaRule
console.log('\n[Test 4] Testing UnreferencedSchemaRule...');
try {
  const config = loadValidatorConfig(CONFIG_PATH);
  const sduiPath = path.join(FMS_ROOT, 'SDUI');
  const finder = new RootSchemaFinder(sduiPath);
  const rule = new UnreferencedSchemaRule(finder, config.schemas.SDUI);
  const errors = rule.run();

  if (errors.length === 0) {
    console.log('✅ No unreferenced schema errors');
  } else {
    console.log(`⚠️  Found ${errors.length} unreferenced schema errors`);
    errors.slice(0, 3).forEach((err) => {
      console.log(`   ${err.ruleName}: ${err.path}`);
    });
  }
} catch (error) {
  console.error('❌ UnreferencedSchemaRule test failed:', error);
}

// Test 5: MetaschemaValidationRule
console.log('\n[Test 5] Testing MetaschemaValidationRule...');
try {
  const config = loadValidatorConfig(CONFIG_PATH);
  const modelsPath = path.join(FMS_ROOT, 'models');
  const rule = new MetaschemaValidationRule(
    modelsPath,
    config.schemas.models
  );
  const errors = rule.run();

  if (errors.length === 0) {
    console.log('✅ All models schemas are valid');
  } else {
    console.log(`⚠️  Found ${errors.length} metaschema validation errors`);
    errors.slice(0, 3).forEach((err) => {
      console.log(`   ${path.basename(err.path)}: ${err.error}`);
    });
  }
} catch (error) {
  console.error('❌ MetaschemaValidationRule test failed:', error);
}

// Test 6: Full validation
console.log('\n[Test 6] Running full validation...');
console.log('-'.repeat(80));

try {
  const success = validateMetaschemas(FMS_ROOT, CONFIG_PATH);

  console.log('-'.repeat(80));
  if (success) {
    console.log('✅ FULL VALIDATION PASSED');
  } else {
    console.log('❌ FULL VALIDATION FAILED');
  }
} catch (error) {
  console.error('❌ Full validation error:', error);
  process.exit(1);
}

console.log('\n' + '='.repeat(80));
console.log('Test suite completed');
console.log('='.repeat(80) + '\n');
