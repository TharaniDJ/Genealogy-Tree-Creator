"use client";

import React, { useEffect, useRef, useState } from "react";
import ReactFlow, {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
} from "reactflow";
import "reactflow/dist/style.css";

interface Relationship {
  entity1: string;
  relationship: string;
  entity2: string;
}

interface LanguageDetails {
  entity: string;
}

interface LanguageTreeProps {
  websocketData?: { type: string; data: any }[];
  rootLanguage: string;
}

function LanguageTree({ websocketData = [], rootLanguage }: LanguageTreeProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [languageDetails, setLanguageDetails] = useState<Map<string, LanguageDetails>>(new Map());
  const [relationships, setRelationships] = useState<Relationship[]>([]);

  // Process websocket data
  useEffect(() => {
    if (websocketData.length === 0) return;

    const details = new Map(languageDetails);
    const rels = [...relationships];

    websocketData.forEach((msg) => {
      if (msg.type === "relationship") {
        rels.push(msg.data as Relationship);
      } else if (msg.type === "language_details") {
        details.set(msg.data.entity, msg.data);
      }
    });

    setLanguageDetails(details);
    setRelationships(rels);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [websocketData]);

  // Generate graph when relationships or details update
  useEffect(() => {
    if (relationships.length === 0) return;

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];

    const VERTICAL_SPACING = 200;
    const HORIZONTAL_SPACING = 220;

    // BFS to assign depths
    const depths = new Map<string, number>();
    const visited = new Set<string>();
    const queue: { lang: string; depth: number }[] = [{ lang: rootLanguage, depth: 0 }];
    depths.set(rootLanguage, 0);

    while (queue.length > 0) {
      const { lang, depth } = queue.shift()!;
      if (visited.has(lang)) continue;
      visited.add(lang);

      relationships.forEach((rel) => {
        if (rel.entity1 === lang && !depths.has(rel.entity2)) {
          depths.set(rel.entity2, depth + 1);
          queue.push({ lang: rel.entity2, depth: depth + 1 });
        }
        if (rel.entity2 === lang && !depths.has(rel.entity1)) {
          depths.set(rel.entity1, depth + 1);
          queue.push({ lang: rel.entity1, depth: depth + 1 });
        }
      });
    }

    // Group languages by depth
    const grouped: Record<number, string[]> = {} as Record<number, string[]>;
    depths.forEach((depth, lang) => {
      if (!grouped[depth]) grouped[depth] = [];
      grouped[depth].push(lang);
    });

    // Position nodes in grid
    Object.entries(grouped).forEach(([depthStr, langs]) => {
      const depth = parseInt(depthStr);
      langs.forEach((lang, i) => {
        newNodes.push({
          id: lang,
          data: { label: lang },
          position: {
            x: i * HORIZONTAL_SPACING,
            y: depth * VERTICAL_SPACING,
          },
          style: {
            border: lang === rootLanguage ? "2px solid orange" : "1px solid #ccc",
            padding: 8,
            borderRadius: 6,
            background: "#fff",
          },
        });
      });
    });

    // Create edges
    relationships.forEach((rel, i) => {
      newEdges.push({
        id: `edge-${i}`,
        source: rel.entity1,
        target: rel.entity2,
        label: rel.relationship,
        animated: true,
        style: {
          stroke:
            rel.relationship === "belongs_to"
              ? "#2563eb"
              : rel.relationship === "descended_from"
              ? "#16a34a"
              : "#dc2626",
          strokeDasharray: rel.relationship === "dialect_of" ? "5,5" : undefined,
        },
      });
    });

    setNodes(newNodes);
    setEdges(newEdges);
  }, [relationships, languageDetails, rootLanguage, setEdges, setNodes]);

  return (
    <div className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        fitViewOptions={{ padding: 0.3 }}
      >
        <Controls />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}

export default function Page() {
  const [rootLanguage, setRootLanguage] = useState("English");
  const [depth, setDepth] = useState<number>(2);
  const [websocketData, setWebsocketData] = useState<{ type: string; data: any }[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  const connectWebSocket = () => {
    // reset data and close any existing socket
    setWebsocketData([]);
    wsRef.current?.close();

    const ws = new WebSocket("ws://localhost:8001/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(`${rootLanguage},${depth}`);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        setWebsocketData((prev) => [...prev, msg]);
      } catch (e) {
        console.error("Invalid WS message", e);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error", err);
    };

    ws.onclose = () => {
      // no-op
    };
  };

  return (
    <div className="h-screen flex flex-col">
      <div className="p-4 flex gap-2 bg-gray-100 border-b">
        <input
          type="text"
          value={rootLanguage}
          onChange={(e) => setRootLanguage(e.target.value)}
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
        <LanguageTree websocketData={websocketData} rootLanguage={rootLanguage} />
      </div>
    </div>
  );
}
