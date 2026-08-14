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
const DIFFICULTIES = new Set(['beginner', 'intermediate', 'advanced']);
const QUESTION_TYPES = new Set(['multiple_choice', 'true_false', 'parametric']);
const STARTER_FILES = { python: 'python.py', cpp: 'cpp.cpp' };
const MODULE_ARTIFACTS = new Set([
  'problem.md',
  'theory.md',
  'tips.md',
  'quiz.yaml',
  'drill.yaml',
  'requirements.txt',
  'starter'
]);

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

function displayPath(filePath) {
  const relative = path.relative(cwd, filePath);
  return (relative || path.basename(filePath)).replace(/\\/g, '/');
}

function diagnostic(filePath, field, message) {
  return `${displayPath(filePath)}${field ? `:${field}` : ''}: ${message}`;
}

function isObject(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

function readValidationYaml(filePath, issues) {
  try {
    return yaml.load(fs.readFileSync(filePath, 'utf-8')) ?? null;
  } catch (err) {
    const line = err?.mark?.line === undefined ? '' : String(err.mark.line + 1);
    issues.push(diagnostic(filePath, line, `invalid YAML (${err.reason ?? err.message ?? err})`));
    return null;
  }
}

function requireString(value, filePath, field, issues) {
  if (typeof value !== 'string' || value.trim() === '') {
    issues.push(diagnostic(filePath, field, 'expected a non-empty string'));
    return false;
  }
  return true;
}

function optionalNumber(value, filePath, field, issues, options = {}) {
  if (value === undefined) return true;
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    issues.push(diagnostic(filePath, field, 'expected a finite number'));
    return false;
  }
  if (options.integer && !Number.isInteger(value)) {
    issues.push(diagnostic(filePath, field, 'expected an integer'));
    return false;
  }
  if (options.min !== undefined && value < options.min) {
    issues.push(diagnostic(filePath, field, `expected a value >= ${options.min}`));
    return false;
  }
  if (options.max !== undefined && value > options.max) {
    issues.push(diagnostic(filePath, field, `expected a value <= ${options.max}`));
    return false;
  }
  return true;
}

function optionalStringArray(value, filePath, field, issues, options = {}) {
  if (value === undefined) return true;
  if (!Array.isArray(value) || (options.nonEmpty && value.length === 0)) {
    issues.push(diagnostic(filePath, field, `expected ${options.nonEmpty ? 'a non-empty' : 'an'} array of strings`));
    return false;
  }
  value.forEach((item, index) => {
    if (typeof item !== 'string' || item.trim() === '') {
      issues.push(diagnostic(filePath, `${field}[${index}]`, 'expected a non-empty string'));
    }
  });
  return value.every((item) => typeof item === 'string' && item.trim() !== '');
}

function requireStringArray(value, filePath, field, issues, options = {}) {
  if (value === undefined) {
    issues.push(diagnostic(filePath, field, `expected ${options.nonEmpty ? 'a non-empty' : 'an'} array of strings`));
    return false;
  }
  return optionalStringArray(value, filePath, field, issues, options);
}

function validateRuntime(runtime, filePath, issues) {
  if (runtime === undefined) return;
  if (!isObject(runtime)) {
    issues.push(diagnostic(filePath, 'runtime', 'expected an object'));
    return;
  }
  if (runtime.recommendedMode !== undefined &&
      !['baremetal', 'docker', 'docker-gpu'].includes(runtime.recommendedMode)) {
    issues.push(diagnostic(filePath, 'runtime.recommendedMode', 'expected one of: baremetal, docker, docker-gpu'));
  }
  if (runtime.resources === undefined) return;
  if (!isObject(runtime.resources)) {
    issues.push(diagnostic(filePath, 'runtime.resources', 'expected an object'));
    return;
  }
  optionalNumber(runtime.resources.memoryMb, filePath, 'runtime.resources.memoryMb', issues, { min: 0 });
  optionalNumber(runtime.resources.cpus, filePath, 'runtime.resources.cpus', issues, { min: 0 });
  optionalNumber(runtime.resources.timeoutMs, filePath, 'runtime.resources.timeoutMs', issues, { min: 1 });
  const gpu = runtime.resources.gpu;
  if (gpu !== undefined && gpu !== 'all' && gpu !== 'none') {
    if (!isObject(gpu)) {
      issues.push(diagnostic(filePath, 'runtime.resources.gpu', 'expected "all", "none", or { device: number }'));
    } else {
      optionalNumber(gpu.device, filePath, 'runtime.resources.gpu.device', issues, { min: 0, integer: true });
      if (gpu.device === undefined) {
        issues.push(diagnostic(filePath, 'runtime.resources.gpu.device', 'is required'));
      }
    }
  }
}

function validateMetadata(meta, filePath, kind, issues) {
  requireString(meta.title, filePath, 'title', issues);
  requireString(meta.slug, filePath, 'slug', issues);
  if (kind === 'course' || meta.description !== undefined) {
    requireString(meta.description, filePath, 'description', issues);
  }
  optionalStringArray(meta.tags, filePath, 'tags', issues);
  optionalNumber(meta.order, filePath, 'order', issues);
  if (meta.difficulty !== undefined &&
      (typeof meta.difficulty !== 'string' || !DIFFICULTIES.has(meta.difficulty))) {
    issues.push(diagnostic(filePath, 'difficulty', `expected one of: ${[...DIFFICULTIES].join(', ')}`));
  }
  if (kind === 'module') {
    optionalNumber(meta.estimatedMinutes, filePath, 'estimatedMinutes', issues, { min: 1 });
    validateRuntime(meta.runtime, filePath, issues);
  }
}

function validateParamRanges(params, filePath, field, issues) {
  if (!isObject(params) || Object.keys(params).length === 0) {
    issues.push(diagnostic(filePath, field, 'expected a non-empty map of numeric ranges'));
    return;
  }
  for (const [name, range] of Object.entries(params)) {
    const rangeField = `${field}.${name}`;
    if (!isObject(range)) {
      issues.push(diagnostic(filePath, rangeField, 'expected { min, max, step }'));
      continue;
    }
    const minOk = optionalNumber(range.min, filePath, `${rangeField}.min`, issues) && range.min !== undefined;
    const maxOk = optionalNumber(range.max, filePath, `${rangeField}.max`, issues) && range.max !== undefined;
    const stepOk = optionalNumber(range.step, filePath, `${rangeField}.step`, issues) && range.step !== undefined;
    if (range.min === undefined) issues.push(diagnostic(filePath, `${rangeField}.min`, 'is required'));
    if (range.max === undefined) issues.push(diagnostic(filePath, `${rangeField}.max`, 'is required'));
    if (range.step === undefined) issues.push(diagnostic(filePath, `${rangeField}.step`, 'is required'));
    if (minOk && maxOk && range.min > range.max) {
      issues.push(diagnostic(filePath, rangeField, `min (${range.min}) must be <= max (${range.max})`));
    }
    if (stepOk && range.step <= 0) {
      issues.push(diagnostic(filePath, `${rangeField}.step`, 'must be greater than 0'));
    }
  }
}

function validateQuiz(filePath, issues) {
  const quiz = readValidationYaml(filePath, issues);
  if (!isObject(quiz)) {
    if (quiz !== null) issues.push(diagnostic(filePath, '', 'expected a YAML object'));
    return;
  }
  if (!Array.isArray(quiz.questions) || quiz.questions.length === 0) {
    issues.push(diagnostic(filePath, 'questions', 'expected a non-empty array'));
    return;
  }

  const ids = new Set();
  quiz.questions.forEach((question, index) => {
    const base = `questions[${index}]`;
    if (!isObject(question)) {
      issues.push(diagnostic(filePath, base, 'expected a question object'));
      return;
    }
    if (requireString(question.id, filePath, `${base}.id`, issues)) {
      if (ids.has(question.id)) issues.push(diagnostic(filePath, `${base}.id`, `duplicate question id "${question.id}"`));
      ids.add(question.id);
    }
    if (typeof question.type !== 'string' || !QUESTION_TYPES.has(question.type)) {
      issues.push(diagnostic(filePath, `${base}.type`, `expected one of: ${[...QUESTION_TYPES].join(', ')}`));
      return;
    }

    if (question.type === 'multiple_choice') {
      requireString(question.stem, filePath, `${base}.stem`, issues);
      const optionsOk = requireStringArray(question.options, filePath, `${base}.options`, issues, { nonEmpty: true });
      if (optionsOk && question.options.length < 2) {
        issues.push(diagnostic(filePath, `${base}.options`, 'expected at least 2 options'));
      }
      if (!Number.isInteger(question.correct)) {
        issues.push(diagnostic(filePath, `${base}.correct`, 'expected a zero-based integer option index'));
      } else if (Array.isArray(question.options) &&
          (question.correct < 0 || question.correct >= question.options.length)) {
        issues.push(diagnostic(filePath, `${base}.correct`, `index ${question.correct} is outside options[0..${question.options.length - 1}]`));
      }
      requireString(question.explanation, filePath, `${base}.explanation`, issues);
    } else if (question.type === 'true_false') {
      requireString(question.stem, filePath, `${base}.stem`, issues);
      if (typeof question.correct !== 'boolean') {
        issues.push(diagnostic(filePath, `${base}.correct`, 'expected true or false'));
      }
      requireString(question.explanation, filePath, `${base}.explanation`, issues);
    } else {
      requireString(question.stem_template, filePath, `${base}.stem_template`, issues);
      validateParamRanges(question.params, filePath, `${base}.params`, issues);
      requireString(question.correct_formula, filePath, `${base}.correct_formula`, issues);
      requireStringArray(question.distractor_formulas, filePath, `${base}.distractor_formulas`, issues, { nonEmpty: true });
      requireString(question.explanation_template, filePath, `${base}.explanation_template`, issues);
    }
  });
}

function validateDrill(filePath, issues) {
  const drill = readValidationYaml(filePath, issues);
  if (!isObject(drill)) {
    if (drill !== null) issues.push(diagnostic(filePath, '', 'expected a YAML object'));
    return;
  }
  if (drill.title !== undefined) requireString(drill.title, filePath, 'title', issues);
  if (drill.instructions !== undefined) requireString(drill.instructions, filePath, 'instructions', issues);
  optionalNumber(drill.roundSeconds, filePath, 'roundSeconds', issues, { min: 1 });
  optionalNumber(drill.targetAccuracy, filePath, 'targetAccuracy', issues, { min: 0, max: 1 });
  optionalNumber(drill.itemsPerRound, filePath, 'itemsPerRound', issues, { min: 1, integer: true });
  if (!Array.isArray(drill.items) || drill.items.length === 0) {
    issues.push(diagnostic(filePath, 'items', 'expected a non-empty array'));
    return;
  }

  const ids = new Set();
  drill.items.forEach((item, index) => {
    const base = `items[${index}]`;
    if (!isObject(item)) {
      issues.push(diagnostic(filePath, base, 'expected a drill item object'));
      return;
    }
    if (requireString(item.id, filePath, `${base}.id`, issues)) {
      if (ids.has(item.id)) issues.push(diagnostic(filePath, `${base}.id`, `duplicate drill item id "${item.id}"`));
      ids.add(item.id);
    }
    requireString(item.prompt_template, filePath, `${base}.prompt_template`, issues);
    validateParamRanges(item.params, filePath, `${base}.params`, issues);
    requireString(item.correct_formula, filePath, `${base}.correct_formula`, issues);
    optionalNumber(item.tolerance, filePath, `${base}.tolerance`, issues, { min: 0 });
    if (item.answer_suffix !== undefined) requireString(item.answer_suffix, filePath, `${base}.answer_suffix`, issues);
    if (item.explanation_template !== undefined) {
      requireString(item.explanation_template, filePath, `${base}.explanation_template`, issues);
    }
  });
}

function isLikelyModuleDir(entry, directory) {
  if (/^\d+(?:\.\d+)?[-_]/.test(entry.name)) return true;
  return fs.readdirSync(directory).some((name) => MODULE_ARTIFACTS.has(name));
}

function validateTrack(trackDir) {
  const issues = [];
  const warnings = [];
  const coursePath = path.join(trackDir, 'course.yaml');
  const course = readValidationYaml(coursePath, issues);
  if (!isObject(course)) {
    if (course !== null) issues.push(diagnostic(coursePath, '', 'expected a YAML object'));
    return { issues, warnings, slug: null };
  }
  validateMetadata(course, coursePath, 'course', issues);

  const childDirs = fs.readdirSync(trackDir, { withFileTypes: true }).filter((entry) => entry.isDirectory());
  const moduleDirs = [];
  for (const entry of childDirs) {
    const directory = path.join(trackDir, entry.name);
    if (fs.existsSync(path.join(directory, 'module.yaml'))) moduleDirs.push(directory);
    else if (isLikelyModuleDir(entry, directory)) {
      issues.push(diagnostic(path.join(directory, 'module.yaml'), '', 'missing module.yaml in likely module directory'));
    }
  }
  moduleDirs.sort();

  if (moduleDirs.length === 0) warnings.push(`${displayPath(trackDir)}: no module directories found`);
  const moduleSlugs = new Set();

  for (const moduleDir of moduleDirs) {
    const modulePath = path.join(moduleDir, 'module.yaml');
    const mod = readValidationYaml(modulePath, issues);
    if (!isObject(mod)) {
      if (mod !== null) issues.push(diagnostic(modulePath, '', 'expected a YAML object'));
      continue;
    }
    validateMetadata(mod, modulePath, 'module', issues);
    const type = mod.type ?? 'coding';
    if (mod.slug) {
      if (moduleSlugs.has(mod.slug)) issues.push(diagnostic(modulePath, 'slug', `duplicate module slug "${mod.slug}"`));
      moduleSlugs.add(mod.slug);
    }
    if (typeof type !== 'string' || !MODULE_TYPES.has(type)) {
      issues.push(diagnostic(modulePath, 'type', `expected one of: ${[...MODULE_TYPES].join(', ')}`));
    }
    const declaredLanguagesOk = optionalStringArray(mod.languages, modulePath, 'languages', issues, { nonEmpty: true });
    const languages = declaredLanguagesOk && mod.languages ? mod.languages : ['python'];
    for (const lang of languages) {
      if (!LANGUAGES.has(lang)) issues.push(diagnostic(modulePath, 'languages', `unsupported language "${lang}"`));
    }
    const defaultLanguageOk = mod.defaultLanguage === undefined ||
      (typeof mod.defaultLanguage === 'string' && LANGUAGES.has(mod.defaultLanguage));
    if (!defaultLanguageOk) {
      issues.push(diagnostic(modulePath, 'defaultLanguage', `expected one of: ${[...LANGUAGES].join(', ')}`));
    }
    if (!fs.existsSync(path.join(moduleDir, 'problem.md'))) {
      issues.push(diagnostic(path.join(moduleDir, 'problem.md'), '', 'missing required file'));
    }

    if (type === 'coding') {
      for (const lang of languages.filter((value) => LANGUAGES.has(value))) {
        const starterPath = path.join(moduleDir, 'starter', STARTER_FILES[lang]);
        if (!fs.existsSync(starterPath)) {
          issues.push(diagnostic(starterPath, '', `missing starter file for declared language "${lang}"`));
        }
      }
      if (mod.defaultLanguage !== undefined && defaultLanguageOk && !languages.includes(mod.defaultLanguage)) {
        issues.push(diagnostic(modulePath, 'defaultLanguage', 'must also appear in languages'));
      }
      if (fs.existsSync(path.join(moduleDir, 'requirements.txt'))) {
        warnings.push(`${displayPath(path.join(moduleDir, 'requirements.txt'))}: will install code dependencies when run`);
      }
    } else {
      if (mod.languages || mod.defaultLanguage) {
        warnings.push(`${displayPath(modulePath)}: non-coding module should omit languages/defaultLanguage`);
      }
      if (fs.existsSync(path.join(moduleDir, 'starter'))) {
        warnings.push(`${displayPath(path.join(moduleDir, 'starter'))}: non-coding module starter directory is ignored`);
      }
    }

    if (type === 'quiz' || type === 'test') {
      const quizPath = path.join(moduleDir, 'quiz.yaml');
      if (!fs.existsSync(quizPath)) issues.push(diagnostic(quizPath, '', `missing required file for ${type} module`));
      else validateQuiz(quizPath, issues);
    }
    if (type === 'drill') {
      const drillPath = path.join(moduleDir, 'drill.yaml');
      if (!fs.existsSync(drillPath)) issues.push(diagnostic(drillPath, '', 'missing required file for drill module'));
      else validateDrill(drillPath, issues);
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
