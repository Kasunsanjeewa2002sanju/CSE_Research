/**
 * Hardcoded Domain Data Guard (Rule FR1 & FR3 Checker)
 *
 * Scans `src/` to ensure no domain data, mock objects, or test fixtures
 * are hardcoded inside production frontend source code.
 *
 * Fails the build (exit code 1) if any violation is found.
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface Violation {
  file: string;
  line: number;
  rule: string;
  match: string;
  description: string;
}

const SRC_DIR = path.resolve(__dirname, '../src');

// Regex patterns indicating hardcoded domain data or mock fixtures
const PATTERNS: Array<{ regex: RegExp; rule: string; description: string }> = [
  {
    regex: /(?:import|from)\s+['"][^'"]*tests\/[^'"]*['"]/g,
    rule: 'FR3: NO MOCK DATA IN src/',
    description: 'Importing from tests/ or test fixtures inside src/ is forbidden.',
  },
  {
    regex:
      /\b(?:const|let|var)\s+(?:mock[A-Z0-9_]|MOCK_|fake[A-Z0-9_]|dummy[A-Z0-9_])[a-zA-Z0-9_]*\s*=/g,
    rule: 'FR3: NO MOCK DATA IN src/',
    description: 'Mock data declarations (mock*, MOCK_*, fake*, dummy*) are forbidden in src/.',
  },
  {
    regex: /\b(?:sampleSize|sample_size|sampleCount|sample_count)\s*:\s*\d+/g,
    rule: 'FR1: NO HARDCODED DOMAIN DATA',
    description: 'Sample size (n) must come from the backend API response, not a hardcoded number.',
  },
  {
    regex:
      /\b(?:directionalAccuracy|directional_accuracy|balancedAccuracy|balanced_accuracy)\s*:\s*\d+(?:\.\d+)?/g,
    rule: 'FR1: NO HARDCODED DOMAIN DATA',
    description: 'Model accuracy metrics must come from the backend API, not hardcoded numbers.',
  },
  {
    regex: /\b(?:rSquared|r_squared|r2|rmse|mae)\s*:\s*-?\d+(?:\.\d+)?/g,
    rule: 'FR1: NO HARDCODED DOMAIN DATA',
    description: 'Statistical metrics (R², RMSE, MAE) must come from the backend API.',
  },
  {
    regex: /['"](?:CatBoostRegressor|LGBMRegressor|RidgeRegression|MultitaskLinear)['"]/g,
    rule: 'FR1: NO HARDCODED DOMAIN DATA',
    description:
      'Specific model names in data arrays must come from API enums or API model catalog.',
  },
  {
    regex: /['"](?:2015-01-08|2019-11-16|2024-09-21|2020-08-05|2010-01-26)['"]/g,
    rule: 'FR1: NO HARDCODED DOMAIN DATA',
    description: 'Hardcoded specific historical election dates in source code are forbidden.',
  },
];

function scanDirectory(dir: string, violations: Violation[]): void {
  if (!fs.existsSync(dir)) return;

  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      scanDirectory(fullPath, violations);
    } else if (entry.isFile() && /\.(ts|tsx|js|jsx)$/.test(entry.name)) {
      scanFile(fullPath, violations);
    }
  }
}

function scanFile(filePath: string, violations: Violation[]): void {
  const content = fs.readFileSync(filePath, 'utf-8');
  const lines = content.split('\n');

  for (let i = 0; i < lines.length; i++) {
    const lineText = lines[i];

    // Skip comments
    const trimmed = lineText.trim();
    if (trimmed.startsWith('//') || trimmed.startsWith('*') || trimmed.startsWith('/*')) {
      continue;
    }

    for (const pattern of PATTERNS) {
      pattern.regex.lastIndex = 0;
      let match: RegExpExecArray | null;

      while ((match = pattern.regex.exec(lineText)) !== null) {
        violations.push({
          file: path.relative(path.resolve(__dirname, '..'), filePath),
          line: i + 1,
          rule: pattern.rule,
          match: match[0],
          description: pattern.description,
        });
      }
    }
  }
}

function main(): void {
  console.log('----------------------------------------------------');
  console.log('Running Hardcoding & Mock Data Scanner (FR1 & FR3)...');
  console.log(`Target: ${SRC_DIR}`);
  console.log('----------------------------------------------------');

  const violations: Violation[] = [];
  scanDirectory(SRC_DIR, violations);

  if (violations.length > 0) {
    console.error(
      `\x1b[31m[ERROR] Found ${violations.length} hardcoding violation(s) in src/:\x1b[0m\n`
    );
    for (const v of violations) {
      console.error(`  \x1b[33m${v.file}:${v.line}\x1b[0m - \x1b[1m${v.rule}\x1b[0m`);
      console.error(`    Found: "${v.match}"`);
      console.error(`    Reason: ${v.description}\n`);
    }
    console.error('\x1b[31mBuild aborted due to Rule FR1 / FR3 violations.\x1b[0m');
    process.exit(1);
  }

  console.log('\x1b[32m[PASS] Zero hardcoded domain data or mock fixtures found in src/.\x1b[0m\n');
}

main();
