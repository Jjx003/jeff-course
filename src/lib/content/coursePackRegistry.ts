/**
 * coursePackRegistry.ts
 *
 * Resolves the course roots visible to the app. Built-in courses are always
 * loaded first, then enabled git-backed course packs from a local manifest.
 *
 * SERVER-SIDE ONLY.
 */

import fs from 'fs';
import path from 'path';
import yaml from 'js-yaml';

export interface CoursePackEntry {
  id: string;
  repo?: string;
  ref?: string;
  enabled?: boolean;
  path?: string;
  coursesDir?: string;
}

interface CoursePacksManifest {
  packs?: CoursePackEntry[];
}

function readYaml<T>(filePath: string): T | null {
  if (!fs.existsSync(filePath)) return null;
  try {
    return yaml.load(fs.readFileSync(filePath, 'utf-8')) as T;
  } catch (err) {
    console.warn(`[coursePacks] Failed to parse ${filePath}:`, err);
    return null;
  }
}

export function safeCoursePackId(id: string): string {
  return id.trim().toLowerCase().replace(/[^a-z0-9._-]+/g, '__');
}

export function getCoursePacksManifestPath(): string {
  return process.env.COURSE_PACKS_MANIFEST ?? path.join(process.cwd(), 'data', 'course-packs.yaml');
}

export function getCoursePacksRepoDir(): string {
  return process.env.COURSE_PACKS_DIR ?? path.join(process.cwd(), 'data', 'course-packs', 'repos');
}

function getBuiltInCourseRoots(): string[] {
  const raw = process.env.COURSES_DIR;
  if (!raw) return [path.join(process.cwd(), 'courses')];
  return raw
    .split(path.delimiter)
    .map((p) => p.trim())
    .filter(Boolean);
}

function resolvePackCheckoutPath(pack: CoursePackEntry): string {
  if (pack.path) {
    return path.isAbsolute(pack.path) ? pack.path : path.resolve(process.cwd(), pack.path);
  }
  return path.join(getCoursePacksRepoDir(), safeCoursePackId(pack.id));
}

function resolvePackCourseRoot(pack: CoursePackEntry): string | null {
  const checkoutPath = resolvePackCheckoutPath(pack);
  if (!fs.existsSync(checkoutPath)) {
    console.warn(`[coursePacks] Pack "${pack.id}" is enabled but not installed at ${checkoutPath}`);
    return null;
  }

  if (pack.coursesDir) {
    const root = path.isAbsolute(pack.coursesDir)
      ? pack.coursesDir
      : path.join(checkoutPath, pack.coursesDir);
    return fs.existsSync(root) ? root : null;
  }

  const nestedCourses = path.join(checkoutPath, 'courses');
  return fs.existsSync(nestedCourses) ? nestedCourses : checkoutPath;
}

export function loadCoursePackManifest(): CoursePacksManifest {
  return readYaml<CoursePacksManifest>(getCoursePacksManifestPath()) ?? { packs: [] };
}

export function getCourseRoots(): string[] {
  const roots = [...getBuiltInCourseRoots()];
  const manifest = loadCoursePackManifest();

  for (const pack of manifest.packs ?? []) {
    if (!pack.id) continue;
    if (pack.enabled === false) continue;
    const root = resolvePackCourseRoot(pack);
    if (root) roots.push(root);
  }

  return roots;
}
