import {Composition} from "remotion";
import type React from "react";
import {Episode} from "./Episode";
import {Short} from "./Short";
import type {EpisodeProps, ShortProps} from "./types";

const defaultProps: EpisodeProps = {
  fps: 30,
  width: 1920,
  height: 1080,
  sections: [
    {
      durationInFrames: 150,
      audioSrc: "",
      template: "title_card",
      key_phrase: "COSMIC QUESTION",
      on_screen: {subtitle: "A motion graphics preview"},
      accentIndex: 0,
    },
  ],
};

const defaultShortProps: ShortProps = {
  fps: 30,
  sections: [
    {
      durationInFrames: 150,
      audioSrc: "",
      key_phrase: "COSMIC QUESTION",
      captions: [
        {
          text: "A motion graphics preview",
          start: 0,
          end: 5,
        },
      ],
    },
  ],
};

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="Episode"
        component={Episode}
        defaultProps={defaultProps}
        calculateMetadata={({props}) => {
          const episodeProps = props as EpisodeProps;
          const sections = episodeProps.sections.length > 0 ? episodeProps.sections : defaultProps.sections;
          return {
            fps: episodeProps.fps || 30,
            width: episodeProps.width || 1920,
            height: episodeProps.height || 1080,
            durationInFrames: sections.reduce((sum, section) => sum + section.durationInFrames, 0),
          };
        }}
      />
      <Composition
        id="Short"
        component={Short}
        defaultProps={defaultShortProps}
        calculateMetadata={({props}) => {
          const shortProps = props as ShortProps;
          const sections = shortProps.sections.length > 0 ? shortProps.sections : defaultShortProps.sections;
          return {
            fps: shortProps.fps || 30,
            width: 1080,
            height: 1920,
            durationInFrames: sections.reduce((sum, section) => sum + section.durationInFrames, 0),
          };
        }}
      />
    </>
  );
};
