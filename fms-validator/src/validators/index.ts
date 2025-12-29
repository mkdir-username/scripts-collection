/**
 * Main validator orchestrator
 */

import { readFileSync, existsSync } from 'fs';
import { dirname } from 'path';
import { createHash } from 'crypto';
import { basename } from 'path';
import type {
  ValidationReport,
  ValidationError,
  ValidatorConfig,
  ComponentNode,
  ExpressionValidation,
  ActionItem,
} from '../types/report.js';
import { walkComponents } from './component-walker.js';
import { validateExpressions } from './expression-validator.js';
import { runRuntimeValidation } from './runtime-validator.js';
import { validateJinjava } from './jinjava-validator.js';

export async function validateContract(
  contractPath: string,
  config: ValidatorConfig
): Promise<ValidationReport> {
  const startTime = Date.now();

  // Read and parse contract
  const contractJson = readFileSync(contractPath, 'utf-8');
  const contract = JSON.parse(contractJson);
  const contractHash = createHash('md5').update(contractJson).digest('hex').slice(0, 8);

  const errors: ValidationError[] = [];
  let componentTree: ComponentNode = { path: '$', type: 'root', status: 'OK', children: [] };
  let expressions: ExpressionValidation[] = [];

  // 1. Component tree validation
  console.error('🔍 Validating component tree...');
  const componentResult = walkComponents(contract, config.fmsGitPath, config.platform);
  errors.push(...componentResult.errors);
  componentTree = componentResult.tree;

  // 2. Expression Language validation
  console.error('🔍 Validating expressions...');
  const exprResult = validateExpressions(contract);
  errors.push(...exprResult.errors);
  expressions = exprResult.expressions;

  // 2.5. Jinjava validation (if source template exists)
  // [FULL_PC]_xxx_web.json → [JJ_PC]_xxx_web.java
  const jjPath = contractPath
    .replace('[FULL_PC]', '[JJ_PC]')
    .replace('[FULL_MOB]', '[JJ_MOB]')
    .replace(/\.json$/, '.java');
  if (existsSync(jjPath)) {
    console.error('🔍 Validating Jinjava template...');
    const jjResult = validateJinjava(jjPath, dirname(jjPath));
    errors.push(...jjResult.errors);
  }

  // 3. Runtime validation (optional)
  let runtime;
  if (config.runtime) {
    console.error('🌐 Running Playwright validation...');
    runtime = await runRuntimeValidation(contractPath, config);
    errors.push(...(runtime.errors || []));
  }

  // Sort errors by severity
  const severityOrder = { critical: 0, error: 1, warning: 2, info: 3 };
  errors.sort((a, b) => severityOrder[a.severity] - severityOrder[b.severity]);

  // Calculate verdict
  const blocking = errors.filter(e => e.blocking).length;
  const nonBlocking = errors.filter(e => !e.blocking).length;

  let status: 'VALID' | 'INVALID' | 'WARNINGS' = 'VALID';
  if (blocking > 0) status = 'INVALID';
  else if (nonBlocking > 0) status = 'WARNINGS';

  // Generate action items
  const actionItems = generateActionItems(errors);

  // Generate AI summary
  const forAI = generateAISummary(errors, blocking, nonBlocking);

  const report: ValidationReport = {
    version: '1.0',
    meta: {
      validator: 'fms-contract-validator@0.1.0',
      timestamp: new Date().toISOString(),
      contractPath,
      contractHash,
      platform: config.platform,
      newclickUrl: config.runtime
        ? `http://localhost:${process.env.NEWCLICK_PORT || '8043'}/?endpoint=${config.endpoint}`
        : undefined,
    },
    verdict: {
      status,
      blocking,
      nonBlocking,
      renderResult: runtime?.renderStatus || 'NOT_TESTED',
    },
    forAI,
    errors,
    componentTree,
    expressions,
    runtime: runtime ? {
      rendered: runtime.rendered,
      renderStatus: runtime.renderStatus,
      consoleErrors: runtime.consoleErrors,
      networkErrors: runtime.networkErrors,
      screenshot: runtime.screenshot,
    } : undefined,
    actionItems,
  };

  const duration = Date.now() - startTime;
  console.error(`⏱️  Validation completed in ${duration}ms`);

  return report;
}

function generateActionItems(errors: ValidationError[]): ActionItem[] {
  const items: ActionItem[] = [];

  // Group by category
  const byCategory = new Map<string, ValidationError[]>();
  for (const err of errors) {
    const list = byCategory.get(err.category) || [];
    list.push(err);
    byCategory.set(err.category, list);
  }

  for (const [category, categoryErrors] of byCategory) {
    const blocking = categoryErrors.some(e => e.blocking);
    items.push({
      priority: blocking ? 1 : 2,
      action: categoryErrors[0].fix.action,
      paths: categoryErrors.map(e => e.location.jsonPath),
      errorIds: categoryErrors.map(e => e.id),
      effort: categoryErrors.length > 5 ? 'medium' : 'small',
    });
  }

  return items.sort((a, b) => a.priority - b.priority);
}

function generateAISummary(
  errors: ValidationError[],
  blocking: number,
  nonBlocking: number
): { oneLine: string; priorityActions: string[]; references: string[] } {

  if (errors.length === 0) {
    return {
      oneLine: 'Contract is valid, no issues found.',
      priorityActions: [],
      references: [],
    };
  }

  const criticalErrors = errors.filter(e => e.blocking);
  const oneLine = criticalErrors.length > 0
    ? `${blocking} blocking errors: ${criticalErrors.slice(0, 2).map(e => e.message).join('; ')}`
    : `${nonBlocking} warnings found, contract will render.`;

  const priorityActions = errors
    .slice(0, 5)
    .map(e => `${e.id}: ${e.fix.action} at ${e.location.jsonPath}`);

  const references = [...new Set(errors.flatMap(e => e.fix.refs))].slice(0, 5);

  return { oneLine, priorityActions, references };
}
