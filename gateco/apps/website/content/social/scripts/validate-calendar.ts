#!/usr/bin/env npx tsx
/**
 * Calendar Validation Script
 *
 * Validates social media calendar JSON files against the schema
 * and performs additional content checks.
 *
 * Usage:
 *   npx tsx validate-calendar.ts              # Validate all calendars
 *   npx tsx validate-calendar.ts 2026-07.json # Validate specific file
 *   npx tsx validate-calendar.ts --all        # Validate with detailed output
 */

import Ajv from 'ajv';
import addFormats from 'ajv-formats';
import { readFileSync, readdirSync, existsSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Colors for terminal output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

interface CalendarEntry {
  id: string;
  platform: 'linkedin' | 'twitter' | 'youtube';
  scheduledDate: string;
  scheduledTime?: string;
  contentType: string;
  pillar: string;
  status: string;
  content?: {
    text?: string;
    thread?: string[];
    hashtags?: string[];
    link?: string;
  };
  notes?: string;
}

interface Calendar {
  month: number;
  year: number;
  entries: CalendarEntry[];
}

interface ValidationResult {
  file: string;
  valid: boolean;
  schemaErrors: string[];
  contentWarnings: string[];
  stats: {
    totalEntries: number;
    byPlatform: Record<string, number>;
    byPillar: Record<string, number>;
    byStatus: Record<string, number>;
  };
}

// Target pillar distribution
const PILLAR_TARGETS = {
  'security-gap': 0.4,
  'technical-education': 0.3,
  'industry-compliance': 0.2,
  'product-company': 0.1,
};

// Platform character limits
const CHAR_LIMITS = {
  linkedin: 3000,
  twitter: 280,
  youtube: 5000, // Description
};

function log(color: keyof typeof colors, message: string): void {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function loadSchema(): object {
  const schemaPath = join(__dirname, '..', 'calendar', 'schema.json');
  return JSON.parse(readFileSync(schemaPath, 'utf-8'));
}

function validateSchema(calendar: unknown, schema: object): string[] {
  const ajv = new Ajv({ allErrors: true, strict: false });
  addFormats(ajv);

  const validate = ajv.compile(schema);
  const valid = validate(calendar);

  if (!valid && validate.errors) {
    return validate.errors.map(err =>
      `${err.instancePath || 'root'}: ${err.message}`
    );
  }

  return [];
}

function checkContent(calendar: Calendar): string[] {
  const warnings: string[] = [];
  const seenIds = new Set<string>();

  for (const entry of calendar.entries) {
    // Check for duplicate IDs
    if (seenIds.has(entry.id)) {
      warnings.push(`Duplicate ID: ${entry.id}`);
    }
    seenIds.add(entry.id);

    // Check character limits
    if (entry.content?.text) {
      const limit = CHAR_LIMITS[entry.platform];
      if (entry.content.text.length > limit) {
        warnings.push(
          `${entry.id}: Text exceeds ${entry.platform} limit ` +
          `(${entry.content.text.length}/${limit})`
        );
      }
    }

    // Check thread tweet lengths
    if (entry.content?.thread) {
      entry.content.thread.forEach((tweet, i) => {
        if (tweet.length > 280) {
          warnings.push(
            `${entry.id}: Tweet ${i + 1} exceeds 280 chars (${tweet.length})`
          );
        }
      });
    }

    // Check hashtag count
    if (entry.content?.hashtags) {
      const maxHashtags = entry.platform === 'linkedin' ? 5 : 2;
      if (entry.content.hashtags.length > maxHashtags) {
        warnings.push(
          `${entry.id}: Too many hashtags for ${entry.platform} ` +
          `(${entry.content.hashtags.length}/${maxHashtags})`
        );
      }
    }

    // Check for UTM parameters in links
    if (entry.content?.link && !entry.content.link.includes('utm_')) {
      warnings.push(`${entry.id}: Link missing UTM parameters`);
    }

    // Validate date format
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/;
    if (!dateRegex.test(entry.scheduledDate)) {
      warnings.push(`${entry.id}: Invalid date format (use YYYY-MM-DD)`);
    }

    // Validate time format
    if (entry.scheduledTime) {
      const timeRegex = /^[0-2][0-9]:[0-5][0-9]$/;
      if (!timeRegex.test(entry.scheduledTime)) {
        warnings.push(`${entry.id}: Invalid time format (use HH:MM)`);
      }
    }
  }

  return warnings;
}

function calculateStats(calendar: Calendar): ValidationResult['stats'] {
  const stats = {
    totalEntries: calendar.entries.length,
    byPlatform: {} as Record<string, number>,
    byPillar: {} as Record<string, number>,
    byStatus: {} as Record<string, number>,
  };

  for (const entry of calendar.entries) {
    stats.byPlatform[entry.platform] = (stats.byPlatform[entry.platform] || 0) + 1;
    stats.byPillar[entry.pillar] = (stats.byPillar[entry.pillar] || 0) + 1;
    stats.byStatus[entry.status] = (stats.byStatus[entry.status] || 0) + 1;
  }

  return stats;
}

function checkPillarDistribution(stats: ValidationResult['stats']): string[] {
  const warnings: string[] = [];
  const total = stats.totalEntries;

  if (total === 0) return warnings;

  for (const [pillar, target] of Object.entries(PILLAR_TARGETS)) {
    const actual = (stats.byPillar[pillar] || 0) / total;
    const diff = Math.abs(actual - target);

    if (diff > 0.15) { // More than 15% off target
      warnings.push(
        `Pillar "${pillar}": ${(actual * 100).toFixed(0)}% ` +
        `(target: ${(target * 100).toFixed(0)}%)`
      );
    }
  }

  return warnings;
}

function validateFile(filePath: string, schema: object): ValidationResult {
  const content = readFileSync(filePath, 'utf-8');
  let calendar: Calendar;

  try {
    calendar = JSON.parse(content);
  } catch (e) {
    return {
      file: filePath,
      valid: false,
      schemaErrors: [`Invalid JSON: ${(e as Error).message}`],
      contentWarnings: [],
      stats: { totalEntries: 0, byPlatform: {}, byPillar: {}, byStatus: {} },
    };
  }

  const schemaErrors = validateSchema(calendar, schema);
  const contentWarnings = checkContent(calendar);
  const stats = calculateStats(calendar);
  const distributionWarnings = checkPillarDistribution(stats);

  return {
    file: filePath,
    valid: schemaErrors.length === 0,
    schemaErrors,
    contentWarnings: [...contentWarnings, ...distributionWarnings],
    stats,
  };
}

function printResult(result: ValidationResult, verbose: boolean): void {
  const fileName = result.file.split('/').pop();

  if (result.valid && result.contentWarnings.length === 0) {
    log('green', `✓ ${fileName}`);
  } else if (result.valid) {
    log('yellow', `⚠ ${fileName} (warnings)`);
  } else {
    log('red', `✗ ${fileName} (invalid)`);
  }

  if (result.schemaErrors.length > 0) {
    log('red', '  Schema errors:');
    result.schemaErrors.forEach(err => log('red', `    - ${err}`));
  }

  if (result.contentWarnings.length > 0 && verbose) {
    log('yellow', '  Warnings:');
    result.contentWarnings.forEach(warn => log('yellow', `    - ${warn}`));
  }

  if (verbose) {
    log('cyan', '  Stats:');
    log('cyan', `    Total entries: ${result.stats.totalEntries}`);
    log('cyan', `    By platform: ${JSON.stringify(result.stats.byPlatform)}`);
    log('cyan', `    By pillar: ${JSON.stringify(result.stats.byPillar)}`);
    log('cyan', `    By status: ${JSON.stringify(result.stats.byStatus)}`);
  }
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const verbose = args.includes('--all') || args.includes('-v');
  const specificFile = args.find(arg => arg.endsWith('.json'));

  const calendarDir = join(__dirname, '..', 'calendar');
  const schema = loadSchema();

  let files: string[];

  if (specificFile) {
    const filePath = join(calendarDir, specificFile);
    if (!existsSync(filePath)) {
      log('red', `File not found: ${specificFile}`);
      process.exit(1);
    }
    files = [filePath];
  } else {
    files = readdirSync(calendarDir)
      .filter(f => f.match(/^\d{4}-\d{2}\.json$/))
      .map(f => join(calendarDir, f))
      .sort();
  }

  log('blue', `\nValidating ${files.length} calendar file(s)...\n`);

  const results = files.map(f => validateFile(f, schema));

  results.forEach(r => printResult(r, verbose));

  const invalidCount = results.filter(r => !r.valid).length;
  const warningCount = results.filter(r => r.contentWarnings.length > 0).length;

  console.log('');

  if (invalidCount > 0) {
    log('red', `${invalidCount} file(s) failed validation`);
    process.exit(1);
  } else if (warningCount > 0) {
    log('yellow', `All files valid, ${warningCount} with warnings`);
    process.exit(0);
  } else {
    log('green', 'All files valid');
    process.exit(0);
  }
}

main().catch(console.error);
