/**
 * Capability detection — probes the host for Docker and NVIDIA GPU support.
 *
 * Cached on globalThis so we don't shell out on every API hit.
 *
 *   docker     → `docker info --format {{.ServerVersion}}` (2s timeout)
 *   gpu        → `docker run --rm --gpus all nvidia/cuda:12.4-base nvidia-smi -L`
 *                with a generous timeout because the image may need to pull
 *                on first run. We allow the user to bypass the GPU probe
 *                by setting SANDBOX_SKIP_GPU_PROBE=1 in environments where
 *                pulling cuda base images at boot is undesirable.
 *
 * SERVER-SIDE ONLY.
 */

import { spawn } from 'node:child_process';
import type { SandboxCapabilities } from '../types.js';

const IS_WINDOWS = process.platform === 'win32';

interface Probe {
  stdout: string;
  stderr: string;
  exitCode: number | null;
  timedOut: boolean;
}

function runProbe(cmd: string, args: string[], timeoutMs: number): Promise<Probe> {
  return new Promise((resolve) => {
    let settled = false;
    let stdout = '';
    let stderr = '';
    let proc: import('node:child_process').ChildProcess;
    try {
      proc = spawn(cmd, args, {
        stdio: ['ignore', 'pipe', 'pipe'],
        windowsHide: true
      });
    } catch (err) {
      resolve({
        stdout: '',
        stderr: err instanceof Error ? err.message : String(err),
        exitCode: null,
        timedOut: false
      });
      return;
    }
    const timer = setTimeout(() => {
      if (settled) return;
      try { proc.kill('SIGKILL'); } catch { /* ignore */ }
      settled = true;
      resolve({ stdout, stderr, exitCode: null, timedOut: true });
    }, timeoutMs);
    proc.stdout?.on('data', (b: Buffer) => { stdout += b.toString(); });
    proc.stderr?.on('data', (b: Buffer) => { stderr += b.toString(); });
    proc.on('error', (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ stdout, stderr: stderr || err.message, exitCode: null, timedOut: false });
    });
    proc.on('close', (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ stdout, stderr, exitCode: code, timedOut: false });
    });
  });
}

async function detectDocker(): Promise<SandboxCapabilities['docker']> {
  const probe = await runProbe('docker', ['info', '--format', '{{.ServerVersion}}'], 4_000);
  if (probe.exitCode === 0) {
    return { available: true, version: probe.stdout.trim() || 'unknown' };
  }
  const reason = probe.timedOut
    ? 'docker info timed out (is Docker Desktop / dockerd running?)'
    : probe.stderr.trim().split('\n')[0] || 'docker command not found';
  return { available: false, reason };
}

async function detectGpu(): Promise<SandboxCapabilities['gpu']> {
  if (process.env.SANDBOX_SKIP_GPU_PROBE === '1') {
    return { available: false, reason: 'GPU probe disabled via SANDBOX_SKIP_GPU_PROBE' };
  }
  // First check nvidia-smi on the host. If the host has no NVIDIA driver,
  // there's no point trying the container probe.
  const host = await runProbe('nvidia-smi', ['--query-gpu=name', '--format=csv,noheader'], 2_000);
  if (host.exitCode !== 0) {
    return { available: false, reason: 'nvidia-smi not present on host' };
  }
  const lines = host.stdout.trim().split('\n').filter(Boolean);
  if (lines.length === 0) {
    return { available: false, reason: 'No NVIDIA devices reported by nvidia-smi' };
  }

  // Now verify Docker can actually pass through a GPU. We skip this probe
  // on Windows-without-Docker by short-circuiting if docker.available is
  // false in the caller. Here we just check the runtime is usable.
  const ctr = await runProbe(
    'docker',
    ['run', '--rm', '--gpus', 'all', 'nvidia/cuda:12.4.0-base-ubuntu22.04', 'nvidia-smi', '-L'],
    IS_WINDOWS ? 60_000 : 45_000
  );
  if (ctr.exitCode === 0) {
    return { available: true, deviceCount: lines.length };
  }
  // GPU on host but docker passthrough failed — common when the NVIDIA
  // Container Toolkit isn't installed yet.
  const reason = ctr.stderr.trim().split('\n').slice(-1)[0] || 'docker GPU passthrough failed';
  return { available: false, deviceCount: lines.length, reason };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const g = globalThis as any;
const CACHED: { value: SandboxCapabilities | null; promise: Promise<SandboxCapabilities> | null } =
  g.__sandboxCapabilities ?? (g.__sandboxCapabilities = { value: null, promise: null });

/**
 * Returns cached capabilities or runs the probes if this is the first call.
 * Forcing a refresh (e.g. after the user installs Docker) is done via
 * `refreshCapabilities()`.
 */
export async function getCapabilities(): Promise<SandboxCapabilities> {
  if (CACHED.value) return CACHED.value;
  if (CACHED.promise) return CACHED.promise;
  CACHED.promise = (async () => {
    const docker = await detectDocker();
    // Only probe GPU passthrough if docker is available — otherwise the
    // probe would always fail and noise the logs.
    const gpu = docker.available
      ? await detectGpu()
      : { available: false, reason: 'Docker not available — GPU passthrough requires docker' };
    const caps: SandboxCapabilities = { docker, gpu };
    CACHED.value = caps;
    CACHED.promise = null;
    return caps;
  })();
  return CACHED.promise;
}

export function refreshCapabilities(): Promise<SandboxCapabilities> {
  CACHED.value = null;
  CACHED.promise = null;
  return getCapabilities();
}
