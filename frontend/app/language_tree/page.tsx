"use client";

import { useEffect, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  MarkerType,
  Position,
} from "reactflow";
import dagre from "dagre";
import "reactflow/dist/style.css";

type RelationshipMsg = {
  type: string;
  data: {
    entity1: string;
    relationship: string;
    entity2: string;
  };
};

const relationshipColors: Record<string, string> = {
  belongs_to: "#2563eb", // blue
  descended_from: "#16a34a", // green
  dialect_of: "#dc2626", // red
  default: "#6b7280", // gray
};

// Dagre graph setup
const dagreGraph = new dagre.graphlib.Graph().setDefaultEdgeLabel(() => ({}));
const nodeWidth = 180;
const nodeHeight = 40;

function applyLayout(nodes: Node[], edges: Edge[]) {
  dagreGraph.setGraph({ rankdir: "TB" }); // Top -> Bottom layout

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return nodes.map((node) => {
    const pos = dagreGraph.node(node.id);
    return {
      ...node,
      position: { x: pos.x - nodeWidth / 2, y: pos.y - nodeHeight / 2 },
      targetPosition: Position.Top,
      sourcePosition: Position.Bottom,
    };
  });
}

export default function Page() {
  const [language, setLanguage] = useState("English");
  const [depth, setDepth] = useState(2);
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const seenRelationships = useRef<Set<string>>(new Set());

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const updateGraph = (entity1: string, rel: string, entity2: string) => {
    const key = `${entity1}-${rel}-${entity2}`;
    const reverseKey =
      rel === "belongs_to"
        ? `${entity2}-descended_from-${entity1}`
        : rel === "descended_from"
        ? `${entity2}-belongs_to-${entity1}`
        : "";

    if (
      seenRelationships.current.has(key) ||
      (reverseKey && seenRelationships.current.has(reverseKey))
    ) {
      return;
    }

    seenRelationships.current.add(key);

    setNodes((prevNodes) => {
      const exists = (id: string) => prevNodes.some((n) => n.id === id);
      const newNodes = [...prevNodes];
      if (!exists(entity1)) {
        newNodes.push({
          id: entity1,
          data: { label: entity1 },
          position: { x: 0, y: 0 }, // will be updated by dagre
        });
      }
      if (!exists(entity2)) {
        newNodes.push({
          id: entity2,
          data: { label: entity2 },
          position: { x: 0, y: 0 }, // will be updated by dagre
        });
      }

      const newEdges = [
        ...edges,
        {
          id: key,
          source: entity1,
          target: entity2,
          label: rel,
          animated: true,
          style: {
            stroke: relationshipColors[rel] || relationshipColors.default,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: relationshipColors[rel] || relationshipColors.default,
          },
        },
      ];

      // Apply dagre layout
      const laidOutNodes = applyLayout(newNodes, newEdges);
      setEdges(newEdges);
      return laidOutNodes;
    });
  };

  const connectWebSocket = () => {
    setNodes([]);
    setEdges([]);
    seenRelationships.current.clear();

    const ws = new WebSocket("ws://localhost:8001/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(`${language},${depth}`);
    };

    ws.onmessage = (event) => {
      const msg: RelationshipMsg = JSON.parse(event.data);
      if (msg.type === "relationship") {
        const { entity1, relationship, entity2 } = msg.data;
        updateGraph(entity1, relationship, entity2);
      } else if (msg.type === "complete") {
        console.log("Tree exploration complete.");
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error", err);
    };

    ws.onclose = () => {
      console.log("WebSocket closed");
    };
  };

  return (
    <div className="h-screen flex flex-col">
      <div className="p-4 flex gap-2 bg-gray-100 border-b">
        <input
          type="text"
          value={language}
          onChange={(e) => setLanguage(e.target.value)}
          placeholder="Enter language name"
          className="px-3 py-2 border rounded w-48"
        />
        <input
          type="number"
          min={1}
          max={5}
          value={depth}
          onChange={(e) => setDepth(Number(e.target.value))}
          className="px-3 py-2 border rounded w-20"
        />
        <button
          onClick={connectWebSocket}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Explore
        </button>
      </div>
      <div className="flex-1">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          fitView
          attributionPosition="top-right"
        >
          <Background />
          <Controls />
          <MiniMap
            nodeStrokeWidth={3}
            nodeColor={(n) => "#1d4ed8"}
            maskColor="rgba(0,0,0,0.1)"
          />
        </ReactFlow>
      </div>
    </div>
  );
}
