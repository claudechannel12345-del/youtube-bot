import type {Point} from "./rigTypes";

type IkInput = {
  shoulder: Point;
  target: Point;
  upper: number;
  lower: number;
  bendBias: number;
  side: -1 | 1;
};

export type IkResult = {
  elbow: Point;
  tip: Point;
};

const length = (point: Point): number => Math.hypot(point.x, point.y);

export const solveTwoBoneIk = ({shoulder, target, upper, lower, bendBias, side}: IkInput): IkResult => {
  const dx = target.x - shoulder.x;
  const dy = target.y - shoulder.y;
  const rawDistance = Math.max(0.001, length({x: dx, y: dy}));
  const maxReach = upper + lower;
  const distance = Math.min(rawDistance, maxReach * 0.985);
  const dir = {x: dx / rawDistance, y: dy / rawDistance};
  const tip = {
    x: shoulder.x + dir.x * distance,
    y: shoulder.y + dir.y * distance,
  };
  const cosAngle = Math.max(-1, Math.min(1, (upper * upper + distance * distance - lower * lower) / (2 * upper * distance)));
  const along = cosAngle * upper;
  const height = Math.sqrt(Math.max(0, upper * upper - along * along));
  const normal = {x: -dir.y * side, y: dir.x * side};
  const bend = Math.max(-1, Math.min(1, bendBias));
  const elbow = {
    x: shoulder.x + dir.x * along + normal.x * height * (0.55 + Math.abs(bend) * 0.45) * Math.sign(bend || side),
    y: shoulder.y + dir.y * along + normal.y * height * (0.55 + Math.abs(bend) * 0.45) * Math.sign(bend || side),
  };

  return {elbow, tip};
};
