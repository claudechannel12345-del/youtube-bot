/**
 * GPS cold-open - STYLE PROOF for the clean-flat cutaway engine.
 * ~20s, 4 cutaway beats, hardcoded timing (no audio yet). Silent local render to
 * lock the look before building the director/persona pipeline.
 */
import type React from "react";
import {AbsoluteFill, interpolate, Sequence, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {
  Building,
  ClockFace,
  EarthArc,
  GroundShadow,
  LocationDot,
  Person,
  Phone,
  Satellite,
  SignalWaves,
  SpeechBubble,
  Star,
} from "./primitives";
import {CORAL, fontFamily, INK, INK_SOFT, paperBackground, STROKE_BOLD} from "./theme";

const W = 1920;
const H = 1080;

const Stage: React.FC<{children: React.ReactNode}> = ({children}) => (
  <svg viewBox={`0 0 ${W} ${H}`} width="100%" height="100%">
    {children}
  </svg>
);

// fade content in at beat start, out at beat end, for clean cuts
const useBeatOpacity = (len: number): number => {
  const f = useCurrentFrame();
  return interpolate(f, [0, 10, len - 8, len], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
};

const Caption: React.FC<{children: React.ReactNode; len: number}> = ({children, len}) => {
  const f = useCurrentFrame();
  const y = interpolate(f, [0, 14], [40, 0], {extrapolateRight: "clamp"});
  const op = interpolate(f, [0, 14, len - 8, len], [0, 1, 1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  return (
    <AbsoluteFill style={{justifyContent: "flex-end", alignItems: "center", paddingBottom: 96}}>
      <div
        style={{
          transform: `translateY(${y}px)`,
          opacity: op,
          maxWidth: 1320,
          textAlign: "center",
          fontFamily,
          fontWeight: 800,
          fontSize: 56,
          lineHeight: 1.12,
          color: INK,
          letterSpacing: -0.5,
        }}
      >
        {children}
      </div>
    </AbsoluteFill>
  );
};

const Hi: React.FC<{children: React.ReactNode}> = ({children}) => (
  <span style={{color: CORAL}}>{children}</span>
);

// --- Beat 1: sidewalk + location dot ---------------------------------------
const BeatSidewalk: React.FC = () => {
  const f = useCurrentFrame();
  const op = useBeatOpacity(135);
  const cam = interpolate(f, [0, 135], [1, 1.06]);
  const pulse = (f / 45) % 1;
  return (
    <AbsoluteFill style={{opacity: op}}>
      <Stage>
        <g transform={`translate(${W / 2} ${H / 2}) scale(${cam}) translate(${-W / 2} ${-H / 2})`}>
          <Building x={250} y={390} w={230} h={470} />
          <Building x={520} y={280} w={200} h={580} />
          <Building x={1230} y={330} w={220} h={530} />
          <Building x={1480} y={430} w={210} h={430} />
          {/* ground */}
          <path d={`M 120 860 L 1800 860`} stroke={INK} strokeWidth={STROKE_BOLD} strokeLinecap="round" />
          <GroundShadow x={960} y={864} rx={84} ry={15} />
          <Person x={960} y={665} scale={1.6} />
          <LocationDot x={960} y={905} pulse={pulse} />
        </g>
      </Stage>
      <Caption len={135}>
        Right now, a <Hi>dot on your phone</Hi> knows exactly where you're standing.
      </Caption>
    </AbsoluteFill>
  );
};

// --- Beat 2: phone is listening --------------------------------------------
const BeatPhone: React.FC = () => {
  const {fps} = useVideoConfig();
  const f = useCurrentFrame();
  const op = useBeatOpacity(150);
  const rise = spring({frame: f, fps, config: {damping: 14}});
  const py = interpolate(rise, [0, 1], [620, 540]);
  const prog = (f / 50) % 1;
  return (
    <AbsoluteFill style={{opacity: op}}>
      <Stage>
        <SignalWaves x={960} y={py - 250} progress={prog} startAngle={-150} sweep={120} spread={420} count={4} />
        <GroundShadow x={960} y={py + 286} rx={150} ry={20} />
        <Phone x={960} y={py} scale={0.92} dotPulse={(f / 45) % 1} />
      </Stage>
      <Caption len={150}>
        Your phone isn't tracking you. It's <Hi>listening</Hi>.
      </Caption>
    </AbsoluteFill>
  );
};

// --- Beat 3: pull back to the satellite fleet ------------------------------
const BeatOrbit: React.FC = () => {
  const f = useCurrentFrame();
  const op = useBeatOpacity(165);
  const cam = interpolate(f, [0, 70], [1.5, 1], {extrapolateRight: "clamp"});
  const prog = (f / 60) % 1;
  return (
    <AbsoluteFill style={{opacity: op, ...paperBackground()}}>
      <Stage>
        <g transform={`translate(${W / 2} ${H * 0.72}) scale(${cam}) translate(${-W / 2} ${-H * 0.72})`}>
          <Star x={300} y={180} s={12} />
          <Star x={620} y={110} s={9} />
          <Star x={1500} y={150} s={13} />
          <Star x={1750} y={300} s={8} />
          <Star x={180} y={420} s={8} />
          <EarthArc cx={960} cy={1760} r={980} />
          <Satellite x={520} y={360} scale={0.9} rotate={-12} />
          <Satellite x={1380} y={300} scale={1.05} rotate={10} />
          <Satellite x={980} y={210} scale={0.78} rotate={-4} />
          <SignalWaves x={520} y={400} progress={prog} startAngle={40} sweep={90} spread={260} count={3} color={CORAL} />
          <SignalWaves x={1380} y={340} progress={(prog + 0.4) % 1} startAngle={70} sweep={90} spread={260} count={3} color={CORAL} />
        </g>
      </Stage>
      <Caption len={165}>
        20,000 km up, a fleet of satellites does exactly one thing: <Hi>shout the time</Hi>.
      </Caption>
    </AbsoluteFill>
  );
};

// --- Beat 4: one satellite, an atomic clock, a speech bubble ----------------
const BeatClock: React.FC = () => {
  const {fps} = useVideoConfig();
  const f = useCurrentFrame();
  const op = useBeatOpacity(150);
  const pop = spring({frame: f - 6, fps, config: {damping: 12}});
  const t = (f / fps) % 1;
  return (
    <AbsoluteFill style={{opacity: op}}>
      <Stage>
        <Satellite x={460} y={300} scale={1.15} rotate={-8} />
        <g transform={`translate(960 560) scale(${0.4 + pop * 0.6}) translate(-960 -560)`}>
          <ClockFace x={760} y={600} r={170} t={t} />
        </g>
        <SpeechBubble x={1050} y={300} w={640} h={210} tailX={980} tailY={620} fontFamily={fontFamily}>
          "It is 12:00:00.000... and I am right HERE."
        </SpeechBubble>
        <text
          x={760}
          y={840}
          textAnchor="middle"
          fontFamily={fontFamily}
          fontWeight={700}
          fontSize={30}
          fill={INK_SOFT}
        >
          atomic clock, accurate to a billionth of a second
        </text>
      </Stage>
      <Caption len={150}>
        Each one carries an <Hi>atomic clock</Hi> and screams it, over and over.
      </Caption>
    </AbsoluteFill>
  );
};

export const GpsProof: React.FC = () => {
  return (
    <AbsoluteFill style={paperBackground()}>
      <Sequence durationInFrames={135}>
        <BeatSidewalk />
      </Sequence>
      <Sequence from={135} durationInFrames={150}>
        <BeatPhone />
      </Sequence>
      <Sequence from={285} durationInFrames={165}>
        <BeatOrbit />
      </Sequence>
      <Sequence from={450} durationInFrames={150}>
        <BeatClock />
      </Sequence>
    </AbsoluteFill>
  );
};
