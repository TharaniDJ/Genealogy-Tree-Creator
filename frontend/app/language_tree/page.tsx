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

  // Mapping label -> node id to avoid duplicates; stored in ref to persist across renders without causing rerenders
  const labelToIdRef = useRef<Map<string,string>>(new Map());
  const idCollisionCounterRef = useRef<Record<string, number>>({});

  const slugify = (label: string) => label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$|/g, '').slice(0,40) || 'lang';

  const ensureNode = useCallback((label: string) => {
    if (!label) return null;
    const map = labelToIdRef.current;
    if (map.has(label)) return map.get(label)!;
    let base = slugify(label);
    // resolve collisions with existing ids mapping to different labels
    let id = base;
    let attempts = 1;
    const existingIds = new Set<string>();
    // collect existing node ids cheaply
    // NOTE: using current nodes state directly is fine inside setNodes callback but here we rely on ref; resolve lazily
    // We'll detect collisions when adding.
    while ([...map.values()].includes(id)) {
      attempts += 1;
      id = `${base}-${attempts}`;
    }
    map.set(label, id);
    setNodes(prev => {
      if (prev.some(n => n.id === id)) return prev;
      return [...prev, { id, data: { label }, position: { x: 0, y: 0 }, type: 'language' }];
    });
    return id;
  }, [setNodes]);

  // Process streaming messages from backend (status, relationship, complete, error)
  useEffect(() => {
    if (!messages.length) return;
    for (let i = lastProcessedIndexRef.current; i < messages.length; i++) {
      const msg: any = messages[i];
      if (!msg || i < searchSessionStartRef.current) continue;
      switch (msg.type) {
        case 'status': {
          if (msg.data) {
            setStatus(msg.data.message || '');
            if (typeof msg.data.progress === 'number') setProgress(msg.data.progress);
          }
          break; }
        case 'relationship': {
          const d = msg.data || {};
            const l1: string = d.language1;
            const l2: string = d.language2;
            if (l1 && l2) {
              const childLabel = d.relationship === 'Child of' ? l1 : l1; // default; current backend only emits 'Child of'
              const parentLabel = d.relationship === 'Child of' ? l2 : l2;
              const parentId = ensureNode(parentLabel);
              const childId = ensureNode(childLabel);
              if (parentId && childId) {
                const edgeId = `e-${parentId}-${childId}`;
                setEdges(prev => prev.some(e => e.id === edgeId) ? prev : [...prev, { id: edgeId, source: parentId, target: childId, type: 'smoothstep', animated: true }]);
              }
            }
          break; }
        case 'complete': {
          completeRef.current = true;
          setStatus('Completed');
          setProgress(100);
          if (autoLayoutOnComplete) setTimeout(() => layout(), 0);
          // Optionally process any relationships included in final payload not seen during stream
          const rels = msg.data?.relationships;
          if (Array.isArray(rels)) {
            for (const r of rels) {
              const l1 = r.language1; const l2 = r.language2;
              if (!l1 || !l2) continue;
              const parentLabel = r.relationship === 'Child of' ? l2 : l2;
              const childLabel = r.relationship === 'Child of' ? l1 : l1;
              const parentId = ensureNode(parentLabel);
              const childId = ensureNode(childLabel);
              if (parentId && childId) {
                const edgeId = `e-${parentId}-${childId}`;
                setEdges(prev => prev.some(e => e.id === edgeId) ? prev : [...prev, { id: edgeId, source: parentId, target: childId, type: 'smoothstep', animated: true }]);
              }
            }
          }
          break; }
        case 'error': {
          setStatus(`Error: ${msg.data?.message || 'Unknown error'}`);
          setProgress(100);
          break; }
        default:
          break;
      }
    }
    lastProcessedIndexRef.current = messages.length;
  }, [messages, autoLayoutOnComplete, layout, ensureNode, setEdges]);

  const handleSearch = useCallback(() => {
    console.info(`[RF] New search: language='${language}', depth=${depth}`);
    // reset
    setNodes([]);
    setEdges([]);
    labelToIdRef.current = new Map();
    setStatus('Searching...');
    setProgress(0);
    completeRef.current = false;
    searchSessionStartRef.current = messages.length;
    lastProcessedIndexRef.current = messages.length;
    // create root node immediately
    const rootLabel = language.trim();
    if (rootLabel) {
      const rootId = rootLabel.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$|/g,'') || 'root';
      labelToIdRef.current.set(rootLabel, rootId);
      setNodes([{ id: rootId, data: { label: rootLabel }, position: { x: 0, y: 0 }, type: 'language' }]);
    }
    sendMessage(`${language},${depth}`);
  }, [language, depth, messages.length, sendMessage, setNodes, setEdges]);

  const changeLayout = (dir: 'TB' | 'LR') => {
    setLayoutDirection(dir);
    layout(dir);
  };

  return (
    <div className="h-screen w-full flex flex-col bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50">
      {/* Modern Header with Glass Effect */}
      <div className="relative bg-white/80 backdrop-blur-xl border-b border-white/20 shadow-lg shadow-blue-500/5">
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/5 via-indigo-600/5 to-purple-600/5"></div>
        <div className="relative px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Language Tree Explorer
              </h1>
            </div>
            
            {/* Connection Status with Modern Badge */}
            <div className="flex items-center space-x-2">
              <div className={`px-3 py-1 rounded-full text-xs font-medium border ${
                connectionStatus === 'connected' 
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                  : connectionStatus === 'connecting'
                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                  : 'bg-red-50 text-red-700 border-red-200'
              }`}>
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-emerald-500' : 
                    connectionStatus === 'connecting' ? 'bg-amber-500' : 'bg-red-500'
                  }`}></div>
                  <span>{connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Search Controls in Modern Card Layout */}
          <div className="flex items-center space-x-4 flex-wrap">
            {/* Language Input */}
            <div className="flex-1 min-w-48">
              <div className="relative">
                <input 
                  type="text" 
                  value={language} 
                  onChange={(e) => setLanguage(e.target.value)} 
                  placeholder="Enter language name..."
                  className="w-full px-4 py-3 pl-10 bg-white/70 backdrop-blur-sm border border-blue-200/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all duration-200 shadow-sm hover:shadow-md text-slate-700 placeholder-slate-400"
                />
                <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* Depth Input */}
            <div className="w-24">
              <input 
                type="number" 
                value={depth} 
                onChange={(e) => setDepth(parseInt(e.target.value, 10))}
                placeholder="Depth"
                min="1"
                max="5"
                className="w-full px-3 py-3 bg-white/70 backdrop-blur-sm border border-blue-200/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-400 transition-all duration-200 shadow-sm hover:shadow-md text-slate-700 text-center"
              />
            </div>

            {/* Explore Button */}
            <button 
              onClick={handleSearch} 
              disabled={connectionStatus !== 'connected'} 
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 disabled:from-slate-300 disabled:to-slate-400 text-white font-medium rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed disabled:shadow-sm transform hover:scale-105 disabled:hover:scale-100"
            >
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>{connectionStatus === 'connected' ? 'Explore' : 'Connecting...'}</span>
              </div>
            </button>

            {/* Layout Controls */}
            <div className="flex items-center space-x-2">
              <button 
                onClick={() => changeLayout('TB')} 
                className={`p-3 rounded-xl transition-all duration-200 shadow-sm hover:shadow-md ${
                  layoutDirection === 'TB' 
                    ? 'bg-blue-100 text-blue-600 border border-blue-200' 
                    : 'bg-white/70 text-slate-600 border border-slate-200 hover:bg-blue-50'
                }`}
                title="Vertical Layout"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                </svg>
              </button>
              <button 
                onClick={() => changeLayout('LR')} 
                className={`p-3 rounded-xl transition-all duration-200 shadow-sm hover:shadow-md ${
                  layoutDirection === 'LR' 
                    ? 'bg-blue-100 text-blue-600 border border-blue-200' 
                    : 'bg-white/70 text-slate-600 border border-slate-200 hover:bg-blue-50'
                }`}
                title="Horizontal Layout"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7l4-4m0 0l4 4m-4-4v18m0 0l-4-4m4 4l4-4" transform="rotate(90)" />
                </svg>
              </button>
            </div>

            {/* Auto Layout Toggle */}
            <label className="flex items-center space-x-2 cursor-pointer">
              <input 
                type="checkbox" 
                checked={autoLayoutOnComplete} 
                onChange={e => setAutoLayoutOnComplete(e.target.checked)}
                className="w-4 h-4 text-blue-600 bg-white border-2 border-blue-300 rounded focus:ring-blue-500 focus:ring-2"
              />
              <span className="text-sm font-medium text-slate-600">Auto layout</span>
            </label>
          </div>

          {/* Progress Bar */}
          {(status !== 'Not connected' && status !== 'Completed') && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-slate-700">{status}</span>
                <span className="text-xs text-slate-500">{progress}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-300 ease-out"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* React Flow Container with Modern Styling */}
      <div className="flex-1 relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={(params: Connection) => setEdges((eds) => addEdge(params, eds))}
          nodeTypes={nodeTypes}
          fitView
          className="bg-transparent"
          style={{ background: 'transparent' }}
        >
          <Controls 
            className="!bg-white/80 !backdrop-blur-xl !border-white/20 !shadow-lg !rounded-xl"
            style={{
              background: 'rgba(255, 255, 255, 0.8)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              borderRadius: '12px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.1)'
            }}
          />
          <Background 
            color="#e2e8f0" 
            gap={20}
            size={1}
            className="opacity-30"
          />
        </ReactFlow>
      </div>
    </div>
  );
};

const LanguageTreePageWrapper = () => (
    <ReactFlowProvider>
        <LanguageTreePage />
    </ReactFlowProvider>
);


export default LanguageTreePageWrapper;