/**
 * CLEAN FLAT / LIGHT theme - the locked visual system for the cutaway engine.
 * Bold geometric shapes, thick confident outlines, warm off-white canvas.
 * Distinct from CGP Grey (structured + bold, not loose + doodly).
 */
import {loadFont} from "@remotion/google-fonts/Inter";

const {fontFamily} = loadFont("normal", {
  weights: ["400", "600", "700", "800", "900"],
  subsets: ["latin"],
  ignoreTooManyRequestsWarning: true,
});

export {fontFamily};

// --- core palette -----------------------------------------------------------
export const PAPER = "#F7F4EC"; // warm off-white canvas
export const PAPER_DEEP = "#ECE6D6"; // slightly deeper panel fill
export const INK = "#1E1E24"; // near-black outline + text
export const INK_SOFT = "#5B5B66"; // muted text

// accent ramp - coral is primary; the rest are sparing supporting hues
export const CORAL = "#FF5A3C"; // primary accent
export const TEAL = "#1FB6A6";
export const GOLD = "#FFC23B";
export const BLUE = "#2D6CDF";
export const PLUM = "#7A5BD8";

export const ACCENTS = [CORAL, TEAL, BLUE, GOLD, PLUM] as const;
export const accentFor = (i: number): string => ACCENTS[((i % ACCENTS.length) + ACCENTS.length) % ACCENTS.length];

// --- line + shape language --------------------------------------------------
// Outlines are thick and confident. Stroke widths are tuned for a 1920x1080 world.
export const STROKE = 7; // default outline weight
export const STROKE_BOLD = 11; // hero shapes
export const STROKE_THIN = 4; // small detail

export const RADIUS = 28; // default corner rounding for rects

// A flat, offset drop shadow (no blur-heavy effects) - gives the bold-sticker feel.
export const dropShadow = (dx = 0, dy = 10, color = INK): string =>
  `drop-shadow(${dx}px ${dy}px 0px ${color}1A)`;

// Soft paper vignette so the off-white isn't dead flat.
export const paperBackground = (): React.CSSProperties => ({
  background: `radial-gradient(120% 120% at 50% 18%, #FBF9F3 0%, ${PAPER} 52%, ${PAPER_DEEP} 100%)`,
});

import type React from "react";
