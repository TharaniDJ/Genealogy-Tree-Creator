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
import LanguageDetailsSidebar from '../../components/LanguageDetailsSidebar';

// Dagre layouting
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 172;
const nodeHeight = 36;

type LanguageNodeData = { label: string; meta?: string; category?: string; qid?: string; onExpand?: () => void };
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
  const expandedQidsRef = useRef<Set<string>>(new Set());
  // Track currently selected node for edge highlighting
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedLanguage, setSelectedLanguage] = useState<{
    name: string;
    qid?: string;
    category?: string;
  } | null>(null);

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
      return prevNodes; 
    });
  }, [layoutDirection, setNodes, setEdges]);

  // Mapping label -> node id to avoid duplicates; stored in ref to persist across renders without causing rerenders
  const labelToIdRef = useRef<Map<string,string>>(new Map());
  const idCollisionCounterRef = useRef<Record<string, number>>({});

  const slugify = (label: string) => label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$|/g, '').slice(0,40) || 'lang';

  const ensureNode = useCallback((label: string, category?: string, qid?: string) => {
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
      // If node exists update category/meta if absent
      if (prev.some(n => n.id === id)) {
        return prev.map(n => {
          if (n.id !== id) return n;
          const updates: Partial<LanguageNodeData> = {};
          if (category && !n.data.category) {
            updates.category = category;
            updates.meta = humanizeCategory(category);
          }
          if (qid && !n.data.qid) {
            updates.qid = qid;
          }
          return Object.keys(updates).length > 0 ? { ...n, data: { ...n.data, ...updates } } : n;
        });
      }
      return [...prev, { 
        id, 
        data: { 
          label, 
          category, 
          meta: category ? humanizeCategory(category) : undefined,
          qid,
          onExpand: qid ? () => expandNodeByQid(qid) : undefined
        }, 
        position: { x: 0, y: 0 }, 
        type: 'language' 
      }];
    });
    return id;
  }, [setNodes]);

  const humanizeCategory = (cat?: string) => {
    if (!cat) return '';
    return cat.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());
  };

  // Helpers to prompt user for input in a simple way
  const promptForLabel = useCallback((defaultValue = '') => {
    const res = window.prompt('Enter language label/name:', defaultValue);
    const val = (res || '').trim();
    return val ? val : null;
  }, []);

  const promptForCategory = useCallback((defaultValue = '') => {
    const res = window.prompt('Enter category (e.g., language, dialect, language_family, proto_language, extinct_language, dead_language):', defaultValue);
    const val = (res || '').trim();
    return val || undefined;
  }, []);

  // CRUD: Add a standalone node
  const addStandaloneNode = useCallback(() => {
    const label = promptForLabel('New Language');
    if (!label) return;
    const existing = labelToIdRef.current.get(label);
    if (existing) {
      // Select existing instead of duplicating
      setSelectedNodeId(existing);
      const n = nodes.find(nd => nd.id === existing);
      if (n) {
        setSelectedLanguage({ name: n.data.label, qid: n.data.qid, category: n.data.category });
        setSidebarOpen(true);
      }
      return;
    }
    const cat = promptForCategory('language');
    const id = ensureNode(label, cat);
    if (id) {
      setSelectedNodeId(id);
      setSelectedLanguage({ name: label, category: cat });
      setSidebarOpen(true);
      // Re-layout to place the new node
      setTimeout(() => layout(layoutDirection), 0);
    }
  }, [ensureNode, layout, layoutDirection, nodes, promptForCategory, promptForLabel]);

  // CRUD: Add a child node to the currently selected node
  const addChildNode = useCallback(() => {
    if (!selectedNodeId) return;
    const parent = nodes.find(n => n.id === selectedNodeId);
    if (!parent) return;
    const label = promptForLabel('Child Language');
    if (!label) return;
    let childId: string | undefined = labelToIdRef.current.get(label);
    if (!childId) {
      const cat = promptForCategory('language');
      const createdId = ensureNode(label, cat);
      if (!createdId) return;
      childId = createdId;
    }
    const edgeId = `e-${selectedNodeId}-${childId}`;
    setEdges(prev => {
      if (prev.some(e => e.id === edgeId)) return prev;
      return [...prev, { id: edgeId, source: selectedNodeId, target: childId!, type: 'smoothstep', animated: true }];
    });
    setTimeout(() => layout(layoutDirection), 0);
  }, [ensureNode, layout, layoutDirection, nodes, selectedNodeId, promptForLabel, promptForCategory, setEdges]);

  // CRUD: Edit the selected node's label/category
  const editSelectedNode = useCallback(() => {
    if (!selectedNodeId) return;
    const node = nodes.find(n => n.id === selectedNodeId);
    if (!node) return;
    const oldLabel = node.data.label;
    const newLabel = promptForLabel(oldLabel) || oldLabel;
    // Prevent renaming to an existing different node's label
    const existing = labelToIdRef.current.get(newLabel);
    if (existing && existing !== selectedNodeId) {
      window.alert('A node with that label already exists. Choose another label.');
      return;
    }
    const newCategory = promptForCategory(node.data.category || '') || node.data.category;
    // Update mapping: remove old label key(s) pointing to this id, then add new
    for (const [k, v] of Array.from(labelToIdRef.current.entries())) {
      if (v === selectedNodeId) {
        labelToIdRef.current.delete(k);
      }
    }
    labelToIdRef.current.set(newLabel, selectedNodeId);
    // Update node state
    setNodes(prev => prev.map(n => {
      if (n.id !== selectedNodeId) return n;
      const data = { ...n.data, label: newLabel, category: newCategory, meta: newCategory ? humanizeCategory(newCategory) : undefined };
      return { ...n, data };
    }));
    setSelectedLanguage({ name: newLabel, qid: node.data.qid, category: newCategory });
    setTimeout(() => layout(layoutDirection), 0);
  }, [humanizeCategory, layout, layoutDirection, nodes, promptForCategory, promptForLabel, selectedNodeId, setNodes]);

  // CRUD: Delete the selected node and its connected edges
  const deleteSelectedNode = useCallback(() => {
    if (!selectedNodeId) return;
    const node = nodes.find(n => n.id === selectedNodeId);
    const label = node?.data.label;
    const ok = window.confirm(`Delete node${label ? ` \"${label}\"` : ''} and its connections?`);
    if (!ok) return;
    // Remove node
    setNodes(prev => prev.filter(n => n.id !== selectedNodeId));
    // Remove connected edges
    setEdges(prev => prev.filter(e => e.source !== selectedNodeId && e.target !== selectedNodeId));
    // Clean mapping entries pointing to this id
    for (const [k, v] of Array.from(labelToIdRef.current.entries())) {
      if (v === selectedNodeId) labelToIdRef.current.delete(k);
    }
    // Clear selection/sidebar
    setSelectedNodeId(null);
    setSidebarOpen(false);
    setSelectedLanguage(null);
    setTimeout(() => layout(layoutDirection), 0);
  }, [layout, layoutDirection, nodes, selectedNodeId, setEdges, setNodes]);

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
        case 'root_language': {
          const d = msg.data || {};
          const qid: string | undefined = d.qid || undefined;
          const label: string | undefined = d.label || undefined;
          const primaryType: string | undefined = d.primary_type || undefined;
          if (label) {
            const id = labelToIdRef.current.get(label);
            if (id) {
              setNodes(prev => prev.map(n => {
                if (n.id !== id) return n;
                const updates: Partial<LanguageNodeData> = {};
                if (qid) updates.qid = qid;
                if (primaryType && !n.data.category) {
                  updates.category = primaryType;
                  updates.meta = humanizeCategory(primaryType);
                }
                if (qid && !n.data.onExpand) {
                  updates.onExpand = () => expandNodeByQid(qid);
                }
                return Object.keys(updates).length ? { ...n, data: { ...n.data, ...updates } } : n;
              }));
            }
          }
          break; }
        case 'relationship': {
          const d = msg.data || {};
          const l1: string = d.language1;
          const l2: string = d.language2;
          const c1: string | undefined = d.language1_category || undefined;
          const c2: string | undefined = d.language2_category || undefined;
          const qid1: string | undefined = d.language1_qid || undefined;
          const qid2: string | undefined = d.language2_qid || undefined;
          if (l1 && l2) {
            const childLabel = d.relationship === 'Child of' ? l1 : l1; // current backend only emits 'Child of'
            const parentLabel = d.relationship === 'Child of' ? l2 : l2;
            const childQid = d.relationship === 'Child of' ? qid1 : qid1;
            const parentQid = d.relationship === 'Child of' ? qid2 : qid2;
            const parentId = ensureNode(parentLabel, c2, parentQid);
            const childId = ensureNode(childLabel, c1, childQid);
            if (parentId && childId) {
              const edgeId = `e-${parentId}-${childId}`;
              setEdges(prev => {
                const edgeExists = prev.some(e => e.id === edgeId);
                if (!edgeExists) {
                  // Schedule layout after the edge is added
                  setTimeout(() => layout('TB'), 100);
                  return [...prev, { id: edgeId, source: parentId, target: childId, type: 'smoothstep', animated: true }];
                }
                return prev;
              });

              // Update nodes to include expand handlers if missing
              setNodes(prev => prev.map(n => {
                if (n.id === parentId && parentQid && !n.data.onExpand) {
                  return { ...n, data: { ...n.data, qid: parentQid, onExpand: () => expandNodeByQid(parentQid) } };
                }
                if (n.id === childId && childQid && !n.data.onExpand) {
                  return { ...n, data: { ...n.data, qid: childQid, onExpand: () => expandNodeByQid(childQid) } };
                }
                return n;
              }));
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
              const parentQid = r.relationship === 'Child of' ? r.language2_qid : r.language2_qid;
              const childQid = r.relationship === 'Child of' ? r.language1_qid : r.language1_qid;
              const parentId = ensureNode(parentLabel, r.language2_category, parentQid);
              const childId = ensureNode(childLabel, r.language1_category, childQid);
              if (parentId && childId) {
                const edgeId = `e-${parentId}-${childId}`;
                setEdges(prev => prev.some(e => e.id === edgeId) ? prev : [...prev, { id: edgeId, source: parentId, target: childId, type: 'smoothstep', animated: true }]);

                // ensure expand handlers
                setNodes(prev => prev.map(n => {
                  if (n.id === parentId && parentQid && !n.data.onExpand) {
                    return { ...n, data: { ...n.data, qid: parentQid, onExpand: () => expandNodeByQid(parentQid) } };
                  }
                  if (n.id === childId && childQid && !n.data.onExpand) {
                    return { ...n, data: { ...n.data, qid: childQid, onExpand: () => expandNodeByQid(childQid) } };
                  }
                  return n;
                }));
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
    //if (rootLabel) {
    //  const rootId = rootLabel.toLowerCase().replace(/[^a-z0-9]+/g,'-').replace(/^-|-$|/g,'') || 'root';
    //  labelToIdRef.current.set(rootLabel, rootId);
    //  setNodes([{ id: rootId, data: { label: rootLabel }, position: { x: 0, y: 0 }, type: 'language' }]);
    //}
    sendMessage(`${language},${depth}`);
  }, [language, depth, messages.length, sendMessage, setNodes, setEdges]);

  // Expand logic: request depth-1 relationship
  const expandNodeByQid = useCallback((qid: string) => {
    if (!qid) return;
    if (expandedQidsRef.current.has(qid)) return; // avoid duplicate expand calls
    expandedQidsRef.current.add(qid);
    setStatus(`Expanding ${qid}...`);
    setProgress(0);
    sendMessage({ action: 'expand_by_qid', qid, depth: 1 });
  }, [sendMessage]);

  const changeLayout = (dir: 'TB' | 'LR') => {
    setLayoutDirection(dir);
    layout(dir);
  };

  // Build current relationships payload from edges + nodes' labels/qids/categories
  const buildRelationshipsPayload = useCallback(() => {
    const idToNode = new Map(nodes.map(n => [n.id, n] as const));
    // relationships: parent (source) -> child (target)
    return edges.map(e => {
      const parent = idToNode.get(e.source);
      const child = idToNode.get(e.target);
      return {
        language1: child?.data.label || '',
        relationship: 'Child of',
        language2: parent?.data.label || '',
        language1_qid: child?.data.qid,
        language2_qid: parent?.data.qid,
        language1_category: child?.data.category,
        language2_category: parent?.data.category,
      } as any;
    });
  }, [edges, nodes]);

  // Save current graph to backend
  const handleSaveGraph = useCallback(async () => {
    try {
      const userId = '1234';
      const graphName = window.prompt('Enter a name for this graph:', language.trim()) || language.trim() || 'Unnamed Graph';
      const rels = buildRelationshipsPayload();
      const payload = {
        user_id: userId,
        name: graphName,
        depth: depth,
        node_count: nodes.length,
        relationships: rels,
      };
      const res = await fetch('http://localhost:8001/graphs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || 'Failed to save graph');
      }
      const saved = await res.json();
      setStatus(`Saved graph "${saved.name}"`);
    } catch (err: any) {
      console.error('Save graph failed', err);
      setStatus(`Error saving graph: ${err?.message || err}`);
    }
  }, [buildRelationshipsPayload, depth, language, nodes.length]);

  // Highlight edges connected to selected node without mutating core edge state
  const displayEdges = useMemo(() => {
    if (!selectedNodeId) return edges;
    return edges.map(e => {
      const isConnected = e.source === selectedNodeId || e.target === selectedNodeId;
      if (isConnected) {
        return {
          ...e,
          style: { ...(e.style || {}), stroke: '#8b5cf6', strokeWidth: 3 },
          animated: true,
          className: (e.className ? e.className + ' ' : '') + 'edge-highlight'
        };
      }
      return {
        ...e,
        style: { ...(e.style || {}), stroke: '#64748b', strokeWidth: 1, opacity: 0.3 },
        className: (e.className ? e.className + ' ' : '') + 'edge-dim'
      };
    });
  }, [edges, selectedNodeId]);

  // Handle node click to open sidebar
  const handleNodeClick = useCallback((event: React.MouseEvent, node: LanguageRFNode) => {
    setSelectedNodeId(prev => prev === node.id ? null : node.id);
    setSelectedLanguage({
      name: node.data.label,
      qid: node.data.qid,
      category: node.data.category
    });
    setSidebarOpen(true);
  }, []);

  const handleCloseSidebar = useCallback(() => {
    setSidebarOpen(false);
    setSelectedLanguage(null);
  }, []);

  return (
    <div className="h-screen w-full flex flex-col bg-gradient-to-br from-slate-900 via-gray-900 to-slate-800">
      {/* Modern Dark Header with Glass Effect */}
      <div className="relative bg-gray-900/80 backdrop-blur-xl border-b border-gray-700/30 shadow-lg shadow-purple-500/10">
        <div className="absolute inset-0 bg-gradient-to-r from-purple-600/10 via-blue-600/10 to-cyan-600/10"></div>
        <div className="relative px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-cyan-600 rounded-lg flex items-center justify-center shadow-lg">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 via-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Language Tree Explorer
              </h1>
            </div>
            
            {/* Connection Status with Modern Badge */}
            <div className="flex items-center space-x-2">
              <div className={`px-3 py-1 rounded-full text-xs font-medium border ${
                connectionStatus === 'connected' 
                  ? 'bg-emerald-900/50 text-emerald-300 border-emerald-500/30' 
                  : connectionStatus === 'connecting'
                  ? 'bg-amber-900/50 text-amber-300 border-amber-500/30'
                  : 'bg-red-900/50 text-red-300 border-red-500/30'
              }`}>
                <div className="flex items-center space-x-1">
                  <div className={`w-2 h-2 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-emerald-400' : 
                    connectionStatus === 'connecting' ? 'bg-amber-400' : 'bg-red-400'
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
                  className="w-full px-4 py-3 pl-10 bg-gray-800/70 backdrop-blur-sm border border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 transition-all duration-200 shadow-sm hover:shadow-md text-gray-100 placeholder-gray-400"
                />
                <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                className="w-full px-3 py-3 bg-gray-800/70 backdrop-blur-sm border border-gray-600/50 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-400 transition-all duration-200 shadow-sm hover:shadow-md text-gray-100 text-center"
              />
            </div>

            {/* Explore Button */}
            <button 
              onClick={handleSearch} 
              disabled={connectionStatus !== 'connected'} 
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-cyan-600 hover:from-purple-600 hover:to-cyan-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-medium rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:cursor-not-allowed disabled:shadow-sm transform hover:scale-105 disabled:hover:scale-100"
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
                    ? 'bg-purple-900/50 text-purple-300 border border-purple-500/30' 
                    : 'bg-gray-800/70 text-gray-300 border border-gray-600/30 hover:bg-purple-900/30'
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
                    ? 'bg-purple-900/50 text-purple-300 border border-purple-500/30' 
                    : 'bg-gray-800/70 text-gray-300 border border-gray-600/30 hover:bg-purple-900/30'
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
                className="w-4 h-4 text-purple-600 bg-gray-800 border-2 border-gray-600 rounded focus:ring-purple-500 focus:ring-2"
              />
              <span className="text-sm font-medium text-gray-300">Auto layout</span>
            </label>
          </div>

          {/* Progress Bar */}
          {(status !== 'Not connected' && status !== 'Completed') && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-200">{status}</span>
                
              </div>
              <div className="w-full bg-gray-700/50 rounded-full h-2 overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-purple-500 to-cyan-600 rounded-full transition-all duration-300 ease-out"
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
          edges={displayEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={(params: Connection) => setEdges((eds) => addEdge(params, eds))}
          onNodeClick={handleNodeClick}
          onPaneClick={() => {
            setSelectedNodeId(null);
            setSidebarOpen(false);
            setSelectedLanguage(null);
          }}
          nodeTypes={nodeTypes}
          fitView
          className="bg-transparent"
          style={{ background: 'transparent' }}
        >
          <Controls 
            className="!bg-gray-900/80 !backdrop-blur-xl !border-gray-700/30 !shadow-lg !rounded-xl"
            style={{
              background: 'rgba(17, 24, 39, 0.8)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(55, 65, 81, 0.3)',
              borderRadius: '12px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)'
            }}
          />
          <Background 
            color="#374151" 
            gap={20}
            size={1}
            className="opacity-20"
          />
          {/* Floating toolbar for CRUD operations */}
          <div className="absolute top-4 right-4 z-10 flex items-center gap-2 bg-gray-900/80 backdrop-blur-xl border border-gray-700/30 rounded-xl p-2 shadow-lg">
            <button
              onClick={addStandaloneNode}
              className="px-3 py-2 text-sm rounded-lg bg-gradient-to-r from-purple-500 to-cyan-600 text-white hover:from-purple-600 hover:to-cyan-700 transition-colors shadow"
              title="Add node"
            >
              Add Node
            </button>
            <button
              onClick={addChildNode}
              disabled={!selectedNodeId}
              className={`px-3 py-2 text-sm rounded-lg transition-colors shadow ${selectedNodeId ? 'bg-gray-800/70 text-gray-200 hover:bg-purple-900/40 border border-gray-600/40' : 'bg-gray-800/40 text-gray-500 border border-gray-700/30 cursor-not-allowed'}`}
              title="Add child to selected"
            >
              Add Child
            </button>
            <button
              onClick={editSelectedNode}
              disabled={!selectedNodeId}
              className={`px-3 py-2 text-sm rounded-lg transition-colors shadow ${selectedNodeId ? 'bg-gray-800/70 text-gray-200 hover:bg-purple-900/40 border border-gray-600/40' : 'bg-gray-800/40 text-gray-500 border border-gray-700/30 cursor-not-allowed'}`}
              title="Edit selected node"
            >
              Edit
            </button>
            <button
              onClick={deleteSelectedNode}
              disabled={!selectedNodeId}
              className={`px-3 py-2 text-sm rounded-lg transition-colors shadow ${selectedNodeId ? 'bg-rose-600/80 text-white hover:bg-rose-600' : 'bg-gray-800/40 text-gray-500 border border-gray-700/30 cursor-not-allowed'}`}
              title="Delete selected node"
            >
              Delete
            </button>
            <div className="w-px h-6 bg-gray-700/50 mx-1" />
            <button
              onClick={handleSaveGraph}
              className="px-3 py-2 text-sm rounded-lg bg-gradient-to-r from-emerald-500 to-teal-600 text-white hover:from-emerald-600 hover:to-teal-700 transition-colors shadow"
              title="Save current graph"
            >
              Save Graph
            </button>
          </div>
        </ReactFlow>
      </div>

      {/* Language Details Sidebar */}
      <LanguageDetailsSidebar
        isOpen={sidebarOpen}
        onClose={handleCloseSidebar}
        languageName={selectedLanguage?.name || ''}
        qid={selectedLanguage?.qid}
        category={selectedLanguage?.category}
      />
    </div>
  );
};

const LanguageTreePageWrapper = () => (
    <ReactFlowProvider>
        <LanguageTreePage />
    </ReactFlowProvider>
);


export default LanguageTreePageWrapper;