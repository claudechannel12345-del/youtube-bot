import type React from "react";
import type {TemplateProps} from "../types";
import {Comparison} from "./Comparison";
import {Diagram} from "./Diagram";
import {ImageFocus} from "./ImageFocus";
import {ListReveal} from "./ListReveal";
import {MapHighlight} from "./MapHighlight";
import {Process} from "./Process";
import {Quote} from "./Quote";
import {StatReveal} from "./StatReveal";
import {Timeline} from "./Timeline";
import {TitleCard} from "./TitleCard";

export {TitleCard};

export const TEMPLATES: Record<string, React.FC<TemplateProps>> = {
  title_card: TitleCard,
  stat_reveal: StatReveal,
  comparison: Comparison,
  timeline: Timeline,
  process: Process,
  quote: Quote,
  list: ListReveal,
  map: MapHighlight,
  diagram: Diagram,
  image_focus: ImageFocus,
};
