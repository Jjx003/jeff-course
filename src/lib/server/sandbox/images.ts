/**
 * Local Docker image management.
 *
 * `ensureImagePulled(tag, onProgress)` checks if the image is present
 * locally; if not, it runs `docker build` against the appropriate
 * Dockerfile from `infra/docker/`. We never `docker pull` from a public
 * registry — every jeff-course image is built locally so we can ship
 * Dockerfile changes alongside code changes.
 *
 * SERVER-SIDE ONLY.
 */

import { spawn } from 'node:child_process';
import path from 'node:path';
import { existsSync } from 'node:fs';

interface ImageBuildSpec {
  tag: string;
  dockerfile: string;
  contextDir: string;
}

function infraRoot(): string {
  return path.join(process.cwd(), 'infra', 'docker');
}

function buildSpecForTag(tag: string): ImageBuildSpec {
  const root = infraRoot();
  if (tag.startsWith('jeff-course/cpp')) {
    return { tag, dockerfile: path.join(root, 'cpp.Dockerfile'), contextDir: root };
  }
  if (tag.startsWith('jeff-course/python-cuda')) {
    return { tag, dockerfile: path.join(root, 'python-cuda.Dockerfile'), contextDir: root };
  }
  if (tag.startsWith('jeff-course/python')) {
    return { tag, dockerfile: path.join(root, 'python.Dockerfile'), contextDir: root };
  }
  throw new Error(`Unknown image tag: ${tag}`);
}

function imageExists(tag: string): Promise<boolean> {
  return new Promise((resolve) => {
    const p = spawn('docker', ['image', 'inspect', tag], { stdio: 'ignore', windowsHide: true });
    p.on('close', (code) => resolve(code === 0));
    p.on('error', () => resolve(false));
  });
}

function buildImage(spec: ImageBuildSpec, onProgress: (msg: string) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    if (!existsSync(spec.dockerfile)) {
      reject(new Error(`Dockerfile not found: ${spec.dockerfile}`));
      return;
    }
    const args = ['build', '-t', spec.tag, '-f', spec.dockerfile, spec.contextDir];
    onProgress(`Building image ${spec.tag} (this may take a few minutes on first run)…`);
    const p = spawn('docker', args, { stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true });
    p.stdout?.on('data', (b: Buffer) => {
      const line = b.toString().trim();
      if (line) onProgress(line);
    });
    p.stderr?.on('data', (b: Buffer) => {
      const line = b.toString().trim();
      if (line) onProgress(line);
    });
    p.on('close', (code) => {
      if (code === 0) {
        onProgress(`Image ${spec.tag} ready.`);
        resolve();
      } else {
        reject(new Error(`docker build failed with exit code ${code}`));
      }
    });
    p.on('error', (err) => reject(err));
  });
}

const inflight = new Map<string, Promise<void>>();

/**
 * Make sure `tag` exists locally. If not, build it from the corresponding
 * Dockerfile in `infra/docker/`. Concurrent calls for the same tag share
 * a single build promise.
 */
export function ensureImagePulled(tag: string, onProgress: (msg: string) => void): Promise<void> {
  const existing = inflight.get(tag);
  if (existing) return existing;

  const promise = (async () => {
    if (await imageExists(tag)) return;
    const spec = buildSpecForTag(tag);
    await buildImage(spec, onProgress);
  })();

  inflight.set(tag, promise);
  promise.finally(() => inflight.delete(tag));
  return promise;
}
