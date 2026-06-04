import type {Point} from "./rigTypes";

const control = (previous: Point, next: Point, tension: number): Point => ({
  x: (next.x - previous.x) * tension,
  y: (next.y - previous.y) * tension,
});

export const catmullRomToBezierPath = (points: Point[], tension = 1 / 6): string => {
  if (points.length < 2) {
    return "";
  }

  const commands = [`M ${points[0].x.toFixed(2)} ${points[0].y.toFixed(2)}`];
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[Math.max(0, i - 1)];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[Math.min(points.length - 1, i + 2)];
    const c1 = control(p0, p2, tension);
    const c2 = control(p1, p3, tension);
    const b1 = {x: p1.x + c1.x, y: p1.y + c1.y};
    const b2 = {x: p2.x - c2.x, y: p2.y - c2.y};
    commands.push(
      `C ${b1.x.toFixed(2)} ${b1.y.toFixed(2)} ${b2.x.toFixed(2)} ${b2.y.toFixed(2)} ${p2.x.toFixed(2)} ${p2.y.toFixed(2)}`,
    );
  }

  return commands.join(" ");
};
