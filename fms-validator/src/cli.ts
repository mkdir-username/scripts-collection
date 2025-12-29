#!/usr/bin/env node
/**
 * FMS Contract Validator CLI
 * Usage: npx tsx src/cli.ts <contract.json> [options]
 */

import { Command } from 'commander';
import { existsSync, readFileSync, writeFileSync } from 'fs';
import { resolve, basename } from 'path';
import { createHash } from 'crypto';
import type { ValidatorConfig, ValidationReport } from './types/report.js';
import { validateContract } from './validators/index.js';

const program = new Command();

program
  .name('fms-validate')
  .description('Validate SDUI contracts against FMS schemas with Playwright runtime validation')
  .version('0.1.0');

program
  .argument('<contract>', 'Path to compiled JSON contract ([FULL_PC]_*.json)')
  .option('-p, --platform <platform>', 'Target platform: web, ios, android', 'web')
  .option('-o, --output <path>', 'Output report path (stdout if not set)')
  .option('--runtime', 'Enable Playwright runtime validation', false)
  .option('--screenshot', 'Capture screenshot (requires --runtime)', false)
  .option('--endpoint <path>', 'Newclick endpoint (default: /salary-api)', '/salary-api')
  .option('--fms <path>', 'Path to FMS_GIT', '/Users/username/Documents/FMS_GIT')
  .option('--newclick <path>', 'Path to newclick', '/Users/username/Documents/newclick-server-driven-ui')
  .option('--format <format>', 'Output format: json, text', 'json')
  .action(async (contractPath: string, options) => {
    try {
      const absolutePath = resolve(contractPath);

      if (!existsSync(absolutePath)) {
        console.error(`Error: Contract not found: ${absolutePath}`);
        process.exit(1);
      }

      const config: ValidatorConfig = {
        fmsGitPath: options.fms,
        newclickPath: options.newclick,
        platform: options.platform as 'web' | 'ios' | 'android',
        runtime: options.runtime,
        screenshot: options.screenshot,
        endpoint: options.endpoint,
        format: options.format as 'json' | 'text',
        output: options.output,
      };

      console.error(`\n📋 FMS Contract Validator v0.1.0`);
      console.error(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
      console.error(`Contract: ${basename(absolutePath)}`);
      console.error(`Platform: ${config.platform}`);
      console.error(`Runtime:  ${config.runtime ? 'enabled' : 'disabled'}`);
      console.error(`━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`);

      const report = await validateContract(absolutePath, config);

      // Output report
      const reportJson = JSON.stringify(report, null, 2);

      if (config.output) {
        writeFileSync(config.output, reportJson);
        console.error(`\n✅ Report saved: ${config.output}`);
      } else {
        console.log(reportJson);
      }

      // Exit code based on verdict
      if (report.verdict.status === 'INVALID') {
        console.error(`\n❌ Validation FAILED: ${report.verdict.blocking} blocking errors`);
        process.exit(1);
      } else if (report.verdict.status === 'WARNINGS') {
        console.error(`\n⚠️  Validation passed with ${report.verdict.nonBlocking} warnings`);
        process.exit(0);
      } else {
        console.error(`\n✅ Validation PASSED`);
        process.exit(0);
      }

    } catch (err) {
      console.error(`\n💥 Validator error:`, err);
      process.exit(2);
    }
  });

program.parse();
