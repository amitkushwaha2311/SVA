"use client";

import { useCallback, useState } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  Connection,
  Edge,
  Handle,
  Position,
  NodeProps,
  Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

interface SVANodeData {
  label: string;
  typeLabel: string;
  status?: string;
}

const SVANode = ({ data }: NodeProps) => {
  const nodeData = data as unknown as SVANodeData;
  return (
    <div className="px-4 py-2 shadow-md rounded-md bg-[#12151A] border border-[#20242B] min-w-[200px]">
      <Handle type="target" position={Position.Top} className="w-16 !bg-[#20242B]" />
      <div className="flex flex-col">
        <div className="text-[10px] font-mono text-[#5F6773] uppercase tracking-widest">{nodeData.typeLabel}</div>
        <div className="text-sm font-bold text-[#F5F7FA] mt-1 truncate max-w-[180px]">{nodeData.label}</div>
        {nodeData.status && (
          <div className="mt-2 text-[10px] font-mono tracking-widest text-[#8B93A1]">
            STATUS: <span className="text-[#10B981]">{nodeData.status}</span>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-16 !bg-[#20242B]" />
    </div>
  );
};

const nodeTypes = {
  sva: SVANode,
};

const initialNodes = [
  {
    id: "intent-1",
    type: "sva",
    position: { x: 250, y: 0 },
    data: { label: "Only project owners can delete projects", typeLabel: "Intent", status: "HUMAN_CONFIRMED" },
  },
  {
    id: "req-1",
    type: "sva",
    position: { x: 250, y: 150 },
    data: { label: "REQ-001", typeLabel: "Requirement", status: "PROVEN" },
  },
  {
    id: "contract-1",
    type: "sva",
    position: { x: 250, y: 300 },
    data: { label: "CON-001", typeLabel: "Contract", status: "READY" },
  },
  {
    id: "evidence-1",
    type: "sva",
    position: { x: 100, y: 450 },
    data: { label: "EV-82931 (Owner)", typeLabel: "Evidence", status: "VERIFIED" },
  },
  {
    id: "evidence-2",
    type: "sva",
    position: { x: 400, y: 450 },
    data: { label: "EV-82932 (Non-owner)", typeLabel: "Evidence", status: "VERIFIED" },
  }
];

const initialEdges = [
  { id: "e1-2", source: "intent-1", target: "req-1", animated: false, style: { stroke: "#20242B" } },
  { id: "e2-3", source: "req-1", target: "contract-1", animated: false, style: { stroke: "#20242B" } },
  { id: "e3-4", source: "contract-1", target: "evidence-1", animated: false, style: { stroke: "#20242B" } },
  { id: "e3-5", source: "contract-1", target: "evidence-2", animated: false, style: { stroke: "#20242B" } },
];

export function AssuranceGraph() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(initialNodes as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(initialEdges as Edge[]);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div style={{ width: "100%", height: "100%" }} className="react-flow-dark">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="bg-[#08090B]"
        colorMode="dark"
      >
        <Controls showInteractive={false} className="!bg-[#12151A] !border-[#20242B]" />
        <MiniMap 
          nodeColor="#20242B" 
          maskColor="rgba(8, 9, 11, 0.7)"
          className="!bg-[#0D0F12] !border-[#20242B]"
        />
        <Background gap={16} size={1} color="#20242B" />
      </ReactFlow>
    </div>
  );
}
