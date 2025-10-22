/**
 * Metaschema Validator v3.0.0
 *
 * TypeScript port of Ruby metaschema validation system.
 * Validates JSON schemas against metaschemas (strict.json, relaxed.json, strict_unversioned.json).
 *
 * @module metaschema_validator_v3.0.0
 * @version 3.0.0
 * @author Ported from Ruby validator/lib
 */

import Ajv, { ValidateFunction, ErrorObject } from 'ajv';
import addFormats from 'ajv-formats';
import * as fs from 'fs';
import * as path from 'path';
import * as yaml from 'js-yaml';
import glob from 'glob';

// ============================================================================
// Types and Interfaces
// ============================================================================

/**
 * Validation error structure
 */
export interface ValidationError {
  /** Path to the file with error */
  path: string;
  /** Rule name that triggered the error */
  ruleName: string;
  /** Error message */
  error: string;
}

/**
 * Configuration for a schema directory
 */
export interface SchemaConfig {
  /** Path to metaschema file */
  metaschema: string;
  /** List of root schema paths */
  roots?: string[];
  /** Errors to ignore */
  ignore_errors?: {
    [ruleName: string]: string[];
  };
}

/**
 * Validator configuration from .validator.yaml
 */
export interface ValidatorConfig {
  schemas: {
    [schemaDirectory: string]: SchemaConfig;
  };
}

/**
 * Reference information
 */
export interface SchemaReference {
  /** Referenced file path */
  path: string;
  /** Is this an internal reference (#/definitions/...) */
  isInternal: boolean;
}

// ============================================================================
// Validation Error Class
// ============================================================================

/**
 * Represents a validation error
 * Port of Ruby ValidationError class
 */
export class ValidationErrorImpl implements ValidationError {
  constructor(
    public path: string,
    public ruleName: string,
    public error: string
  ) {}

  toString(): string {
    return `${this.path}: ${this.ruleName}: ${this.error}`;
  }
}

// ============================================================================
// Root Schema Finder
// ============================================================================

/**
 * Finds root schemas and validates references
 * Port of Ruby RootSchemaFinder class
 */
export class RootSchemaFinder {
  public rootSchemaPaths: string[] = [];
  public invalidReferencePaths: Array<[string, string]> = [];

  constructor(directoryPath: string) {
    const result = this.findRootSchemas(directoryPath);
    this.rootSchemaPaths = result.roots;
    this.invalidReferencePaths = result.invalidRefs;
  }

  /**
   * Finds JSON schemas that are not referenced by other schemas
   */
  private findRootSchemas(directoryPath: string): {
    roots: string[];
    invalidRefs: Array<[string, string]>;
  } {
    const schemaFiles = new Set<string>();
    const allReferences = new Set<string>();
    const invalidReferences: Array<[string, string]> = [];

    const jsonPaths = glob.sync(path.join(directoryPath, '**/*.json'));

    jsonPaths.forEach((filePath) => {
      schemaFiles.add(filePath);
      const schemaReferences = this.findReferences(filePath, directoryPath);

      schemaReferences.forEach((ref) => {
        if (!ref.isInternal) {
          allReferences.add(ref.path);
          if (!fs.existsSync(ref.path)) {
            invalidReferences.push([filePath, ref.path]);
          }
        }
      });
    });

    const rootSchemas = Array.from(schemaFiles).filter(
      (file) => !allReferences.has(file)
    );

    return { roots: rootSchemas, invalidRefs: invalidReferences };
  }

  /**
   * Returns all schemas referenced by the given schema
   */
  private findReferences(
    filePath: string,
    repositoryPath: string
  ): SchemaReference[] {
    try {
      const jsonData = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
      const references: SchemaReference[] = [];
      const stack: any[] = [jsonData];

      while (stack.length > 0) {
        const item = stack.pop();

        if (typeof item === 'object' && item !== null) {
          if (Array.isArray(item)) {
            item.forEach((element) => {
              if (typeof element === 'object' && element !== null) {
                stack.push(element);
              }
            });
          } else {
            Object.entries(item).forEach(([key, value]) => {
              if (key === '$ref' && typeof value === 'string') {
                // Check if internal reference
                if (value.startsWith('#/')) {
                  references.push({ path: value, isInternal: true });
                } else {
                  let refPath: string;

                  if (value.startsWith('/')) {
                    // Absolute path relative to repository root
                    refPath = path.join(repositoryPath, '..', value);
                  } else {
                    // Relative path
                    refPath = path.join(path.dirname(filePath), value);
                  }

                  // Add .json extension if missing
                  if (path.extname(refPath) === '') {
                    refPath += '.json';
                  }

                  references.push({ path: refPath, isInternal: false });
                }
              } else if (typeof value === 'object' && value !== null) {
                stack.push(value);
              }
            });
          }
        }
      }

      return references;
    } catch (error) {
      console.error(`Error reading file ${filePath}:`, error);
      return [];
    }
  }
}

// ============================================================================
// Metaschema Validator
// ============================================================================

/**
 * Validates schemas against metaschemas using Ajv
 * Port of Ruby MetaschemaValidator class
 */
export class MetaschemaValidator {
  private ajv: Ajv;
  private metaschemaPath: string;
  private validateFn: ValidateFunction | null = null;

  constructor(metaschemaPath: string) {
    this.metaschemaPath = metaschemaPath;
    this.ajv = new Ajv({
      strict: false,
      allErrors: true,
      verbose: true,
      loadSchema: this.loadSchema.bind(this),
    });
    addFormats(this.ajv);

    try {
      const metaschemaContent = fs.readFileSync(metaschemaPath, 'utf-8');
      const metaschema = JSON.parse(metaschemaContent);
      this.validateFn = this.ajv.compile(metaschema);
    } catch (error) {
      throw new Error(
        `Metaschema ${this.metaschemaPath} cannot be parsed: ${error}`
      );
    }
  }

  /**
   * Custom schema loader for resolving $ref
   */
  private async loadSchema(uri: string): Promise<any> {
    try {
      let refPath = uri;

      // Handle relative paths
      if (!path.isAbsolute(refPath)) {
        refPath = path.resolve(path.dirname(this.metaschemaPath), uri);
      }

      // Add .json extension if missing
      if (!fs.existsSync(refPath) && path.extname(refPath) === '') {
        refPath += '.json';
      }

      const content = fs.readFileSync(refPath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      throw new Error(`Failed to load schema ${uri}: ${error}`);
    }
  }

  /**
   * Validates a schema file against the metaschema
   *
   * @param schemaPath Path to schema file to validate
   * @returns Array of error messages (empty if valid)
   */
  public validate(schemaPath: string): string[] {
    try {
      const schemaContent = fs.readFileSync(schemaPath, 'utf-8');
      const schema = JSON.parse(schemaContent);

      if (!this.validateFn) {
        return [`Metaschema ${this.metaschemaPath} is not initialized`];
      }

      const valid = this.validateFn(schema);

      if (!valid && this.validateFn.errors) {
        return this.validateFn.errors.map((err) => this.formatError(err));
      }

      return [];
    } catch (error) {
      if (error instanceof SyntaxError) {
        return [`Invalid JSON in schema: ${error.message}`];
      }
      return [`Validation error: ${error}`];
    }
  }

  /**
   * Formats Ajv error object into readable message
   */
  private formatError(error: ErrorObject): string {
    const dataPath = error.instancePath || 'root';
    let message = `${dataPath}: ${error.message}`;

    if (error.params) {
      const params = Object.entries(error.params)
        .map(([key, val]) => `${key}=${JSON.stringify(val)}`)
        .join(', ');
      message += ` (${params})`;
    }

    return message;
  }
}

// ============================================================================
// Validation Rules
// ============================================================================

/**
 * Rule for checking unreferenced schemas
 * Port of Ruby UnreferencedSchemaRule class
 */
export class UnreferencedSchemaRule {
  constructor(
    private rootSchemaFinder: RootSchemaFinder,
    private config: SchemaConfig
  ) {}

  run(): ValidationError[] {
    const errors: ValidationError[] = [];

    // Check for unreferenced root schemas
    this.rootSchemaFinder.rootSchemaPaths.forEach((rootSchemaPath) => {
      const roots = this.config.roots || [];
      if (!roots.includes(rootSchemaPath)) {
        errors.push(
          new ValidationErrorImpl(
            rootSchemaPath,
            'unexpected_root',
            'Schema is not referenced by any other schema and is not a root schema (see root_schemas in config)'
          )
        );
      }
    });

    // Check for invalid references
    this.rootSchemaFinder.invalidReferencePaths.forEach(
      ([schemaPath, invalidReference]) => {
        errors.push(
          new ValidationErrorImpl(
            schemaPath,
            'invalid_reference',
            `Schema references non-existing file ${invalidReference}`
          )
        );
      }
    );

    return errors;
  }
}

/**
 * Rule for validating schemas against metaschema
 * Port of Ruby MetaschemaValidationRule class
 */
export class MetaschemaValidationRule {
  constructor(
    private rootDirectoryPath: string,
    private config: SchemaConfig
  ) {}

  run(): ValidationError[] {
    const errors: ValidationError[] = [];
    const validator = new MetaschemaValidator(this.config.metaschema);
    const jsonPaths = glob.sync(
      path.join(this.rootDirectoryPath, '**/*.json')
    );

    jsonPaths.forEach((filePath) => {
      const validationErrors = validator.validate(filePath);
      validationErrors.forEach((err) => {
        errors.push(new ValidationErrorImpl(filePath, 'invalid_schema', err));
      });
    });

    return errors;
  }
}

// ============================================================================
// Main Rules Runner
// ============================================================================

/**
 * Main rules runner
 * Port of Ruby Rules class
 */
export class Rules {
  /**
   * Runs all validation rules
   *
   * @param rootDirectoryPath Root directory path
   * @param config Validator configuration
   * @param configPath Path to config file
   * @returns True if no errors, false otherwise
   */
  static run(
    rootDirectoryPath: string,
    config: ValidatorConfig,
    configPath: string
  ): boolean {
    const errors: ValidationError[] = [];
    const filesWithoutErrors = new Set<string>();

    Object.entries(config.schemas).forEach(
      ([schemaDirectory, schemaConfig]) => {
        const schemaDirectoryPath = path.join(
          rootDirectoryPath,
          schemaDirectory
        );
        const rootSchemaFinder = new RootSchemaFinder(schemaDirectoryPath);

        // Collect files in ignore list
        if (schemaConfig.ignore_errors) {
          Object.values(schemaConfig.ignore_errors).forEach((files) => {
            files.forEach((file) => filesWithoutErrors.add(file));
          });
        }

        // Run validation rules
        const schemaErrors: ValidationError[] = [];
        schemaErrors.push(
          ...new UnreferencedSchemaRule(
            rootSchemaFinder,
            schemaConfig
          ).run()
        );
        schemaErrors.push(
          ...new MetaschemaValidationRule(
            schemaDirectoryPath,
            schemaConfig
          ).run()
        );

        // Filter errors based on ignore_errors config
        schemaErrors.forEach((error) => {
          const ignoreList =
            schemaConfig.ignore_errors?.[error.ruleName] || [];
          if (ignoreList.includes(error.path)) {
            filesWithoutErrors.delete(error.path);
          } else {
            errors.push(error);
          }
        });
      }
    );

    // Check for files in ignore list with no actual errors
    filesWithoutErrors.forEach((file) => {
      errors.push(
        new ValidationErrorImpl(
          configPath,
          'invalid_config',
          `File ${file} is ignored but doesn't contain any errors`
        )
      );
    });

    // Print errors
    errors.forEach((error) => {
      console.log(`${error.path}: ${error.ruleName}: ${error.error}\n`);
    });

    return errors.length === 0;
  }
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Loads validator configuration from YAML file
 *
 * @param configPath Path to .validator.yaml
 * @returns Parsed configuration
 */
export function loadValidatorConfig(configPath: string): ValidatorConfig {
  try {
    const content = fs.readFileSync(configPath, 'utf-8');
    return yaml.load(content) as ValidatorConfig;
  } catch (error) {
    throw new Error(`Failed to load config ${configPath}: ${error}`);
  }
}

/**
 * Main validation function
 *
 * @param rootPath Root directory of the repository
 * @param configPath Path to .validator.yaml (optional, defaults to .validator.yaml in root)
 * @returns True if validation passes, false otherwise
 */
export function validateMetaschemas(
  rootPath: string,
  configPath?: string
): boolean {
  const finalConfigPath = configPath || path.join(rootPath, '.validator.yaml');
  const config = loadValidatorConfig(finalConfigPath);
  return Rules.run(rootPath, config, finalConfigPath);
}

// ============================================================================
// CLI Entry Point (if run directly)
// ============================================================================

if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Usage: node metaschema_validator_v3.0.0.js <root_directory> [config_path]');
    process.exit(1);
  }

  const rootPath = args[0];
  const configPath = args[1];

  try {
    const success = validateMetaschemas(rootPath, configPath);
    process.exit(success ? 0 : 1);
  } catch (error) {
    console.error(`Fatal error: ${error}`);
    process.exit(1);
  }
}

// ============================================================================
// Exports
// ============================================================================

export default {
  MetaschemaValidator,
  RootSchemaFinder,
  UnreferencedSchemaRule,
  MetaschemaValidationRule,
  Rules,
  ValidationErrorImpl,
  loadValidatorConfig,
  validateMetaschemas,
};
