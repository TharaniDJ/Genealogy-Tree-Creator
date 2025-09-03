"use client";

import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import ReactFlow, {
  Controls,
  Background,
  addEdge,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  Node,
  Edge,
  Connection,
  Position,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { useWebSocket } from '../../hooks/useWebSocket';
import LanguageNode from '../../components/LanguageNode';

// Dagre layouting
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 172;
const nodeHeight = 36;

type LanguageNodeData = { label: string; meta?: string };
type LanguageRFNode = Node<LanguageNodeData>;

const getLayoutedElements = (nodes: LanguageRFNode[], edges: Edge[], direction = 'TB') => {
  const isHorizontal = direction === 'LR';
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach(node => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });
  edges.forEach(edge => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  nodes.forEach(node => {
    const pos = dagreGraph.node(node.id);
    if (!pos) return;
    node.targetPosition = isHorizontal ? Position.Left : Position.Top;
    node.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;
    node.position = { x: pos.x - nodeWidth / 2, y: pos.y - nodeHeight / 2 };
  });
  return { nodes, edges };
};


const LanguageTreePage = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState<LanguageNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
  const [language, setLanguage] = useState('English');
  const [depth, setDepth] = useState(2);
  const [status, setStatus] = useState('Not connected');
  const [progress, setProgress] = useState(0);
  const [layoutDirection, setLayoutDirection] = useState<'TB' | 'LR'>('TB');
  const [autoLayoutOnComplete, setAutoLayoutOnComplete] = useState(true);

  const { messages, connectionStatus, connect, disconnect, sendMessage } = useWebSocket('ws://localhost:8001/ws/relationships');

  // Track which messages have been processed to avoid losing earlier batches when multiple arrive quickly.
  const lastProcessedIndexRef = useRef(0);
  // Track search session start to ignore old messages from prior sessions if needed.
  const searchSessionStartRef = useRef(0);
  const completeRef = useRef(false);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  const nodeTypes = useMemo(() => ({ language: LanguageNode }), []);

  const layout = useCallback((direction: 'TB' | 'LR' = layoutDirection) => {
    setNodes(prevNodes => {
      setEdges(prevEdges => {
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements([...prevNodes.map(n => ({ ...n }))], [...prevEdges], direction);
        // Replace with layouted versions
        setNodes(layoutedNodes);
        return layoutedEdges;
      });
      return prevNodes; // actual replacement done above
    });
  }, [layoutDirection, setNodes, setEdges]);

  // Process ALL new messages since lastProcessedIndex to avoid dropping batches.
  useEffect(() => {
    if (!messages.length) return;

    for (let i = lastProcessedIndexRef.current; i < messages.length; i++) {
      const message = messages[i];
      if (!message) continue;
      // Skip messages that belong to a previous session
      if (i < searchSessionStartRef.current) continue;

      switch (message.type) {
        case 'status': {
          setStatus(message.data.message);
          setProgress(message.data.progress);
          break; }
        case 'base_language': {
          setNodes(prev => {
            if (prev.some(n => n.id === message.data.glottocode)) return prev;
            const newNode: LanguageRFNode = {
              id: message.data.glottocode,
              data: { label: `${message.data.name} (${message.data.level})` },
              position: { x: 0, y: 0 },
              type: 'language',
            };
            return [...prev, newNode];
          });
          break; }
        case 'relationships_batch': {
          const batch = message.data || [];
          if (!Array.isArray(batch)) break;

          // Deduplicate within batch first
          const nodeAdditions: Record<string, LanguageRFNode> = {};
            const edgeAdditions: Record<string, Edge> = {};
          for (const rel of batch) {
            const sourceId = rel.entity1_glottocode;
            const targetId = rel.entity2_glottocode;
            if (!sourceId || !targetId) continue;

            if (sourceId && rel.entity1 && !nodeAdditions[sourceId]) {
              nodeAdditions[sourceId] = { id: sourceId, data: { label: rel.entity1 }, position: { x: 0, y: 0 }, type: 'language' };
            }
            if (targetId && rel.entity2 && !nodeAdditions[targetId]) {
              nodeAdditions[targetId] = { id: targetId, data: { label: rel.entity2 }, position: { x: 0, y: 0 }, type: 'language' };
            }
            const edgeId = `e-${sourceId}-${targetId}`;
            if (!edgeAdditions[edgeId]) {
              edgeAdditions[edgeId] = { id: edgeId, source: sourceId, target: targetId, type: 'smoothstep', animated: true };
            }
          }

          setNodes(prev => {
            const existingIds = new Set(prev.map(n => n.id));
            const toAdd = Object.values(nodeAdditions).filter(n => !existingIds.has(n.id));
            if (toAdd.length) console.debug(`[RF] Adding ${toAdd.length} new nodes (total -> ${prev.length + toAdd.length}).`);
            return toAdd.length ? [...prev, ...toAdd] : prev;
          });
          setEdges(prev => {
            const existingIds = new Set(prev.map(e => e.id));
            const toAdd = Object.values(edgeAdditions).filter(e => !existingIds.has(e.id));
            if (toAdd.length) console.debug(`[RF] Adding ${toAdd.length} new edges (total -> ${prev.length + toAdd.length}).`);
            return toAdd.length ? [...prev, ...toAdd] : prev;
          });
          break; }
        case 'complete': {
          completeRef.current = true;
          setStatus('Completed');
          setProgress(100);
          if (autoLayoutOnComplete) {
            // Delay to ensure final nodes/edges states are committed
            setTimeout(() => layout(), 0);
          }
          break; }
        case 'error': {
          setStatus(`Error: ${message.data.message}`);
          setProgress(100);
          break; }
        default:
          break;
      }
    }
    lastProcessedIndexRef.current = messages.length;
  }, [messages, autoLayoutOnComplete, layout, setNodes, setEdges]);

  const handleSearch = useCallback(() => {
    console.info(`[RF] New search: language='${language}', depth=${depth}`);
    setNodes([]);
    setEdges([]);
    setStatus('Searching...');
    setProgress(0);
    completeRef.current = false;
    // Start indexing new messages from current length to ignore any leftover old messages.
    searchSessionStartRef.current = messages.length;
    lastProcessedIndexRef.current = messages.length;
    sendMessage(`${language},${depth}`);
  }, [language, depth, messages.length, sendMessage, setNodes, setEdges]);

  const changeLayout = (dir: 'TB' | 'LR') => {
    setLayoutDirection(dir);
    layout(dir);
  };

  return (
    <div style={{ height: '100vh', width: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '10px', display: 'flex', gap: '10px', alignItems: 'center', borderBottom: '1px solid #eee' }}>
        <input 
          type="text" 
          value={language} 
          onChange={(e) => setLanguage(e.target.value)} 
          placeholder="Language name"
          style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc' }}
        />
        <input 
          type="number" 
          value={depth} 
          onChange={(e) => setDepth(parseInt(e.target.value, 10))}
          placeholder="Depth"
          style={{ padding: '8px', borderRadius: '4px', border: '1px solid #ccc', width: '80px' }}
        />
        <button onClick={handleSearch} disabled={connectionStatus !== 'connected'} style={{ padding: '8px 12px', borderRadius: '4px', border: 'none', background: '#007bff', color: 'white', cursor: 'pointer' }}>
          {connectionStatus === 'connected' ? 'Explore' : 'Connecting...'}
        </button>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '5px' }}>
            <div style={{ fontSize: '14px' }}>{status}</div>
            <div style={{ width: '100%', background: '#eee', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ width: `${progress}%`, background: '#007bff', height: '10px', transition: 'width 0.2s' }} />
            </div>
        </div>
        <button onClick={() => changeLayout('TB')} style={{ padding: '8px 12px' }}>Vertical Layout</button>
        <button onClick={() => changeLayout('LR')} style={{ padding: '8px 12px' }}>Horizontal Layout</button>
        <label style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 12 }}>
          <input type="checkbox" checked={autoLayoutOnComplete} onChange={e => setAutoLayoutOnComplete(e.target.checked)} /> Auto layout on complete
        </label>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={(params: Connection) => setEdges((eds) => addEdge(params, eds))}
        nodeTypes={nodeTypes}
        fitView
      >
        <Controls />
        <Background />
      </ReactFlow>
    </div>
  );
};

const LanguageTreePageWrapper = () => (
    <ReactFlowProvider>
        <LanguageTreePage />
    </ReactFlowProvider>
);


export default LanguageTreePageWrapper;
