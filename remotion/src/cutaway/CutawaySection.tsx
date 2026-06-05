import type React from "react";
import {AbsoluteFill, Audio, Sequence, staticFile} from "remotion";
import {CutawayBeat} from "./CutawayBeat";
import type {CutawaySection as CutawaySectionType} from "./types";

export const CutawaySection: React.FC<{section: CutawaySectionType; renderer?: "legacy" | "blueprint"}> = ({section, renderer = "legacy"}) => (
  <Sequence durationInFrames={Math.max(1, section.durationInFrames)}>
    <AbsoluteFill>
      {typeof section.audioSrc === "string" && section.audioSrc.trim().length > 0 ? (
        <Audio src={staticFile(section.audioSrc)} />
      ) : null}
      {section.beats.map((beat) => (
        <CutawayBeat key={beat.id} beat={beat} renderer={renderer} />
      ))}
    </AbsoluteFill>
  </Sequence>
);
