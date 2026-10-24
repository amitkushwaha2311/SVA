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
    <div className="px-4 py-2.5 shadow-xl rounded-xl bg-[#211B16] border border-[#514236] min-w-[200px] hover:border-[#F4D9A0]/60 transition-colors">
      <Handle type="target" position={Position.Top} className="w-16 !bg-[#514236]" />
      <div className="flex flex-col">
        <div className="text-[10px] font-mono text-[#847768] uppercase tracking-widest font-medium">{nodeData.typeLabel}</div>
        <div className="text-sm font-serif font-medium text-[#F5EFE5] mt-1 truncate max-w-[180px]">{nodeData.label}</div>
        {nodeData.status && (
          <div className="mt-2 text-[10px] font-mono tracking-widest text-[#B5AA9C]">
            STATUS: <span className="text-[#10B981] font-semibold">{nodeData.status}</span>
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} className="w-16 !bg-[#514236]" />
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
      <div className="flex-1 flex items-center justify-center h-full bg-[#17130F]">
        <div className="animate-pulse flex flex-col items-center gap-4 text-[#847768]">
          <div className="w-12 h-12 bg-[#2A221B] rounded-xl border border-[#514236]" />
          <span className="font-mono text-xs">Loading assurance topology...</span>
        </div>
      </div>
    );
  }

  if (!activeAnalysis) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center h-full p-12 text-center bg-[#17130F]">
        <div className="w-16 h-16 bg-[#211B16] border border-[#514236] rounded-2xl flex items-center justify-center mb-6 shadow-md">
          <div className="w-8 h-8 rounded-full bg-[#514236]/50" />
        </div>
        <div className="font-mono text-xs uppercase tracking-widest text-[#847768] mb-2 font-medium">No Assurance Graph</div>
        <p className="text-[#B5AA9C] max-w-sm text-sm leading-relaxed">
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
        className="bg-[#17130F]"
        colorMode="dark"
      >
        <Controls showInteractive={false} className="!bg-[#2A221B] !border-[#514236] !text-[#F5EFE5] !rounded-xl overflow-hidden" />
        <MiniMap 
          nodeColor="#514236" 
          maskColor="rgba(23, 19, 15, 0.75)"
          className="!bg-[#211B16] !border-[#514236] !rounded-xl"
        />
        <Background gap={18} size={1} color="#514236" />
      </ReactFlow>
    </div>
  );
}
