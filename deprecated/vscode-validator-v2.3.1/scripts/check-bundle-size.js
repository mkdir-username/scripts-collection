#!/usr/bin/env node

/**
 * Bundle Size Checker v1.0.0
 * Проверка размера собранного бандла
 */

import { readdir, stat } from 'fs/promises';
import { join } from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const DIST_DIR = join(__dirname, '..', 'dist');
const MAX_SIZE_MB = 5;
const WARN_SIZE_MB = 3;

const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  green: '\x1b[32m',
  blue: '\x1b[34m',
};

async function getDirectorySize(dirPath) {
  let totalSize = 0;

  try {
    const files = await readdir(dirPath);

    for (const file of files) {
      const filePath = join(dirPath, file);
      const stats = await stat(filePath);

      if (stats.isDirectory()) {
        totalSize += await getDirectorySize(filePath);
      } else {
        totalSize += stats.size;
      }
    }
  } catch (error) {
    console.error(`${colors.red}Error reading directory:${colors.reset}`, error.message);
  }

  return totalSize;
}

function formatSize(bytes) {
  const mb = bytes / (1024 * 1024);
  return mb.toFixed(2);
}

async function checkBundleSize() {
  console.log(`${colors.blue}Checking bundle size...${colors.reset}\n`);

  try {
    const totalSize = await getDirectorySize(DIST_DIR);
    const sizeMB = formatSize(totalSize);

    console.log(`Bundle size: ${sizeMB} MB`);
    console.log(`Warning threshold: ${WARN_SIZE_MB} MB`);
    console.log(`Maximum threshold: ${MAX_SIZE_MB} MB\n`);

    if (parseFloat(sizeMB) > MAX_SIZE_MB) {
      console.error(
        `${colors.red}ERROR: Bundle size exceeds maximum threshold!${colors.reset}`
      );
      console.error(
        `${colors.red}Bundle: ${sizeMB} MB > ${MAX_SIZE_MB} MB${colors.reset}`
      );
      process.exit(1);
    } else if (parseFloat(sizeMB) > WARN_SIZE_MB) {
      console.warn(
        `${colors.yellow}WARNING: Bundle size exceeds warning threshold${colors.reset}`
      );
      console.warn(
        `${colors.yellow}Bundle: ${sizeMB} MB > ${WARN_SIZE_MB} MB${colors.reset}`
      );
    } else {
      console.log(
        `${colors.green}Bundle size is acceptable${colors.reset}`
      );
    }
  } catch (error) {
    console.error(
      `${colors.red}Error checking bundle size:${colors.reset}`,
      error.message
    );
    process.exit(1);
  }
}

checkBundleSize();
