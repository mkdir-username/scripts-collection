"use strict";
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
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.Rules = exports.MetaschemaValidationRule = exports.UnreferencedSchemaRule = exports.MetaschemaValidator = exports.RootSchemaFinder = exports.ValidationErrorImpl = void 0;
exports.loadValidatorConfig = loadValidatorConfig;
exports.validateMetaschemas = validateMetaschemas;
const ajv_1 = __importDefault(require("ajv"));
const ajv_formats_1 = __importDefault(require("ajv-formats"));
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const yaml = __importStar(require("js-yaml"));
const glob_1 = __importDefault(require("glob"));
// ============================================================================
// Validation Error Class
// ============================================================================
/**
 * Represents a validation error
 * Port of Ruby ValidationError class
 */
class ValidationErrorImpl {
    constructor(path, ruleName, error) {
        this.path = path;
        this.ruleName = ruleName;
        this.error = error;
    }
    toString() {
        return `${this.path}: ${this.ruleName}: ${this.error}`;
    }
}
exports.ValidationErrorImpl = ValidationErrorImpl;
// ============================================================================
// Root Schema Finder
// ============================================================================
/**
 * Finds root schemas and validates references
 * Port of Ruby RootSchemaFinder class
 */
class RootSchemaFinder {
    constructor(directoryPath) {
        this.rootSchemaPaths = [];
        this.invalidReferencePaths = [];
        const result = this.findRootSchemas(directoryPath);
        this.rootSchemaPaths = result.roots;
        this.invalidReferencePaths = result.invalidRefs;
    }
    /**
     * Finds JSON schemas that are not referenced by other schemas
     */
    findRootSchemas(directoryPath) {
        const schemaFiles = new Set();
        const allReferences = new Set();
        const invalidReferences = [];
        const jsonPaths = glob_1.default.sync(path.join(directoryPath, '**/*.json'));
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
        const rootSchemas = Array.from(schemaFiles).filter((file) => !allReferences.has(file));
        return { roots: rootSchemas, invalidRefs: invalidReferences };
    }
    /**
     * Returns all schemas referenced by the given schema
     */
    findReferences(filePath, repositoryPath) {
        try {
            const jsonData = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
            const references = [];
            const stack = [jsonData];
            while (stack.length > 0) {
                const item = stack.pop();
                if (typeof item === 'object' && item !== null) {
                    if (Array.isArray(item)) {
                        item.forEach((element) => {
                            if (typeof element === 'object' && element !== null) {
                                stack.push(element);
                            }
                        });
                    }
                    else {
                        Object.entries(item).forEach(([key, value]) => {
                            if (key === '$ref' && typeof value === 'string') {
                                // Check if internal reference
                                if (value.startsWith('#/')) {
                                    references.push({ path: value, isInternal: true });
                                }
                                else {
                                    let refPath;
                                    if (value.startsWith('/')) {
                                        // Absolute path relative to repository root
                                        refPath = path.join(repositoryPath, '..', value);
                                    }
                                    else {
                                        // Relative path
                                        refPath = path.join(path.dirname(filePath), value);
                                    }
                                    // Add .json extension if missing
                                    if (path.extname(refPath) === '') {
                                        refPath += '.json';
                                    }
                                    references.push({ path: refPath, isInternal: false });
                                }
                            }
                            else if (typeof value === 'object' && value !== null) {
                                stack.push(value);
                            }
                        });
                    }
                }
            }
            return references;
        }
        catch (error) {
            console.error(`Error reading file ${filePath}:`, error);
            return [];
        }
    }
}
exports.RootSchemaFinder = RootSchemaFinder;
// ============================================================================
// Metaschema Validator
// ============================================================================
/**
 * Validates schemas against metaschemas using Ajv
 * Port of Ruby MetaschemaValidator class
 */
class MetaschemaValidator {
    constructor(metaschemaPath) {
        this.validateFn = null;
        this.metaschemaPath = metaschemaPath;
        this.ajv = new ajv_1.default({
            strict: false,
            allErrors: true,
            verbose: true,
            loadSchema: this.loadSchema.bind(this),
        });
        (0, ajv_formats_1.default)(this.ajv);
        try {
            const metaschemaContent = fs.readFileSync(metaschemaPath, 'utf-8');
            const metaschema = JSON.parse(metaschemaContent);
            this.validateFn = this.ajv.compile(metaschema);
        }
        catch (error) {
            throw new Error(`Metaschema ${this.metaschemaPath} cannot be parsed: ${error}`);
        }
    }
    /**
     * Custom schema loader for resolving $ref
     */
    async loadSchema(uri) {
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
        }
        catch (error) {
            throw new Error(`Failed to load schema ${uri}: ${error}`);
        }
    }
    /**
     * Validates a schema file against the metaschema
     *
     * @param schemaPath Path to schema file to validate
     * @returns Array of error messages (empty if valid)
     */
    validate(schemaPath) {
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
        }
        catch (error) {
            if (error instanceof SyntaxError) {
                return [`Invalid JSON in schema: ${error.message}`];
            }
            return [`Validation error: ${error}`];
        }
    }
    /**
     * Formats Ajv error object into readable message
     */
    formatError(error) {
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
exports.MetaschemaValidator = MetaschemaValidator;
// ============================================================================
// Validation Rules
// ============================================================================
/**
 * Rule for checking unreferenced schemas
 * Port of Ruby UnreferencedSchemaRule class
 */
class UnreferencedSchemaRule {
    constructor(rootSchemaFinder, config) {
        this.rootSchemaFinder = rootSchemaFinder;
        this.config = config;
    }
    run() {
        const errors = [];
        // Check for unreferenced root schemas
        this.rootSchemaFinder.rootSchemaPaths.forEach((rootSchemaPath) => {
            const roots = this.config.roots || [];
            if (!roots.includes(rootSchemaPath)) {
                errors.push(new ValidationErrorImpl(rootSchemaPath, 'unexpected_root', 'Schema is not referenced by any other schema and is not a root schema (see root_schemas in config)'));
            }
        });
        // Check for invalid references
        this.rootSchemaFinder.invalidReferencePaths.forEach(([schemaPath, invalidReference]) => {
            errors.push(new ValidationErrorImpl(schemaPath, 'invalid_reference', `Schema references non-existing file ${invalidReference}`));
        });
        return errors;
    }
}
exports.UnreferencedSchemaRule = UnreferencedSchemaRule;
/**
 * Rule for validating schemas against metaschema
 * Port of Ruby MetaschemaValidationRule class
 */
class MetaschemaValidationRule {
    constructor(rootDirectoryPath, config) {
        this.rootDirectoryPath = rootDirectoryPath;
        this.config = config;
    }
    run() {
        const errors = [];
        const validator = new MetaschemaValidator(this.config.metaschema);
        const jsonPaths = glob_1.default.sync(path.join(this.rootDirectoryPath, '**/*.json'));
        jsonPaths.forEach((filePath) => {
            const validationErrors = validator.validate(filePath);
            validationErrors.forEach((err) => {
                errors.push(new ValidationErrorImpl(filePath, 'invalid_schema', err));
            });
        });
        return errors;
    }
}
exports.MetaschemaValidationRule = MetaschemaValidationRule;
// ============================================================================
// Main Rules Runner
// ============================================================================
/**
 * Main rules runner
 * Port of Ruby Rules class
 */
class Rules {
    /**
     * Runs all validation rules
     *
     * @param rootDirectoryPath Root directory path
     * @param config Validator configuration
     * @param configPath Path to config file
     * @returns True if no errors, false otherwise
     */
    static run(rootDirectoryPath, config, configPath) {
        const errors = [];
        const filesWithoutErrors = new Set();
        Object.entries(config.schemas).forEach(([schemaDirectory, schemaConfig]) => {
            const schemaDirectoryPath = path.join(rootDirectoryPath, schemaDirectory);
            const rootSchemaFinder = new RootSchemaFinder(schemaDirectoryPath);
            // Collect files in ignore list
            if (schemaConfig.ignore_errors) {
                Object.values(schemaConfig.ignore_errors).forEach((files) => {
                    files.forEach((file) => filesWithoutErrors.add(file));
                });
            }
            // Run validation rules
            const schemaErrors = [];
            schemaErrors.push(...new UnreferencedSchemaRule(rootSchemaFinder, schemaConfig).run());
            schemaErrors.push(...new MetaschemaValidationRule(schemaDirectoryPath, schemaConfig).run());
            // Filter errors based on ignore_errors config
            schemaErrors.forEach((error) => {
                const ignoreList = schemaConfig.ignore_errors?.[error.ruleName] || [];
                if (ignoreList.includes(error.path)) {
                    filesWithoutErrors.delete(error.path);
                }
                else {
                    errors.push(error);
                }
            });
        });
        // Check for files in ignore list with no actual errors
        filesWithoutErrors.forEach((file) => {
            errors.push(new ValidationErrorImpl(configPath, 'invalid_config', `File ${file} is ignored but doesn't contain any errors`));
        });
        // Print errors
        errors.forEach((error) => {
            console.log(`${error.path}: ${error.ruleName}: ${error.error}\n`);
        });
        return errors.length === 0;
    }
}
exports.Rules = Rules;
// ============================================================================
// Helper Functions
// ============================================================================
/**
 * Loads validator configuration from YAML file
 *
 * @param configPath Path to .validator.yaml
 * @returns Parsed configuration
 */
function loadValidatorConfig(configPath) {
    try {
        const content = fs.readFileSync(configPath, 'utf-8');
        return yaml.load(content);
    }
    catch (error) {
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
function validateMetaschemas(rootPath, configPath) {
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
    }
    catch (error) {
        console.error(`Fatal error: ${error}`);
        process.exit(1);
    }
}
// ============================================================================
// Exports
// ============================================================================
exports.default = {
    MetaschemaValidator,
    RootSchemaFinder,
    UnreferencedSchemaRule,
    MetaschemaValidationRule,
    Rules,
    ValidationErrorImpl,
    loadValidatorConfig,
    validateMetaschemas,
};
//# sourceMappingURL=metaschema_validator_v3.0.0.js.map