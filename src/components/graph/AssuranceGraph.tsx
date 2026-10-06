"use client";

import { useCallback, useState, useEffect } from "react";
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
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { useWorkspace, useRepository } from "@/components/providers";

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
  intent: SVANode,
  contract: SVANode,
};

export function AssuranceGraph() {
  const { activeWorkspace } = useWorkspace();
  const { activeAnalysis, isRepoLoading } = useRepository();

  const { data, isLoading } = useQuery({
    queryKey: ["graph", activeWorkspace?.id, activeAnalysis?.id],
    enabled: !!activeWorkspace?.id && !!activeAnalysis?.id,
    queryFn: () =>
      apiFetch<{ nodes: any[]; edges: any[] }>(
        `/v1/analyses/${activeAnalysis!.id}/graph?workspace_id=${activeWorkspace!.id}`
      ).catch(() => ({ nodes: [], edges: [] })),
    retry: false,
  });

  const initialNodes = data?.nodes || [];
  const initialEdges = data?.edges || [];

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>(initialNodes as Node[]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>(initialEdges as Edge[]);

  // Update when data changes
  useEffect(() => {
    setNodes(initialNodes as Node[]);
    setEdges(initialEdges as Edge[]);
  }, [data, setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  if (isRepoLoading || isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center h-full">
        <div className="animate-pulse flex flex-col items-center gap-4 text-[#5F6773]">
          <div className="w-12 h-12 bg-[#12151A] rounded-lg border border-[#20242B]" />
          Loading assurance graph...
        </div>
      </div>
    );
  }

  if (!activeAnalysis) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full p-12 text-center bg-[#08090B]">
        <div className="w-16 h-16 bg-[#12151A] border border-[#20242B] rounded-xl flex items-center justify-center mb-6 shadow-md">
          <div className="w-8 h-8 text-[#5F6773]" />
        </div>
        <div className="font-mono text-xs uppercase tracking-widest text-[#5F6773] mb-2">No Assurance Graph</div>
        <p className="text-[#8B93A1] max-w-sm text-sm leading-relaxed">
          No analysis has been completed for this repository yet. Run an analysis to generate the assurance graph.
        </p>
      </div>
    );
  }

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
