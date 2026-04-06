"use client";

import { useMemo } from "react";
import type { GoalLineage } from "@/types";

interface GoalLineageGraphProps {
  lineage: GoalLineage;
}

interface PositionedNode {
  goal_id: string;
  title: string;
  progress: number;
  status: string;
  x: number;
  y: number;
}

const NODE_W = 210;
const NODE_H = 78;
const ROOT_X = 300;
const ROOT_Y = 36;
const CHILD_START_X = 56;
const CHILD_GAP = 230;
const CHILD_Y = 188;

function shortId(id: string): string {
  return id.slice(0, 8);
}

export function GoalLineageGraph({ lineage }: GoalLineageGraphProps) {
  const { nodesById, positionedNodes, edges } = useMemo(() => {
    const byId = new Map(lineage.nodes.map((node) => [node.goal_id, node]));

    const root = byId.get(lineage.root_goal_id) || lineage.nodes[0];
    const children = lineage.edges
      .filter((edge) => edge.parent_goal_id === lineage.root_goal_id)
      .map((edge) => byId.get(edge.child_goal_id))
      .filter((node): node is NonNullable<typeof node> => Boolean(node));

    const fallbackNodes = lineage.nodes.filter((node) => node.goal_id !== root?.goal_id);
    const renderChildren = children.length > 0 ? children : fallbackNodes;

    const positioned: PositionedNode[] = [];
    if (root) {
      positioned.push({
        goal_id: root.goal_id,
        title: root.title,
        progress: root.progress,
        status: root.status,
        x: ROOT_X,
        y: ROOT_Y,
      });
    }

    renderChildren.forEach((node, index) => {
      positioned.push({
        goal_id: node.goal_id,
        title: node.title,
        progress: node.progress,
        status: node.status,
        x: CHILD_START_X + index * CHILD_GAP,
        y: CHILD_Y,
      });
    });

    const edgeRows = lineage.edges.filter((edge) => byId.has(edge.parent_goal_id) && byId.has(edge.child_goal_id));

    return {
      nodesById: byId,
      positionedNodes: positioned,
      edges: edgeRows,
    };
  }, [lineage]);

  return (
    <div className="rounded-lg border border-border/70 bg-surface/40 p-3">
      <p className="mb-2 text-sm font-medium text-foreground">Lineage Graph</p>
      <div className="overflow-x-auto">
        <svg width={960} height={340} viewBox="0 0 960 340" className="min-w-[760px]">
          <defs>
            <marker id="lineageArrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
              <path d="M0,0 L0,6 L6,3 z" fill="currentColor" />
            </marker>
          </defs>

          {edges.map((edge, index) => {
            const parent = positionedNodes.find((node) => node.goal_id === edge.parent_goal_id);
            const child = positionedNodes.find((node) => node.goal_id === edge.child_goal_id);
            if (!parent || !child) return null;

            const x1 = parent.x + NODE_W / 2;
            const y1 = parent.y + NODE_H;
            const x2 = child.x + NODE_W / 2;
            const y2 = child.y;
            const midY = (y1 + y2) / 2;

            return (
              <g key={`${edge.parent_goal_id}-${edge.child_goal_id}-${index}`} className="text-muted-foreground">
                <path
                  d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
                  fill="none"
                  stroke="currentColor"
                  strokeWidth={1.4}
                  markerEnd="url(#lineageArrow)"
                />
                <text x={(x1 + x2) / 2} y={midY - 6} textAnchor="middle" className="fill-muted-foreground text-[10px]">
                  {edge.contribution_percentage}%
                </text>
              </g>
            );
          })}

          {positionedNodes.map((node) => {
            const fullNode = nodesById.get(node.goal_id);
            const strokeClass = fullNode?.goal_id === lineage.root_goal_id ? "stroke-primary" : "stroke-border";

            return (
              <g key={node.goal_id}>
                <rect
                  x={node.x}
                  y={node.y}
                  width={NODE_W}
                  height={NODE_H}
                  rx={10}
                  className={`fill-card ${strokeClass}`}
                  strokeWidth={1.2}
                />
                <text x={node.x + 10} y={node.y + 20} className="fill-foreground text-[12px] font-medium">
                  {node.title.slice(0, 28)}
                </text>
                <text x={node.x + 10} y={node.y + 38} className="fill-muted-foreground text-[10px]">
                  {shortId(node.goal_id)}
                </text>
                <text x={node.x + 10} y={node.y + 55} className="fill-muted-foreground text-[10px]">
                  {node.status} | progress {Math.round(node.progress)}%
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
