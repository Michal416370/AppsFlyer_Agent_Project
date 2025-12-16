import React from "react";
import { componentMap } from "./componentMap";

type UINode = {
  component: string;
  props?: Record<string, any>;
  children?: UINode[];
};

export const UIRenderer = ({ node }: { node: UINode }) => {
  if (!node) return null;

  const Component = componentMap[node.component];

  if (!Component) {
    return (
      <div style={{ color: "red" }}>
        Unknown component: {node.component}
      </div>
    );
  }

  return (
    <Component {...node.props}>
      {node.children?.map((child, i) => (
        <UIRenderer key={i} node={child} />
      ))}
    </Component>
  );
}