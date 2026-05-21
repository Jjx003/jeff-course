import { existsSync } from 'node:fs';
import { readFile } from 'node:fs/promises';
import path from 'node:path';
import type { ReadingAudioClip, ReadingAudioManifest, ReadingAudioWord } from '$lib/types/audio.js';
import type { Problem } from '$lib/types/course.js';

interface RawTtsOutput {
  id?: unknown;
  title?: unknown;
  path?: unknown;
  text?: unknown;
  duration_ms_estimate?: unknown;
  words?: unknown;
}

interface RawTtsManifest {
  title?: unknown;
  outputs?: unknown;
}

const SECTION_IDS = new Set(['problem', 'theory', 'tips']);

function parseWords(value: unknown): ReadingAudioWord[] | undefined {
  if (!Array.isArray(value)) return undefined;
  const words = value.flatMap((word): ReadingAudioWord[] => {
    if (typeof word !== 'object' || word === null) return [];
    const candidate = word as Record<string, unknown>;
    if (
      typeof candidate.text !== 'string' ||
      typeof candidate.startMs !== 'number' ||
      typeof candidate.endMs !== 'number'
    ) {
      return [];
    }
    return [
      {
        text: candidate.text,
        startMs: candidate.startMs,
        endMs: candidate.endMs,
        confidence: typeof candidate.confidence === 'number' ? candidate.confidence : undefined
      }
    ];
  });
  return words.length > 0 ? words : undefined;
}

function ttsRoot(): string {
  return path.resolve(process.cwd(), 'data', 'tts-output');
}

function manifestPath(trackSlug: string): string {
  return path.join(ttsRoot(), `${trackSlug}-gradual`, 'manifest.json');
}

function clipPrefix(problem: Problem): string {
  return `${String(problem.order).padStart(2, '0')}-${problem.slug}-`;
}

function parseClipId(id: string, prefix: string): { sectionId: string; stepIndex: number } | null {
  if (!id.startsWith(prefix)) return null;
  const rest = id.slice(prefix.length);
  const match = /^(problem|theory|tips)-(\d+)$/.exec(rest);
  if (!match || !SECTION_IDS.has(match[1])) return null;
  return { sectionId: match[1], stepIndex: Number(match[2]) };
}

async function readRawManifest(trackSlug: string): Promise<RawTtsManifest | null> {
  const file = manifestPath(trackSlug);
  if (!existsSync(file)) return null;
  const raw = await readFile(file, 'utf8');
  return JSON.parse(raw) as RawTtsManifest;
}

export async function getReadingAudioManifest(
  trackSlug: string,
  problem: Problem
): Promise<ReadingAudioManifest> {
  const raw = await readRawManifest(trackSlug);
  if (!raw || !Array.isArray(raw.outputs)) {
    return { available: false, title: null, clips: [] };
  }

  const prefix = clipPrefix(problem);
  const clips: ReadingAudioClip[] = raw.outputs
    .filter((output): output is RawTtsOutput => typeof output === 'object' && output !== null)
    .flatMap((output) => {
      if (typeof output.id !== 'string') return [];
      const parsed = parseClipId(output.id, prefix);
      if (!parsed) return [];
      const clip: ReadingAudioClip = {
        id: output.id,
        title: typeof output.title === 'string' ? output.title : output.id,
        sectionId: parsed.sectionId,
        stepIndex: parsed.stepIndex,
        durationMs:
          typeof output.duration_ms_estimate === 'number' ? output.duration_ms_estimate : 30_000,
        url: `/api/audio/${trackSlug}/${problem.slug}/${output.id}`,
        text: typeof output.text === 'string' ? output.text : undefined,
        words: parseWords(output.words)
      };
      return [clip];
    })
    .sort((a, b) => {
      const sectionOrder = ['problem', 'theory', 'tips'];
      const sectionDiff = sectionOrder.indexOf(a.sectionId) - sectionOrder.indexOf(b.sectionId);
      return sectionDiff || a.stepIndex - b.stepIndex;
    });

  return {
    available: clips.length > 0,
    title: typeof raw.title === 'string' ? raw.title : null,
    clips
  };
}

export async function getReadingAudioClipPath(
  trackSlug: string,
  problem: Problem,
  clipId: string
): Promise<string | null> {
  const raw = await readRawManifest(trackSlug);
  if (!raw || !Array.isArray(raw.outputs)) return null;

  const prefix = clipPrefix(problem);
  if (!parseClipId(clipId, prefix)) return null;

  const output = raw.outputs.find((item): item is RawTtsOutput => {
    return typeof item === 'object' && item !== null && (item as RawTtsOutput).id === clipId;
  });
  if (!output || typeof output.path !== 'string') return null;

  const root = ttsRoot();
  const resolved = path.resolve(output.path);
  if (!resolved.startsWith(root + path.sep)) return null;
  return resolved;
}
