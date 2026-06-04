import {AbsoluteFill} from "remotion";
import type React from "react";
import {BG} from "../theme";

type SceneWorldProps = {
  children: React.ReactNode;
  perspective?: number;
};

export const SceneWorld: React.FC<SceneWorldProps> = ({children, perspective = 1200}) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: BG,
        overflow: "hidden",
        perspective,
        transformStyle: "preserve-3d",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: -90,
          background:
            "radial-gradient(circle at 24% 18%, rgba(155,93,229,0.20), transparent 32%), radial-gradient(circle at 76% 70%, rgba(6,214,160,0.13), transparent 36%), linear-gradient(160deg, #0D0D1A 0%, #111327 52%, #080814 100%)",
          transform: "translateZ(-420px) scale(1.14)",
        }}
      />
      {children}
    </AbsoluteFill>
  );
};
