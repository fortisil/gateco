/**
 * Social Media Calendar Validation Script
 *
 * Validates calendar JSON files against schema and content rules.
 *
 * Usage:
 *   npx tsx scripts/social/validate-calendar.ts --all
 *   npx tsx scripts/social/validate-calendar.ts 2026-05.json
 *
 * Exit codes:
 *   0 - All validations passed
 *   1 - Validation errors found
 */

import * as fs from 'fs';
import * as path from 'path';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

const CALENDAR_DIR = path.join(__dirname, '../../content/social/calendar');
const SCHEMA_PATH = path.join(CALENDAR_DIR, 'schema.json');

// Platform-specific character limits
const CHAR_LIMITS: Record<string, number> = {
  twitter: 280,
  linkedin: 3000,
  youtube: 5000,
};

// Content pillar distribution targets (as percentages)
const PILLAR_TARGETS: Record<string, number> = {
  'security-gap': 40,
  'technical-education': 30,
  'industry-compliance': 20,
  'product-company': 10,
};

interface ValidationResult {
  file: string;
  valid: boolean;
  errors: string[];
  warnings: string[];
  stats: {
    totalEntries: number;
    byPlatform: Record<string, number>;
    byPillar: Record<string, number>;
    byStatus: Record<string, number>;
  };
}

interface CalendarEntry {
  id: string;
  platform: string;
  scheduledDate: string;
  scheduledTime?: string;
  contentType: string;
  pillar: string;
  status: string;
  content?: {
    text?: string;
    thread?: string[];
    headline?: string;
    cta?: string;
    link?: string;
    hashtags?: string[];
  };
  targeting?: {
    persona?: string;
    industry?: string[];
  };
  notes?: string;
}

interface Calendar {
  month: number;
  year: number;
  entries: CalendarEntry[];
}

function validateCalendarFile(filePath: string): ValidationResult {
  const result: ValidationResult = {
    file: path.basename(filePath),
    valid: true,
    errors: [],
    warnings: [],
    stats: {
      totalEntries: 0,
      byPlatform: {},
      byPillar: {},
      byStatus: {},
    },
  };

  // Read and parse file
  let calendar: Calendar;
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    calendar = JSON.parse(content) as Calendar;
  } catch (e) {
    result.valid = false;
    result.errors.push(`Invalid JSON: ${(e as Error).message}`);
    return result;
  }

  // Schema validation
  try {
    const schema = JSON.parse(fs.readFileSync(SCHEMA_PATH, 'utf-8'));
    const ajv = new Ajv({ allErrors: true });
    addFormats(ajv);
    const validate = ajv.compile(schema);

    if (!validate(calendar)) {
      result.valid = false;
      validate.errors?.forEach((err) => {
        result.errors.push(`Schema error at ${err.instancePath}: ${err.message}`);
      });
    }
  } catch (e) {
    result.warnings.push(`Could not load schema for validation: ${(e as Error).message}`);
  }

  // Track IDs for uniqueness check
  const seenIds = new Set<string>();

  // Track scheduling conflicts
  const scheduleMap = new Map<string, string>();

  // Content validation
  for (const entry of calendar.entries || []) {
    const entryId = entry.id || 'unknown';

    // Update stats
    result.stats.totalEntries++;
    result.stats.byPlatform[entry.platform] = (result.stats.byPlatform[entry.platform] || 0) + 1;
    result.stats.byPillar[entry.pillar] = (result.stats.byPillar[entry.pillar] || 0) + 1;
    result.stats.byStatus[entry.status] = (result.stats.byStatus[entry.status] || 0) + 1;

    // Check ID uniqueness
    if (seenIds.has(entryId)) {
      result.errors.push(`Entry ${entryId}: Duplicate ID`);
      result.valid = false;
    }
    seenIds.add(entryId);

    // Check scheduling conflicts (same platform, same date/time)
    if (entry.scheduledDate && entry.scheduledTime) {
      const scheduleKey = `${entry.platform}-${entry.scheduledDate}-${entry.scheduledTime}`;
      if (scheduleMap.has(scheduleKey)) {
        result.warnings.push(
          `Entry ${entryId}: Scheduling conflict with ${scheduleMap.get(scheduleKey)} (same platform/date/time)`
        );
      }
      scheduleMap.set(scheduleKey, entryId);
    }

    // Check character limits for text content
    const limit = CHAR_LIMITS[entry.platform];
    if (entry.platform === 'twitter' && entry.content?.text) {
      if (entry.content.text.length > limit) {
        result.errors.push(
          `Entry ${entryId}: Twitter text exceeds ${limit} chars (${entry.content.text.length})`
        );
        result.valid = false;
      }
    }

    // Check thread tweets
    if (entry.content?.thread) {
      entry.content.thread.forEach((tweet: string, i: number) => {
        if (tweet.length > 280) {
          result.errors.push(
            `Entry ${entryId}: Thread tweet ${i + 1} exceeds 280 chars (${tweet.length})`
          );
          result.valid = false;
        }
      });
    }

    // Check hashtag count
    const hashtags = entry.content?.hashtags || [];
    if (hashtags.length > 5) {
      result.warnings.push(`Entry ${entryId}: More than 5 hashtags (${hashtags.length})`);
    }

    // Check hashtag format
    hashtags.forEach((tag: string) => {
      if (!tag.startsWith('#')) {
        result.errors.push(`Entry ${entryId}: Hashtag "${tag}" must start with #`);
        result.valid = false;
      }
    });

    // Check for placeholder text
    const placeholders = ['TODO', 'TBD', 'PLACEHOLDER', 'Lorem ipsum', '[insert', 'XXX', 'FIXME'];
    const textToCheck = JSON.stringify(entry.content || {});
    placeholders.forEach((p) => {
      if (textToCheck.toUpperCase().includes(p.toUpperCase())) {
        result.warnings.push(`Entry ${entryId}: Contains placeholder text "${p}"`);
      }
    });

    // Check scheduled date is in the future (for non-published posts)
    const scheduledDate = new Date(entry.scheduledDate);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    if (scheduledDate < today && entry.status !== 'published') {
      result.warnings.push(`Entry ${entryId}: Scheduled date is in the past`);
    }

    // Check for missing CTA on product posts
    if (entry.contentType === 'product-highlight' && !entry.content?.cta) {
      result.warnings.push(`Entry ${entryId}: Product highlight missing CTA`);
    }

    // Check for missing link on posts with CTA
    if (entry.content?.cta && !entry.content?.link) {
      result.warnings.push(`Entry ${entryId}: Has CTA but no link`);
    }

    // Check UTM parameters in links
    if (entry.content?.link && !entry.content.link.includes('utm_')) {
      result.warnings.push(`Entry ${entryId}: Link missing UTM parameters`);
    }

    // Check weekend scheduling for B2B content
    const dayOfWeek = scheduledDate.getDay();
    if (dayOfWeek === 0 || dayOfWeek === 6) {
      result.warnings.push(`Entry ${entryId}: Scheduled on weekend (${dayOfWeek === 0 ? 'Sunday' : 'Saturday'})`);
    }
  }

  // Check pillar distribution
  const totalEntries = result.stats.totalEntries;
  if (totalEntries > 0) {
    for (const [pillar, target] of Object.entries(PILLAR_TARGETS)) {
      const actual = ((result.stats.byPillar[pillar] || 0) / totalEntries) * 100;
      const deviation = Math.abs(actual - target);
      if (deviation > 15) {
        result.warnings.push(
          `Pillar "${pillar}" distribution is ${actual.toFixed(1)}% (target: ${target}%, deviation: ${deviation.toFixed(1)}%)`
        );
      }
    }
  }

  return result;
}

function printResult(result: ValidationResult): void {
  console.log(`📄 ${result.file}`);
  console.log(`   Total entries: ${result.stats.totalEntries}`);

  if (Object.keys(result.stats.byPlatform).length > 0) {
    console.log(`   Platforms: ${Object.entries(result.stats.byPlatform).map(([k, v]) => `${k}(${v})`).join(', ')}`);
  }

  if (Object.keys(result.stats.byPillar).length > 0) {
    console.log(`   Pillars: ${Object.entries(result.stats.byPillar).map(([k, v]) => `${k}(${v})`).join(', ')}`);
  }

  if (result.errors.length > 0) {
    console.log('   ❌ Errors:');
    result.errors.forEach((e) => console.log(`      - ${e}`));
  }

  if (result.warnings.length > 0) {
    console.log('   ⚠️  Warnings:');
    result.warnings.forEach((w) => console.log(`      - ${w}`));
  }

  if (result.valid && result.warnings.length === 0) {
    console.log('   ✅ Valid (no errors or warnings)');
  } else if (result.valid) {
    console.log('   ✅ Valid (with warnings)');
  } else {
    console.log('   ❌ Invalid');
  }

  console.log('');
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const validateAll = args.includes('--all');
  const verbose = args.includes('--verbose') || args.includes('-v');
  const specificFile = args.find((a) => !a.startsWith('--') && !a.startsWith('-'));

  let files: string[] = [];

  if (validateAll || !specificFile) {
    try {
      files = fs
        .readdirSync(CALENDAR_DIR)
        .filter((f) => f.endsWith('.json') && f !== 'schema.json' && f !== 'template.json')
        .map((f) => path.join(CALENDAR_DIR, f));
    } catch (e) {
      console.error(`Error reading calendar directory: ${(e as Error).message}`);
      process.exit(1);
    }
  } else {
    const filePath = path.isAbsolute(specificFile)
      ? specificFile
      : path.join(CALENDAR_DIR, specificFile);
    if (!fs.existsSync(filePath)) {
      console.error(`File not found: ${filePath}`);
      process.exit(1);
    }
    files = [filePath];
  }

  if (files.length === 0) {
    console.log('No calendar files found to validate.');
    process.exit(0);
  }

  console.log(`\n🔍 Validating ${files.length} calendar file(s)...\n`);

  let allValid = true;
  let totalErrors = 0;
  let totalWarnings = 0;
  let totalEntries = 0;

  for (const file of files) {
    const result = validateCalendarFile(file);
    printResult(result);

    if (!result.valid) {
      allValid = false;
    }
    totalErrors += result.errors.length;
    totalWarnings += result.warnings.length;
    totalEntries += result.stats.totalEntries;
  }

  // Print summary
  console.log('═'.repeat(50));
  console.log(`📊 Summary`);
  console.log(`   Files validated: ${files.length}`);
  console.log(`   Total entries: ${totalEntries}`);
  console.log(`   Errors: ${totalErrors}`);
  console.log(`   Warnings: ${totalWarnings}`);
  console.log(`   Status: ${allValid ? '✅ All valid' : '❌ Validation failed'}`);
  console.log('');

  process.exit(allValid ? 0 : 1);
}

main().catch((e) => {
  console.error('Validation failed:', e);
  process.exit(1);
});
