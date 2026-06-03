import {AbsoluteFill, Audio, Sequence, staticFile} from "remotion";
import type React from "react";
import {Background} from "./Background";
import {accentFor} from "./theme";
import {TEMPLATES, TitleCard} from "./templates";
import type {EpisodeProps} from "./types";

export const Episode: React.FC<EpisodeProps> = ({sections}) => {
  let offset = 0;

  return (
    <AbsoluteFill>
      <Background />
      {sections.map((section, index) => {
        const from = offset;
        offset += section.durationInFrames;
        const Template = TEMPLATES[section.template] ?? TitleCard;

        return (
          <Sequence
            key={`${section.audioSrc}-${index}`}
            from={from}
            durationInFrames={section.durationInFrames}
          >
            {section.audioSrc ? <Audio src={staticFile(section.audioSrc)} /> : null}
            <Template section={section} accent={accentFor(section.accentIndex)} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
