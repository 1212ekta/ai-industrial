"use client";

import { useEffect, useState } from "react";
import ReactFlow, { Background, Controls, MiniMap } from "reactflow";
import "reactflow/dist/style.css";
import api from "@/lib/api";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";

export default function GraphPage() {
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/graph").then(res => {
      const data = res.data;
      
      // Transform Neo4j data to ReactFlow format
      const rfNodes = data.nodes.map((n: any, i: number) => ({
        id: n.id,
        data: { label: n.properties.name || n.properties.type || n.id },
        position: { x: Math.random() * 500, y: Math.random() * 500 },
        style: {
          background: n.labels.includes("Equipment") ? "#3b82f6" : n.labels.includes("Failure") ? "#ef4444" : "#10b981",
          color: "white",
          borderRadius: "8px",
          padding: "10px",
          border: "1px solid rgba(255,255,255,0.2)"
        }
      }));

      const rfEdges = data.edges.map((e: any) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        label: e.type,
        animated: true,
        style: { stroke: '#888' }
      }));

      setNodes(rfNodes);
      setEdges(rfEdges);
      setLoading(false);
    }).catch(console.error);
  }, []);

  return (
    <div className="h-full w-full flex flex-col space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Knowledge Graph</h1>
      </div>
      
      <Card className="flex-1 border-border/50 bg-background/50 overflow-hidden relative">
        {loading ? (
          <div className="absolute inset-0 flex items-center justify-center text-muted-foreground animate-pulse">
            Generating Graph...
          </div>
        ) : (
          <ReactFlow nodes={nodes} edges={edges} fitView>
            <Background color="#333" gap={16} />
            <Controls className="bg-card border-border fill-foreground" />
            <MiniMap className="bg-card border-border" />
          </ReactFlow>
        )}
      </Card>
    </div>
  );
}
