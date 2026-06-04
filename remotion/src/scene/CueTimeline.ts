export type CueBeat = {
  id: string;
  time: number;
  duration: number;
  kind: "count" | "trace" | "label";
  target: string;
  value?: string | number;
  actor?: "content" | "octopus" | "both";
  emphasis?: number;
};

export type ActiveCueBeat = CueBeat & {
  progress: number;
};

export const getActiveCue = (
  beats: CueBeat[],
  fps: number,
  frame: number,
): ActiveCueBeat | null => {
  const time = frame / fps;
  const active = beats.find((beat) => time >= beat.time && time <= beat.time + beat.duration);
  if (!active) {
    return null;
  }

  return {
    ...active,
    progress: active.duration <= 0 ? 1 : Math.max(0, Math.min(1, (time - active.time) / active.duration)),
  };
};

export const cueProgress = (beat: CueBeat, fps: number, frame: number): number => {
  const time = frame / fps;
  return Math.max(0, Math.min(1, (time - beat.time) / Math.max(beat.duration, 0.001)));
};
