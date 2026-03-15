#!/usr/bin/env npx tsx
/**
 * Calendar Analysis Script
 *
 * Analyzes social media calendar data to provide insights on
 * content distribution, scheduling patterns, and pillar balance.
 *
 * Usage:
 *   npx tsx analyze-calendar.ts              # Analyze all calendars
 *   npx tsx analyze-calendar.ts 2026-07.json # Analyze specific month
 */

import { readFileSync, readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

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
  };
  targeting?: {
    persona?: string;
    industry?: string[];
  };
}

interface Calendar {
  month: number;
  year: number;
  entries: CalendarEntry[];
}

interface AnalysisResult {
  period: string;
  totalPosts: number;
  platforms: Record<string, { count: number; percentage: number }>;
  pillars: Record<string, { count: number; percentage: number; target: number }>;
  contentTypes: Record<string, number>;
  personas: Record<string, number>;
  industries: Record<string, number>;
  weekdayDistribution: Record<string, number>;
  timeDistribution: Record<string, number>;
  averageContentLength: Record<string, number>;
  hashtagUsage: {
    total: number;
    unique: Set<string>;
    topHashtags: [string, number][];
  };
}

const PILLAR_TARGETS: Record<string, number> = {
  'security-gap': 0.4,
  'technical-education': 0.3,
  'industry-compliance': 0.2,
  'product-company': 0.1,
};

const WEEKDAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

function loadCalendars(files: string[]): Calendar[] {
  return files.map(file => {
    const content = readFileSync(file, 'utf-8');
    return JSON.parse(content) as Calendar;
  });
}

function analyze(calendars: Calendar[]): AnalysisResult {
  const entries = calendars.flatMap(c => c.entries);

  // Basic counts
  const platforms: Record<string, number> = {};
  const pillars: Record<string, number> = {};
  const contentTypes: Record<string, number> = {};
  const personas: Record<string, number> = {};
  const industries: Record<string, number> = {};
  const weekdays: Record<string, number> = {};
  const hours: Record<string, number> = {};
  const contentLengths: Record<string, number[]> = {};
  const allHashtags: string[] = [];

  for (const entry of entries) {
    // Platform
    platforms[entry.platform] = (platforms[entry.platform] || 0) + 1;

    // Pillar
    pillars[entry.pillar] = (pillars[entry.pillar] || 0) + 1;

    // Content type
    contentTypes[entry.contentType] = (contentTypes[entry.contentType] || 0) + 1;

    // Persona
    if (entry.targeting?.persona) {
      personas[entry.targeting.persona] = (personas[entry.targeting.persona] || 0) + 1;
    }

    // Industries
    if (entry.targeting?.industry) {
      for (const industry of entry.targeting.industry) {
        industries[industry] = (industries[industry] || 0) + 1;
      }
    }

    // Weekday
    const date = new Date(entry.scheduledDate);
    const weekday = WEEKDAYS[date.getDay()];
    weekdays[weekday] = (weekdays[weekday] || 0) + 1;

    // Hour
    if (entry.scheduledTime) {
      const hour = entry.scheduledTime.split(':')[0];
      hours[hour] = (hours[hour] || 0) + 1;
    }

    // Content length
    let length = 0;
    if (entry.content?.text) {
      length = entry.content.text.length;
    } else if (entry.content?.thread) {
      length = entry.content.thread.reduce((sum, t) => sum + t.length, 0);
    }
    if (length > 0) {
      if (!contentLengths[entry.platform]) {
        contentLengths[entry.platform] = [];
      }
      contentLengths[entry.platform].push(length);
    }

    // Hashtags
    if (entry.content?.hashtags) {
      allHashtags.push(...entry.content.hashtags);
    }
  }

  // Calculate percentages and format results
  const total = entries.length;

  const platformResults: Record<string, { count: number; percentage: number }> = {};
  for (const [platform, count] of Object.entries(platforms)) {
    platformResults[platform] = {
      count,
      percentage: Math.round((count / total) * 100),
    };
  }

  const pillarResults: Record<string, { count: number; percentage: number; target: number }> = {};
  for (const [pillar, count] of Object.entries(pillars)) {
    pillarResults[pillar] = {
      count,
      percentage: Math.round((count / total) * 100),
      target: Math.round((PILLAR_TARGETS[pillar] || 0) * 100),
    };
  }

  // Average content lengths
  const avgLengths: Record<string, number> = {};
  for (const [platform, lengths] of Object.entries(contentLengths)) {
    avgLengths[platform] = Math.round(
      lengths.reduce((sum, l) => sum + l, 0) / lengths.length
    );
  }

  // Hashtag analysis
  const hashtagCounts: Record<string, number> = {};
  for (const tag of allHashtags) {
    hashtagCounts[tag] = (hashtagCounts[tag] || 0) + 1;
  }
  const topHashtags = Object.entries(hashtagCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  // Period string
  const months = calendars.map(c => `${c.year}-${String(c.month).padStart(2, '0')}`);
  const period = months.length === 1
    ? months[0]
    : `${months[0]} to ${months[months.length - 1]}`;

  return {
    period,
    totalPosts: total,
    platforms: platformResults,
    pillars: pillarResults,
    contentTypes,
    personas,
    industries,
    weekdayDistribution: weekdays,
    timeDistribution: hours,
    averageContentLength: avgLengths,
    hashtagUsage: {
      total: allHashtags.length,
      unique: new Set(allHashtags),
      topHashtags,
    },
  };
}

function printReport(result: AnalysisResult): void {
  console.log('\n' + '='.repeat(60));
  console.log(`SOCIAL CALENDAR ANALYSIS: ${result.period}`);
  console.log('='.repeat(60));

  console.log(`\nTotal Posts: ${result.totalPosts}`);

  console.log('\n--- Platform Distribution ---');
  for (const [platform, data] of Object.entries(result.platforms)) {
    console.log(`  ${platform}: ${data.count} posts (${data.percentage}%)`);
  }

  console.log('\n--- Pillar Distribution ---');
  for (const [pillar, data] of Object.entries(result.pillars)) {
    const diff = data.percentage - data.target;
    const indicator = diff > 5 ? '(+)' : diff < -5 ? '(-)' : '';
    console.log(
      `  ${pillar}: ${data.count} posts (${data.percentage}% vs ${data.target}% target) ${indicator}`
    );
  }

  console.log('\n--- Content Types ---');
  const sortedTypes = Object.entries(result.contentTypes).sort((a, b) => b[1] - a[1]);
  for (const [type, count] of sortedTypes) {
    console.log(`  ${type}: ${count}`);
  }

  console.log('\n--- Target Personas ---');
  const sortedPersonas = Object.entries(result.personas).sort((a, b) => b[1] - a[1]);
  for (const [persona, count] of sortedPersonas) {
    console.log(`  ${persona}: ${count}`);
  }

  if (Object.keys(result.industries).length > 0) {
    console.log('\n--- Target Industries ---');
    const sortedIndustries = Object.entries(result.industries).sort((a, b) => b[1] - a[1]);
    for (const [industry, count] of sortedIndustries) {
      console.log(`  ${industry}: ${count}`);
    }
  }

  console.log('\n--- Weekday Distribution ---');
  for (const day of WEEKDAYS) {
    const count = result.weekdayDistribution[day] || 0;
    const bar = '#'.repeat(Math.round(count / 2));
    console.log(`  ${day.padEnd(10)}: ${bar} (${count})`);
  }

  console.log('\n--- Posting Times ---');
  const sortedHours = Object.entries(result.timeDistribution)
    .sort((a, b) => a[0].localeCompare(b[0]));
  for (const [hour, count] of sortedHours) {
    console.log(`  ${hour}:00 - ${count} posts`);
  }

  console.log('\n--- Average Content Length ---');
  for (const [platform, length] of Object.entries(result.averageContentLength)) {
    console.log(`  ${platform}: ${length} characters`);
  }

  console.log('\n--- Top Hashtags ---');
  for (const [hashtag, count] of result.hashtagUsage.topHashtags) {
    console.log(`  ${hashtag}: ${count}`);
  }
  console.log(`  (${result.hashtagUsage.unique.size} unique hashtags total)`);

  console.log('\n' + '='.repeat(60));
}

async function main(): Promise<void> {
  const args = process.argv.slice(2);
  const specificFile = args.find(arg => arg.endsWith('.json'));

  const calendarDir = join(__dirname, '..', 'calendar');

  let files: string[];

  if (specificFile) {
    files = [join(calendarDir, specificFile)];
  } else {
    files = readdirSync(calendarDir)
      .filter(f => f.match(/^\d{4}-\d{2}\.json$/))
      .map(f => join(calendarDir, f))
      .sort();
  }

  const calendars = loadCalendars(files);
  const result = analyze(calendars);
  printReport(result);
}

main().catch(console.error);
