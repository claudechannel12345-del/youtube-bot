import type React from "react";

type DepthPlaneProps = {
  z: number;
  children: React.ReactNode;
};

export const DepthPlane: React.FC<DepthPlaneProps> = ({z, children}) => {
  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        transform: `translateZ(${z}px)`,
        transformStyle: "preserve-3d",
      }}
    >
      {children}
    </div>
  );
};
