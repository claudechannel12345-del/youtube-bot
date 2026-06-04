import type {ExpressionChannels, ExpressionName} from "./rigTypes";

const base: ExpressionChannels = {
  eyeOpen: 1,
  pupilScale: 1,
  pupilX: 0,
  pupilY: 0,
  browRaise: 0,
  browAngle: 0,
  mouthOpen: 0,
  mouthCurve: 0,
  mantleSquash: 0,
  glowIntensity: 0.5,
};

const poses: Record<ExpressionName, ExpressionChannels> = {
  neutral: {...base, eyeOpen: 0.82, mouthCurve: 0.08, glowIntensity: 0.38},
  curious: {...base, eyeOpen: 0.96, pupilScale: 1.05, browRaise: 0.42, browAngle: -0.18, mouthCurve: 0.18, glowIntensity: 0.62},
  surprised: {...base, eyeOpen: 1.24, pupilScale: 0.86, browRaise: 0.82, browAngle: 0.22, mouthOpen: 0.5, mouthCurve: -0.12, mantleSquash: 0.18, glowIntensity: 0.92},
  skeptical: {...base, eyeOpen: 0.72, browRaise: -0.12, browAngle: -0.35, mouthCurve: -0.18, glowIntensity: 0.48},
  thinking: {...base, eyeOpen: 0.78, pupilX: -0.15, browRaise: 0.25, browAngle: 0.12, mouthCurve: -0.04, glowIntensity: 0.5},
  excited: {...base, eyeOpen: 1.08, pupilScale: 1.08, browRaise: 0.74, mouthOpen: 0.26, mouthCurve: 0.35, mantleSquash: 0.08, glowIntensity: 1},
  concerned: {...base, eyeOpen: 0.86, browRaise: 0.3, browAngle: 0.38, mouthCurve: -0.28, glowIntensity: 0.54},
};

export const blendExpressions = (weights: Partial<Record<ExpressionName, number>> = {neutral: 1}): ExpressionChannels => {
  const entries = Object.entries(weights).filter((entry): entry is [ExpressionName, number] => entry[1] > 0);
  const total = entries.reduce((sum, [, value]) => sum + value, 0) || 1;
  const out = {...base};

  Object.keys(out).forEach((key) => {
    out[key as keyof ExpressionChannels] = 0;
  });

  for (const [name, weight] of entries) {
    const normalized = Math.max(0, Math.min(1, weight)) / total;
    const pose = poses[name] ?? poses.neutral;
    Object.keys(out).forEach((key) => {
      out[key as keyof ExpressionChannels] += pose[key as keyof ExpressionChannels] * normalized;
    });
  }

  return out;
};
