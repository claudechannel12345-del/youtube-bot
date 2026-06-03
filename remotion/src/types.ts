export type Section = {
  durationInFrames: number;
  audioSrc: string;
  template: string;
  key_phrase: string;
  on_screen: Record<string, unknown>;
  accentIndex: number;
};

export type EpisodeProps = {
  fps: number;
  width: number;
  height: number;
  sections: Section[];
};

export type TemplateProps = {
  section: Section;
  accent: string;
};

export type ShortCaption = {
  text: string;
  start: number;
  end: number;
};

export type ShortSection = {
  durationInFrames: number;
  audioSrc: string;
  key_phrase: string;
  captions: ShortCaption[];
};

export type ShortProps = {
  fps: number;
  sections: ShortSection[];
};
