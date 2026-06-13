#!/usr/bin/env node
// @ts-nocheck

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import yaml from 'js-yaml';

const cwd = process.cwd();
const manifestPath = process.env.COURSE_PACKS_MANIFEST ?? path.join(cwd, 'data', 'course-packs.yaml');
const repoDir = process.env.COURSE_PACKS_DIR ?? path.join(cwd, 'data', 'course-packs', 'repos');

const MODULE_TYPES = new Set(['coding', 'reading', 'quiz', 'test', 'drill']);
const LANGUAGES = new Set(['python', 'cpp']);

function safeId(id) {
  return id.trim().toLowerCase().replace(/[^a-z0-9._-]+/g, '__');
}

function usage(exitCode = 0) {
  console.log(`Course pack manager

Usage:
  npm run course:list
  npm run course:add -- <git-url-or-local-path> [--id owner/name] [--ref main]
  npm run course:update
  npm run course:validate

Environment:
  COURSE_PACKS_MANIFEST  Manifest path. Default: data/course-packs.yaml
  COURSE_PACKS_DIR       Git checkout directory. Default: data/course-packs/repos
`);
  process.exit(exitCode);
}

function parseArgs(argv) {
  const [command, ...rest] = argv;
  const opts = { _: [] };
  for (let i = 0; i < rest.length; i += 1) {
    const token = rest[i];
    if (!token.startsWith('--')) {
      opts._.push(token);
      continue;
    }
    const key = token.slice(2);
    const next = rest[i + 1];
    if (!next || next.startsWith('--')) {
      opts[key] = true;
    } else {
      opts[key] = next;
      i += 1;
    }
  }
  return { command, opts };
}

function readYaml(filePath, fallback) {
  if (!fs.existsSync(filePath)) return fallback;
  return yaml.load(fs.readFileSync(filePath, 'utf-8')) ?? fallback;
}

function writeManifest(manifest) {
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });
  fs.writeFileSync(
    manifestPath,
    `${yaml.dump(manifest, { lineWidth: 100, noRefs: true })}`,
    'utf-8'
  );
}

function readManifest() {
  const manifest = readYaml(manifestPath, { packs: [] });
  if (!Array.isArray(manifest.packs)) manifest.packs = [];
  return manifest;
}

function run(cmd, args, options = {}) {
  const result = spawnSync(cmd, args, {
    cwd,
    stdio: options.capture ? ['ignore', 'pipe', 'pipe'] : 'inherit',
    encoding: 'utf-8',
    windowsHide: true
  });
  if (result.status !== 0 && !options.allowFailure) {
    const detail = options.capture ? result.stderr || result.stdout : '';
    throw new Error(`${cmd} ${args.join(' ')} failed${detail ? `\n${detail}` : ''}`);
  }
  return result.stdout?.trim() ?? '';
}

function cloneAndCheckout(repo, ref, destination) {
  run('git', ['clone', repo, destination]);
  if (ref) run('git', ['-C', destination, 'checkout', ref]);
}

function inferId(source) {
  const cleaned = source.replace(/\\/g, '/').replace(/\/$/, '').replace(/\.git$/, '');
  const parts = cleaned.split(/[/:]/).filter(Boolean);
  const repo = parts.at(-1) ?? 'course-pack';
  const owner = parts.at(-2);
  return owner ? `${owner}/${repo}` : repo;
}

function packPath(pack) {
  if (pack.path) return path.isAbsolute(pack.path) ? pack.path : path.resolve(cwd, pack.path);
  return path.join(repoDir, safeId(pack.id));
}

function courseRootForPack(pack) {
  const checkout = packPath(pack);
  if (pack.coursesDir) {
    return path.isAbsolute(pack.coursesDir) ? pack.coursesDir : path.join(checkout, pack.coursesDir);
  }
  const nested = path.join(checkout, 'courses');
  return fs.existsSync(nested) ? nested : checkout;
}

function findTrackDirs(courseRoot) {
  if (!fs.existsSync(courseRoot)) return [];
  if (fs.existsSync(path.join(courseRoot, 'course.yaml'))) return [courseRoot];
  return fs
    .readdirSync(courseRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(courseRoot, entry.name))
    .filter((dir) => fs.existsSync(path.join(dir, 'course.yaml')));
}

function validateTrack(trackDir) {
  const issues = [];
  const warnings = [];
  const course = readYaml(path.join(trackDir, 'course.yaml'), null);
  if (!course || typeof course !== 'object') {
    issues.push(`missing or invalid course.yaml in ${trackDir}`);
    return { issues, warnings, slug: null };
  }
  for (const field of ['title', 'slug', 'description']) {
    if (!course[field]) issues.push(`${trackDir}: course.yaml missing "${field}"`);
  }

  const moduleDirs = fs
    .readdirSync(trackDir, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => path.join(trackDir, entry.name))
    .filter((dir) => fs.existsSync(path.join(dir, 'module.yaml')))
    .sort();

  if (moduleDirs.length === 0) warnings.push(`${course.slug ?? trackDir}: no module directories found`);
  const moduleSlugs = new Set();

  for (const moduleDir of moduleDirs) {
    const mod = readYaml(path.join(moduleDir, 'module.yaml'), null);
    if (!mod || typeof mod !== 'object') {
      issues.push(`${moduleDir}: invalid module.yaml`);
      continue;
    }
    const type = mod.type ?? 'coding';
    for (const field of ['title', 'slug']) {
      if (!mod[field]) issues.push(`${moduleDir}: module.yaml missing "${field}"`);
    }
    if (mod.slug) {
      if (moduleSlugs.has(mod.slug)) issues.push(`${course.slug}: duplicate module slug "${mod.slug}"`);
      moduleSlugs.add(mod.slug);
    }
    if (!MODULE_TYPES.has(type)) issues.push(`${moduleDir}: unsupported module type "${type}"`);
    if (!fs.existsSync(path.join(moduleDir, 'problem.md'))) {
      issues.push(`${moduleDir}: missing problem.md`);
    }

    if (type === 'coding') {
      const languages = Array.isArray(mod.languages) && mod.languages.length > 0 ? mod.languages : ['python'];
      for (const lang of languages) {
        if (!LANGUAGES.has(lang)) issues.push(`${moduleDir}: unsupported language "${lang}"`);
      }
      const hasStarter = languages.some((lang) => {
        const file = lang === 'cpp' ? 'cpp.cpp' : 'python.py';
        return fs.existsSync(path.join(moduleDir, 'starter', file));
      });
      if (!hasStarter) issues.push(`${moduleDir}: coding module needs starter code`);
      if (fs.existsSync(path.join(moduleDir, 'requirements.txt'))) {
        warnings.push(`${moduleDir}: requirements.txt will install code dependencies when run`);
      }
    } else {
      if (mod.languages || mod.defaultLanguage) {
        warnings.push(`${moduleDir}: non-coding module should omit languages/defaultLanguage`);
      }
      if (fs.existsSync(path.join(moduleDir, 'starter'))) {
        warnings.push(`${moduleDir}: non-coding module has starter/ directory; app ignores it`);
      }
    }

    if ((type === 'quiz' || type === 'test') && !fs.existsSync(path.join(moduleDir, 'quiz.yaml'))) {
      issues.push(`${moduleDir}: ${type} module missing quiz.yaml`);
    }
    if (type === 'drill' && !fs.existsSync(path.join(moduleDir, 'drill.yaml'))) {
      issues.push(`${moduleDir}: drill module missing drill.yaml`);
    }
  }

  return { issues, warnings, slug: course.slug ?? null };
}

function validateRoots(roots) {
  const allIssues = [];
  const allWarnings = [];
  const seenTrackSlugs = new Map();

  for (const root of roots) {
    const trackDirs = findTrackDirs(root);
    if (trackDirs.length === 0) {
      allIssues.push(`${root}: no tracks found. Expected course.yaml or child folders with course.yaml`);
      continue;
    }
    for (const trackDir of trackDirs) {
      const result = validateTrack(trackDir);
      allIssues.push(...result.issues);
      allWarnings.push(...result.warnings);
      if (result.slug) {
        if (seenTrackSlugs.has(result.slug)) {
          allIssues.push(`duplicate track slug "${result.slug}" in ${trackDir} and ${seenTrackSlugs.get(result.slug)}`);
        } else {
          seenTrackSlugs.set(result.slug, trackDir);
        }
      }
    }
  }

  return { issues: allIssues, warnings: allWarnings, trackCount: seenTrackSlugs.size };
}

function commandList() {
  const manifest = readManifest();
  console.log(`Manifest: ${manifestPath}`);
  if (manifest.packs.length === 0) {
    console.log('No course packs installed yet.');
    return;
  }
  for (const pack of manifest.packs) {
    const status = pack.enabled === false ? 'disabled' : 'enabled';
    const installed = fs.existsSync(packPath(pack)) ? 'installed' : 'missing';
    console.log(`- ${pack.id} (${status}, ${installed})`);
    if (pack.repo) console.log(`  repo: ${pack.repo}`);
    if (pack.ref) console.log(`  ref: ${pack.ref}`);
    console.log(`  path: ${packPath(pack)}`);
  }
}

function commandAdd(opts) {
  const source = opts._[0];
  if (!source) usage(1);
  const id = opts.id || inferId(source);
  const ref = opts.ref;
  const manifest = readManifest();
  if (manifest.packs.some((pack) => pack.id === id)) {
    throw new Error(`Pack "${id}" already exists in ${manifestPath}`);
  }

  let entry;
  if (fs.existsSync(source)) {
    entry = { id, path: path.resolve(source), enabled: opts.disabled ? false : true };
    if (opts.ref) entry.ref = opts.ref;
  } else {
    const destination = path.join(repoDir, safeId(id));
    if (fs.existsSync(destination)) throw new Error(`Destination already exists: ${destination}`);
    fs.mkdirSync(path.dirname(destination), { recursive: true });
    cloneAndCheckout(source, ref, destination);
    entry = { id, repo: source, enabled: opts.disabled ? false : true };
    if (ref) entry.ref = ref;
  }

  manifest.packs.push(entry);
  writeManifest(manifest);
  console.log(`Added course pack "${id}".`);
  commandValidate();
}

function commandUpdate() {
  const manifest = readManifest();
  for (const pack of manifest.packs) {
    if (pack.enabled === false) continue;
    if (!pack.repo) {
      console.log(`Skipping ${pack.id}: local path pack`);
      continue;
    }
    const checkout = packPath(pack);
    if (!fs.existsSync(checkout)) {
      fs.mkdirSync(path.dirname(checkout), { recursive: true });
      cloneAndCheckout(pack.repo, pack.ref, checkout);
      continue;
    }
    console.log(`Updating ${pack.id}`);
    run('git', ['-C', checkout, 'fetch', '--all', '--tags']);
    if (pack.ref) run('git', ['-C', checkout, 'checkout', pack.ref]);
    const branch = run('git', ['-C', checkout, 'symbolic-ref', '--short', '-q', 'HEAD'], {
      capture: true,
      allowFailure: true
    });
    if (branch) {
      run('git', ['-C', checkout, 'pull', '--ff-only']);
    } else {
      console.log(`Skipping pull for ${pack.id}: checked out at detached ref ${pack.ref}`);
    }
  }
  commandValidate();
}

function commandValidate() {
  const manifest = readManifest();
  const roots = (process.env.COURSES_DIR
    ? process.env.COURSES_DIR.split(path.delimiter).map((root) => root.trim()).filter(Boolean)
    : [path.join(cwd, 'courses')]);
  for (const pack of manifest.packs) {
    if (pack.enabled === false) continue;
    roots.push(courseRootForPack(pack));
  }
  const { issues, warnings, trackCount } = validateRoots(roots);
  for (const warning of warnings) console.warn(`warning: ${warning}`);
  if (issues.length > 0) {
    for (const issue of issues) console.error(`error: ${issue}`);
    throw new Error(`Validation failed with ${issues.length} error(s).`);
  }
  console.log(`Validated ${trackCount} track(s) across ${roots.length} course root(s).`);
}

const { command, opts } = parseArgs(process.argv.slice(2));

try {
  if (!command || command === 'help' || command === '--help') usage(0);
  if (command === 'list') commandList();
  else if (command === 'add') commandAdd(opts);
  else if (command === 'update') commandUpdate();
  else if (command === 'validate') commandValidate();
  else usage(1);
} catch (err) {
  console.error(err instanceof Error ? err.message : err);
  process.exit(1);
}
