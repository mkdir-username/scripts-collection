#!/usr/bin/env node

/**
 * CLI Interface for SDUI JSON Validator v2.3.1
 *
 * Command-line interface с поддержкой:
 * - Флагов verbose, no-color, jinja-aware
 * - Вывод версии и помощи
 * - Exit codes (0 = success, 1 = error)
 *
 * @module cli
 * @version 2.3.1
 */

import { Command } from 'commander';
import * as fs from 'fs';
import * as path from 'path';
import chalk from 'chalk';
import { validateFile, validateFiles } from './main';
import { ValidationResult, ValidationSeverity } from './types';

// ============================================================================
// Constants
// ============================================================================

const VERSION = '2.3.1';
const PACKAGE_NAME = 'vscode-sdui-validator';

// ============================================================================
// CLI Configuration
// ============================================================================

const program = new Command();

program
  .name(PACKAGE_NAME)
  .version(VERSION, '-v, --version', 'Output the current version')
  .description('SDUI JSON Schema Validator with Jinja2 support for VSCode')
  .argument('[files...]', 'Files or directories to validate')
  .option('--verbose', 'Enable verbose output', false)
  .option('--no-color', 'Disable colored output', false)
  .option('--jinja-aware', 'Enable Jinja2 template awareness', true)
  .option('--strict', 'Enable strict validation mode', true)
  .option('--max-errors <number>', 'Maximum errors to display', '50')
  .option('-r, --recursive', 'Recursively validate directories', false)
  .option('-o, --output <format>', 'Output format (text|json|html)', 'text')
  .option('--max-file-size <bytes>', 'Maximum file size in bytes', '10485760')
  .option('--performance', 'Show performance metrics', false)
  .action(async (files: string[], options) => {
    await runValidator(files, options);
  });

program
  .command('validate <files...>')
  .description('Validate JSON/Jinja files')
  .option('--verbose', 'Enable verbose output')
  .option('--no-color', 'Disable colored output')
  .option('--jinja-aware', 'Enable Jinja2 awareness')
  .action(async (files: string[], options) => {
    await runValidator(files, { ...options, color: true });
  });

program
  .command('check <file>')
  .description('Quick syntax check for a single file')
  .action(async (file: string) => {
    await runQuickCheck(file);
  });

program
  .command('batch <_pattern>')
  .description('Validate files matching glob pattern')
  .option('-r, --recursive', 'Recursive search')
  .action(async () => {
    console.log(chalk.yellow('Batch validation not yet implemented'));
    process.exit(1);
  });

// ============================================================================
// Main Validator Runner
// ============================================================================

interface CLIOptions {
  verbose: boolean;
  color: boolean;
  jinjaAware: boolean;
  strict: boolean;
  maxErrors: string;
  recursive: boolean;
  output: 'text' | 'json' | 'html';
  maxFileSize: string;
  performance: boolean;
}

async function runValidator(files: string[], options: CLIOptions): Promise<void> {
  const startTime = Date.now();

  // Проверка наличия файлов
  if (!files || files.length === 0) {
    console.error(chalk.red('Error: No files specified'));
    console.log('');
    console.log('Usage: vscode-validator [options] <files...>');
    console.log('');
    console.log('Try "vscode-validator --help" for more information');
    process.exit(1);
  }

  // Настройка цветного вывода
  if (!options.color) {
    chalk.level = 0;
  }

  // Вывод заголовка
  if (options.verbose) {
    console.log(chalk.cyan.bold(`\n${PACKAGE_NAME} v${VERSION}`));
    console.log(chalk.gray('='.repeat(60)));
    console.log('');
  }

  // Сбор всех файлов для валидации
  const filesToValidate: string[] = [];

  for (const fileOrDir of files) {
    const resolvedPath = path.resolve(fileOrDir);

    if (!fs.existsSync(resolvedPath)) {
      console.error(chalk.red(`Error: File or directory not found: ${fileOrDir}`));
      process.exit(1);
    }

    const stat = fs.statSync(resolvedPath);

    if (stat.isDirectory()) {
      if (options.recursive) {
        const dirFiles = await collectFilesFromDirectory(resolvedPath, true);
        filesToValidate.push(...dirFiles);
      } else {
        console.error(chalk.yellow(`Warning: Skipping directory ${fileOrDir} (use -r for recursive)`));
      }
    } else if (stat.isFile()) {
      filesToValidate.push(resolvedPath);
    }
  }

  if (filesToValidate.length === 0) {
    console.error(chalk.red('Error: No valid files to validate'));
    process.exit(1);
  }

  // Вывод информации о файлах
  if (options.verbose) {
    console.log(chalk.blue(`Validating ${filesToValidate.length} file(s)...`));
    console.log('');
  }

  // Валидация файлов
  const results = await validateFiles(filesToValidate, {
    jinjaAware: options.jinjaAware,
    strict: options.strict,
    maxFileSize: parseInt(options.maxFileSize, 10),
    trackPerformance: options.performance
  });

  // Вывод результатов
  const totalDuration = Date.now() - startTime;

  if (options.output === 'json') {
    outputJSON(results);
  } else if (options.output === 'html') {
    outputHTML(results);
  } else {
    outputText(results, options, totalDuration);
  }

  // Exit code
  const hasErrors = results.some(r => r.errorCount > 0);
  process.exit(hasErrors ? 1 : 0);
}

// ============================================================================
// Quick Check
// ============================================================================

async function runQuickCheck(file: string): Promise<void> {
  const resolvedPath = path.resolve(file);

  if (!fs.existsSync(resolvedPath)) {
    console.error(chalk.red(`File not found: ${file}`));
    process.exit(1);
  }

  console.log(chalk.blue(`Checking ${file}...`));

  const result = await validateFile(resolvedPath, { jinjaAware: true });

  if (result.isValid) {
    console.log(chalk.green('✓ Valid'));
    process.exit(0);
  } else {
    console.log(chalk.red(`✗ ${result.errorCount} error(s) found`));
    result.errors.forEach(error => {
      console.log(chalk.red(`  Line ${error.line}:${error.column} - ${error.message}`));
    });
    process.exit(1);
  }
}

// ============================================================================
// Output Formatters
// ============================================================================

function outputText(results: ValidationResult[], options: CLIOptions, totalDuration: number): void {
  const maxErrors = parseInt(options.maxErrors, 10);
  let totalErrors = 0;
  let totalWarnings = 0;
  let validFiles = 0;

  results.forEach(result => {
    const relPath = path.relative(process.cwd(), result.filePath);

    // Статус файла
    if (result.isValid) {
      validFiles++;
      if (options.verbose) {
        console.log(chalk.green(`✓ ${relPath}`));
        if (options.performance && result.metrics) {
          console.log(chalk.gray(`  Duration: ${result.duration}ms | Lines: ${result.metrics.totalLines}`));
        }
      }
    } else {
      console.log(chalk.red(`✗ ${relPath}`));

      // Вывод ошибок
      const errorsToShow = result.errors.slice(0, maxErrors);
      errorsToShow.forEach(error => {
        const severityIcon = error.severity === ValidationSeverity.ERROR ? '✗' : '⚠';
        const severityColor = error.severity === ValidationSeverity.ERROR ? chalk.red : chalk.yellow;

        console.log(
          severityColor(
            `  ${severityIcon} Line ${error.line}:${error.column} - ${error.message}`
          )
        );

        if (options.verbose && error.description) {
          console.log(chalk.gray(`     ${error.description}`));
        }

        if (error.fix) {
          console.log(chalk.cyan(`     Fix: ${error.fix}`));
        }
      });

      if (result.errors.length > maxErrors) {
        console.log(chalk.yellow(`  ... and ${result.errors.length - maxErrors} more error(s)`));
      }

      console.log('');
    }

    totalErrors += result.errorCount;
    totalWarnings += result.warningCount;
  });

  // Итоговая статистика
  console.log(chalk.gray('─'.repeat(60)));
  console.log('');
  console.log(chalk.bold('Summary:'));
  console.log(`  Files validated: ${results.length}`);
  console.log(`  Valid files:     ${chalk.green(validFiles.toString())}`);
  console.log(`  Files with errors: ${chalk.red((results.length - validFiles).toString())}`);
  console.log(`  Total errors:    ${chalk.red(totalErrors.toString())}`);
  console.log(`  Total warnings:  ${chalk.yellow(totalWarnings.toString())}`);

  if (options.performance) {
    console.log(`  Total duration:  ${totalDuration}ms`);
    const avgDuration = results.reduce((sum, r) => sum + r.duration, 0) / results.length;
    console.log(`  Average duration: ${Math.round(avgDuration)}ms`);
  }

  console.log('');

  if (totalErrors > 0) {
    console.log(chalk.red.bold(`Validation failed with ${totalErrors} error(s)`));
  } else {
    console.log(chalk.green.bold('All files are valid!'));
  }
}

function outputJSON(results: ValidationResult[]): void {
  const output = {
    version: VERSION,
    timestamp: new Date().toISOString(),
    summary: {
      total: results.length,
      valid: results.filter(r => r.isValid).length,
      errors: results.reduce((sum, r) => sum + r.errorCount, 0),
      warnings: results.reduce((sum, r) => sum + r.warningCount, 0)
    },
    results: results.map(r => ({
      file: r.filePath,
      valid: r.isValid,
      errors: r.errors,
      duration: r.duration,
      fileSize: r.fileSize,
      fileType: r.fileType
    }))
  };

  console.log(JSON.stringify(output, null, 2));
}

function outputHTML(results: ValidationResult[]): void {
  console.log('<!DOCTYPE html>');
  console.log('<html lang="en">');
  console.log('<head>');
  console.log('  <meta charset="UTF-8">');
  console.log('  <title>Validation Report</title>');
  console.log('  <style>');
  console.log('    body { font-family: Arial, sans-serif; margin: 20px; }');
  console.log('    .error { color: red; }');
  console.log('    .warning { color: orange; }');
  console.log('    .success { color: green; }');
  console.log('    .file { margin-bottom: 20px; border: 1px solid #ccc; padding: 10px; }');
  console.log('  </style>');
  console.log('</head>');
  console.log('<body>');
  console.log(`  <h1>Validation Report - ${new Date().toISOString()}</h1>`);

  results.forEach(result => {
    const status = result.isValid ? 'success' : 'error';
    console.log(`  <div class="file ${status}">`);
    console.log(`    <h2>${result.filePath}</h2>`);

    if (result.isValid) {
      console.log(`    <p class="success">✓ Valid</p>`);
    } else {
      console.log(`    <ul>`);
      result.errors.forEach(error => {
        const cssClass = error.severity === ValidationSeverity.ERROR ? 'error' : 'warning';
        console.log(`      <li class="${cssClass}">`);
        console.log(`        Line ${error.line}:${error.column} - ${error.message}`);
        console.log(`      </li>`);
      });
      console.log(`    </ul>`);
    }

    console.log(`  </div>`);
  });

  console.log('</body>');
  console.log('</html>');
}

// ============================================================================
// Utility Functions
// ============================================================================

async function collectFilesFromDirectory(dirPath: string, recursive: boolean): Promise<string[]> {
  const files: string[] = [];
  const entries = fs.readdirSync(dirPath, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dirPath, entry.name);

    if (entry.isDirectory() && recursive) {
      const subFiles = await collectFilesFromDirectory(fullPath, recursive);
      files.push(...subFiles);
    } else if (entry.isFile() && isValidFileExtension(entry.name)) {
      files.push(fullPath);
    }
  }

  return files;
}

function isValidFileExtension(fileName: string): boolean {
  const validExtensions = ['.json', '.jinja.json', '.j2.java'];
  return validExtensions.some(ext => fileName.endsWith(ext));
}

// ============================================================================
// Entry Point
// ============================================================================

// Обработка необработанных ошибок
process.on('unhandledRejection', (error: Error) => {
  console.error(chalk.red('Unhandled error:'));
  console.error(error);
  process.exit(1);
});

process.on('uncaughtException', (error: Error) => {
  console.error(chalk.red('Uncaught exception:'));
  console.error(error);
  process.exit(1);
});

// Запуск CLI
program.parse(process.argv);

// Если не передано аргументов, показываем help
if (!process.argv.slice(2).length) {
  program.outputHelp();
}
