export interface ReadingAudioWord {
  text: string;
  startMs: number;
  endMs: number;
  confidence?: number;
}

export interface ReadingAudioClip {
  id: string;
  title: string;
  sectionId: string;
  stepIndex: number;
  durationMs: number;
  url: string | null;
  text?: string;
  words?: ReadingAudioWord[];
}

export interface ReadingAudioManifest {
  available: boolean;
  title: string | null;
  clips: ReadingAudioClip[];
}
