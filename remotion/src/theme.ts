import {loadFont} from "@remotion/google-fonts/Inter";
import type React from "react";

export const BG = "#0D0D1A";
export const WHITE = "#FFFFFF";
export const MUTED = "#A9B0C7";
export const ACCENTS = ["#FFD166", "#06D6A0", "#EF476F", "#9B5DE5"];

const {fontFamily} = loadFont("normal", {
  weights: ["400", "700", "800", "900"],
  subsets: ["latin"],
  ignoreTooManyRequestsWarning: true,
});

export {fontFamily};

export const accentFor = (index: number): string => ACCENTS[index % ACCENTS.length];

export const surface = (accent: string): React.CSSProperties => ({
  background: "rgba(13, 13, 26, 0.72)",
  border: `2px solid ${accent}55`,
  boxShadow: `0 0 42px ${accent}24`,
  backdropFilter: "blur(8px)",
});
