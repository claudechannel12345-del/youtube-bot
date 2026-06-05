import type React from "react";
import {AbsoluteFill, Sequence} from "remotion";
import {paperBackground} from "../flat/theme";
import {CutawaySection} from "./CutawaySection";
import type {EpisodeProps} from "./types";

export const CutawayEpisode: React.FC<EpisodeProps> = ({sections, renderer = "legacy"}) => {
  let cursor = 0;
  return (
    <AbsoluteFill style={paperBackground()}>
      {sections.map((section) => {
        const from = cursor;
        cursor += Math.max(1, section.durationInFrames);
        return (
          <Sequence key={section.section_index} from={from} durationInFrames={Math.max(1, section.durationInFrames)}>
            <CutawaySection section={section} renderer={renderer} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
