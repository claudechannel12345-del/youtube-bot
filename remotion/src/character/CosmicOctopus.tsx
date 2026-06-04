import type React from "react";
import {BG, WHITE} from "../theme";
import type {Point, ResolvedPose, SolvedArm} from "./rigTypes";
import {octopusSilhouettePath} from "./silhouette";

type CosmicOctopusProps = {
  pose: ResolvedPose;
};

const GOO_BLUR = 7;
export const MANTLE_SCALE = 0.88;
export let MERGE_MODE: "polygon" | "goo" = "goo";

const spots = Array.from({length: 11}, (_, i) => ({
  x: Math.cos(i * 1.91) * (24 + (i % 4) * 14),
  y: -8 + Math.sin(i * 1.29) * (16 + (i % 3) * 16),
  r: 1.9 + (i % 3) * 0.8,
  opacity: 0.24 + (i % 4) * 0.055,
}));

const gazePoint = (gazeTarget: ResolvedPose["gazeTarget"]): Point => {
  if ("px" in gazeTarget) {
    return {x: gazeTarget.px, y: gazeTarget.py};
  }
  return gazeTarget;
};

const clamp = (value: number, min: number, max: number): number => Math.max(min, Math.min(max, value));

export const CosmicOctopus: React.FC<CosmicOctopusProps> = ({pose}) => {
  const {body, expression, accent, frame} = pose;
  const gaze = gazePoint(pose.gazeTarget);
  const gazeDx = Math.max(-1, Math.min(1, (gaze.x - body.x) / 650));
  const gazeDy = Math.max(-1, Math.min(1, (gaze.y - body.y) / 520));
  const eyeOpen = clamp(expression.eyeOpen, 0.85, 1.14);
  const browRaise = clamp(expression.browRaise, -0.08, 0.5);
  const browAngle = clamp(expression.browAngle, -0.18, 0.18);
  const browBaseY = -48.5 - browRaise * 8;
  const browTilt = browAngle * 10;
  const leftBrowOuterY = browBaseY + browTilt;
  const leftBrowInnerY = browBaseY - browTilt;
  const rightBrowInnerY = browBaseY - browTilt;
  const rightBrowOuterY = browBaseY + browTilt;
  const browArcY = browBaseY - 4.6;
  const pupilOffsetX = gazeDx * 11 + expression.pupilX * 8;
  const pupilOffsetY = gazeDy * 8 + expression.pupilY * 8;
  const glow = 0.16 + expression.glowIntensity * 0.42;
  const bodyTransform = `translate(${body.x.toFixed(2)} ${body.y.toFixed(2)}) rotate(${body.rotate.toFixed(2)}) scale(${(body.scale / 100).toFixed(4)})`;
  const mantleTransform = `scale(${MANTLE_SCALE.toFixed(3)})`;
  const pulseTransform = `scale(${body.pulseX.toFixed(3)} ${body.pulseY.toFixed(3)})`;
  const mantlePath = "M 0 -86 C 49 -84 75 -51 76 -9 C 77 24 63 49 42 61 C 26 72 -26 72 -42 61 C -63 49 -77 24 -76 -9 C -75 -51 -49 -84 0 -86 Z";
  const glowPath = "M 0 -80 C 42 -78 66 -47 67 -8 C 68 26 51 55 24 70 C 10 76 -10 76 -24 70 C -51 55 -68 26 -67 -8 C -66 -47 -42 -78 0 -80 Z";
  const silhouettePath = MERGE_MODE === "polygon" ? octopusSilhouettePath({
    arms: pose.arms,
    mantlePath,
    body,
    mantleScale: MANTLE_SCALE,
  }) : "";
  const renderArm = (arm: SolvedArm) => (
    <path
      key={arm.id}
      d={arm.outlinePath}
      fill="url(#octopusBody)"
      opacity={arm.opacity}
    />
  );

  return (
    <svg
      width={1920}
      height={1080}
      viewBox="0 0 1920 1080"
      style={{position: "absolute", inset: 0, overflow: "visible"}}
    >
      <defs>
        <linearGradient
          id="octopusBody"
          x1={(body.x - body.scale * 1.35).toFixed(2)}
          y1={(body.y - body.scale * 0.95).toFixed(2)}
          x2={(body.x + body.scale * 1.1).toFixed(2)}
          y2={(body.y + body.scale * 1.55).toFixed(2)}
          gradientUnits="userSpaceOnUse"
        >
          <stop offset="0" stopColor="#3A1D72" />
          <stop offset="0.52" stopColor="#2C1B5A" />
          <stop offset="1" stopColor="#123D49" />
        </linearGradient>
        <radialGradient id="octopusBodyGlow" cx="-22" cy="-46" r="122" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#9B5DE5" stopOpacity="0.36" />
          <stop offset="0.64" stopColor="#9B5DE5" stopOpacity="0.08" />
          <stop offset="1" stopColor="#06D6A0" stopOpacity="0.12" />
        </radialGradient>
        <filter id="octoGoo" x="-30%" y="-30%" width="160%" height="160%" colorInterpolationFilters="sRGB">
          <feGaussianBlur in="SourceGraphic" stdDeviation={GOO_BLUR} result="blur" />
          <feColorMatrix
            in="blur"
            mode="matrix"
            values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 26 -11"
            result="goo"
          />
          <feComposite in="SourceGraphic" in2="goo" operator="atop" />
        </filter>
      </defs>
      <g style={{filter: `drop-shadow(0 0 ${18 + glow * 18}px ${accent}66)`}}>
        {MERGE_MODE === "polygon" ? (
          <path
            d={silhouettePath}
            fill="url(#octopusBody)"
            opacity={0.98}
          />
        ) : (
          <g filter="url(#octoGoo)">
            {pose.arms.map(renderArm)}
            <g transform={bodyTransform}>
              <g transform={mantleTransform}>
                <path
                  d={mantlePath}
                  fill="url(#octopusBody)"
                  opacity={0.98}
                  transform={pulseTransform}
                />
              </g>
            </g>
          </g>
        )}
        <g transform={bodyTransform}>
          <g transform={mantleTransform}>
            <path
              d={glowPath}
              fill="url(#octopusBodyGlow)"
              transform={pulseTransform}
            />
            <path
              d="M -67 -9 C -65 -47 -41 -78 0 -81 C 41 -78 65 -47 67 -9"
              fill="none"
              stroke="#140A2A"
              strokeWidth={2.6}
              strokeLinecap="round"
              opacity={0.52}
              transform={pulseTransform}
            />
            {spots.map((spot, i) => (
              <circle
                key={i}
                cx={spot.x}
                cy={spot.y}
                r={spot.r}
                fill={i % 2 === 0 ? accent : "#06D6A0"}
                style={{filter: `drop-shadow(0 0 ${6 + expression.glowIntensity * 8}px ${i % 2 === 0 ? accent : "#06D6A0"})`}}
                opacity={spot.opacity * (0.55 + expression.glowIntensity * 0.45 + Math.sin(frame / 18 + i) * 0.08)}
              />
            ))}
            <g transform="translate(-31 -25)">
              <ellipse rx={18} ry={15 * eyeOpen} fill="#F6F7FF" />
              <ellipse rx={18} ry={15 * eyeOpen} fill="none" stroke="#C9D2F0" strokeWidth={1.8} opacity={0.78} />
              <circle cx={pupilOffsetX} cy={pupilOffsetY} r={7.2 * expression.pupilScale} fill={BG} />
              <circle cx={pupilOffsetX - 2.6} cy={pupilOffsetY - 3.2} r={2.2} fill={WHITE} opacity={0.92} />
              <path d={`M -18 ${-15 * eyeOpen} C -8 ${-21 * eyeOpen} 8 ${-21 * eyeOpen} 18 ${-15 * eyeOpen}`} stroke="#E8ECFF" strokeWidth={2} strokeLinecap="round" opacity={0.38} />
            </g>
            <g transform="translate(31 -25)">
              <ellipse rx={18} ry={15 * eyeOpen} fill="#F6F7FF" />
              <ellipse rx={18} ry={15 * eyeOpen} fill="none" stroke="#C9D2F0" strokeWidth={1.8} opacity={0.78} />
              <circle cx={pupilOffsetX} cy={pupilOffsetY} r={7.2 * expression.pupilScale} fill={BG} />
              <circle cx={pupilOffsetX - 2.6} cy={pupilOffsetY - 3.2} r={2.2} fill={WHITE} opacity={0.92} />
              <path d={`M -18 ${-15 * eyeOpen} C -8 ${-21 * eyeOpen} 8 ${-21 * eyeOpen} 18 ${-15 * eyeOpen}`} stroke="#E8ECFF" strokeWidth={2} strokeLinecap="round" opacity={0.38} />
            </g>
            <path
              d={`M -49 ${leftBrowOuterY.toFixed(2)} Q -31 ${browArcY.toFixed(2)} -14 ${leftBrowInnerY.toFixed(2)}`}
              stroke="#E8ECFF"
              strokeWidth={2.8}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              opacity={0.7}
            />
            <path
              d={`M 14 ${rightBrowInnerY.toFixed(2)} Q 31 ${browArcY.toFixed(2)} 49 ${rightBrowOuterY.toFixed(2)}`}
              stroke="#E8ECFF"
              strokeWidth={2.8}
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
              opacity={0.7}
            />
            <path
              d={`M -13 33 Q 0 ${35 + expression.mouthOpen * 12 - expression.mouthCurve * 8} 13 33`}
              fill="none"
              stroke="#DDE6FF"
              strokeWidth={2.4}
              strokeLinecap="round"
              opacity={0.2 + expression.mouthOpen * 0.34 + Math.max(0, expression.mouthCurve) * 0.16}
            />
          </g>
        </g>
      </g>
    </svg>
  );
};
