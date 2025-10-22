"use client";

import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import AuthGuard from '@/components/AuthGuard';
import VerticalNavbar from '@/components/VerticalNavbar';
import useAuth from '@/hooks/useAuth';
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
  MarkerType,
  useReactFlow,
  getRectOfNodes,
  getTransformForBounds,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { useWebSocket } from '../../hooks/useWebSocket';
import LanguageNode from '../../components/LanguageNode';
import LanguageDetailsSidebar from '../../components/LanguageDetailsSidebar';
import { toPng, toJpeg } from 'html-to-image';
import jsPDF from 'jspdf';

const MIN_NODE_WIDTH = 200;
const MAX_NODE_WIDTH = 360;
const LABEL_CHAR_PIXEL_WIDTH = 7.5;
const BASE_NODE_HEIGHT = 56;
const LINE_HEIGHT = 18;
const HEAVY_CHILD_THRESHOLD = 10;
const HEAVY_PARENT_EXTRA_BASE = 80;
const HEAVY_PARENT_EXTRA_PER_CHILD = 6;

type LanguageNodeData = {
  label: string;
  meta?: string;
  category?: string;
  qid?: string;
  // Raw type labels returned from classifier (e.g., ["language", "dialect"]) for persistence
  types?: string[];
  onExpand?: () => void;
};
type LanguageRFNode = Node<LanguageNodeData>;

type LevelAnalysis = {
  levelMap: Map<string, number>;
  adjacency: Map<string, string[]>;
};

type RelationshipRecord = {
  language1: string;
  language2: string;
  relationship: string;
  language1_qid?: string;
  language2_qid?: string;
  language1_category?: string;
  language2_category?: string;
  // Persist raw classifier outputs as well
  language1_types?: string[];
  language2_types?: string[];
};

type SavedGraph = {
  id: string;
  graph_name: string;
  description?: string;
  nodes_count?: number;
  depth_usage?: boolean;
  depth?: number;
  updated_at: string;
};

type InboundMessage = {
  type: string;
  data?: unknown;
};

const isRecord = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null;

const toRelationshipRecord = (value: unknown): RelationshipRecord | null => {
  if (!isRecord(value)) return null;
  const language1 = typeof value.language1 === 'string' ? value.language1 : undefined;
  const language2 = typeof value.language2 === 'string' ? value.language2 : undefined;
  if (!language1 || !language2) return null;
  const relationship = typeof value.relationship === 'string' ? value.relationship : 'Child of';
  return {
    language1,
    language2,
    relationship,
    language1_qid: typeof value.language1_qid === 'string' ? value.language1_qid : undefined,
    language2_qid: typeof value.language2_qid === 'string' ? value.language2_qid : undefined,
    language1_category: typeof value.language1_category === 'string' ? value.language1_category : undefined,
    language2_category: typeof value.language2_category === 'string' ? value.language2_category : undefined,
  };
};

const calculateNodeDimensions = (node: LanguageRFNode) => {
  const label = node.data?.label ?? '';
  const meta = node.data?.meta ?? '';
  const estimatedWidth = Math.min(
    MAX_NODE_WIDTH,
    Math.max(MIN_NODE_WIDTH, 80 + label.length * 6.5)
  );
  const charsPerLine = Math.max(14, Math.floor(estimatedWidth / LABEL_CHAR_PIXEL_WIDTH));
  const labelLines = Math.max(1, Math.ceil(label.length / charsPerLine));
  const metaLines = meta ? Math.max(1, Math.ceil(meta.length / charsPerLine)) : 0;
  const height = BASE_NODE_HEIGHT + (labelLines - 1) * LINE_HEIGHT + metaLines * LINE_HEIGHT;
  return { width: Math.round(estimatedWidth), height: Math.round(height) };
};

const computeHierarchyLevels = (nodes: LanguageRFNode[], edges: Edge[]): LevelAnalysis => {
  const adjacency = new Map<string, string[]>();
  const indegree = new Map<string, number>();

  nodes.forEach(node => {
    adjacency.set(node.id, []);
    indegree.set(node.id, 0);
  });

  edges.forEach(edge => {
    if (!edge.source || !edge.target) return;
    if (!adjacency.has(edge.source)) {
      adjacency.set(edge.source, []);
    }
    adjacency.get(edge.source)!.push(edge.target);
    indegree.set(edge.target, (indegree.get(edge.target) ?? 0) + 1);
    if (!indegree.has(edge.source)) {
      indegree.set(edge.source, 0);
    }
  });

  const queue: string[] = [];
  indegree.forEach((deg, id) => {
    if (deg === 0) {
      queue.push(id);
    }
  });

  const levelMap = new Map<string, number>();

  queue.forEach(id => {
    if (!levelMap.has(id)) {
      levelMap.set(id, 0);
    }
  });

  while (queue.length) {
    const id = queue.shift()!;
    const level = levelMap.get(id) ?? 0;

    const neighbours = adjacency.get(id) ?? [];
    neighbours.forEach(target => {
      const candidateLevel = Math.max(levelMap.get(target) ?? 0, level + 1);
      levelMap.set(target, candidateLevel);
      const remaining = (indegree.get(target) ?? 0) - 1;
      indegree.set(target, remaining);
      if (remaining === 0) {
        queue.push(target);
      }
    });
  }

  nodes.forEach(node => {
    if (!levelMap.has(node.id)) {
      levelMap.set(node.id, 0);
    }
  });

  return { levelMap, adjacency };
};

const getLayoutedElements = (nodes: LanguageRFNode[], edges: Edge[], direction = 'TB') => {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  const isHorizontal = direction === 'LR';
  const { adjacency } = computeHierarchyLevels(nodes, edges);

  const baseRankSep = isHorizontal ? 140 : 160;
  const baseNodeSep = isHorizontal ? 120 : 110;

  dagreGraph.setGraph({ rankdir: direction, ranksep: baseRankSep, nodesep: baseNodeSep });

  const dimensionCache = new Map<string, { width: number; height: number }>();

  nodes.forEach(node => {
    const dims = calculateNodeDimensions(node);
    dimensionCache.set(node.id, dims);
    dagreGraph.setNode(node.id, { width: dims.width, height: dims.height });
  });
  edges.forEach(edge => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  const heavySpacingOffsets = new Map<string, number>();
  if (!isHorizontal) {
  adjacency.forEach((children) => {
      if (!children || children.length < HEAVY_CHILD_THRESHOLD) return;
      const childCount = children.length;
      const extra = HEAVY_PARENT_EXTRA_BASE + (childCount - HEAVY_CHILD_THRESHOLD) * HEAVY_PARENT_EXTRA_PER_CHILD;
      const queue = [...children];
      const visited = new Set<string>();
      while (queue.length) {
        const nodeId = queue.shift()!;
        if (visited.has(nodeId)) continue;
        visited.add(nodeId);
        heavySpacingOffsets.set(nodeId, Math.max(heavySpacingOffsets.get(nodeId) ?? 0, extra));
        const descendants = adjacency.get(nodeId);
        if (descendants && descendants.length) {
          queue.push(...descendants);
        }
      }
    });
  }

  nodes.forEach(node => {
    const pos = dagreGraph.node(node.id);
    if (!pos) return;
    node.targetPosition = isHorizontal ? Position.Left : Position.Top;
    node.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;
    const dims = dimensionCache.get(node.id);
    const width = dims?.width ?? MIN_NODE_WIDTH;
    const height = dims?.height ?? BASE_NODE_HEIGHT;
    const heavyOffset = !isHorizontal ? heavySpacingOffsets.get(node.id) ?? 0 : 0;
    node.position = {
      x: pos.x - width / 2,
      y: pos.y - height / 2 + heavyOffset,
    };
    node.style = {
      ...(node.style || {}),
      width,
      minWidth: width,
    };
  });
  return { nodes, edges };
};


const LanguageTreePage = () => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [nodes, setNodes, onNodesChange] = useNodesState<LanguageNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
  const [language, setLanguage] = useState('English');
  const [depth, setDepth] = useState(2);
  const [status, setStatus] = useState('Not connected');
  const [progress, setProgress] = useState(0);
  // Collapsible UI state for status panel and toolbar (match family tree style)
  const [isStatusCollapsed, setIsStatusCollapsed] = useState(true);
  const [isToolbarCollapsed, setIsToolbarCollapsed] = useState(true);
  // Pinned open flags when user explicitly opens
  const [statusPinnedOpen, setStatusPinnedOpen] = useState(false);
  const [toolbarPinnedOpen, setToolbarPinnedOpen] = useState(false);
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

  // Graph saving state
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [graphName, setGraphName] = useState('');
  const [graphDescription, setGraphDescription] = useState('');
  const [savedGraphs, setSavedGraphs] = useState<SavedGraph[]>([]);
  const [loadingGraphs, setLoadingGraphs] = useState(false);
  const [savingGraph, setSavingGraph] = useState(false);
  const [isFullTreeMode, setIsFullTreeMode] = useState(false);
  const [classifying, setClassifying] = useState(false);
  // Wikipedia URL input
  const [wikiUrl, setWikiUrl] = useState('');
  // Title choices modal state
  const [showTitleModal, setShowTitleModal] = useState(false);
  const [titleChoices, setTitleChoices] = useState<{
    query: string;
    context: 'search' | 'expand_node' | 'fetch_full_tree';
    depth?: number;
    nodeLabel?: string;
    results: { title: string; snippet?: string; url: string }[];
    existingGraph?: RelationshipRecord[] | null;
  } | null>(null);

  const { getNodes, fitView: fitViewApi } = useReactFlow();
  const reactFlowRef = useRef<HTMLDivElement>(null);
  const { getToken } = useAuth();

  const wsBase = process.env.NEXT_PUBLIC_LANGUAGE_API_URL || 'http://localhost:8001';
  const wsUrl = wsBase.replace(/^http/, 'ws') + '/ws/relationships';
  const { messages, connectionStatus, connect, disconnect, sendMessage } = useWebSocket(wsUrl, { 
    token: getToken() 
  });
  const httpBase = wsBase; // same base but http

  // Track which messages have been processed to avoid losing earlier batches when multiple arrive quickly.
  const lastProcessedIndexRef = useRef(0);
  // Track search session start to ignore old messages from prior sessions if needed.
  const searchSessionStartRef = useRef(0);
  const completeRef = useRef(false);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  // Auto manage collapse/expand based on activity
  useEffect(() => {
    const hasActiveProgress = progress > 0 && progress < 100;
    const normalizedStatus = (status || '').toLowerCase();
    const hasActiveStatus = normalizedStatus.length > 0 && !/completed|not connected/.test(normalizedStatus);
    const eventActive = connectionStatus === 'connecting' || hasActiveProgress || hasActiveStatus;

    if (eventActive) {
      setIsStatusCollapsed(false);
      setIsToolbarCollapsed(false);
    } else {
      const t = setTimeout(() => {
        if (!statusPinnedOpen) setIsStatusCollapsed(true);
        if (!toolbarPinnedOpen) setIsToolbarCollapsed(true);
      }, 1200);
      return () => clearTimeout(t);
    }
  }, [connectionStatus, progress, status, statusPinnedOpen, toolbarPinnedOpen]);

  

  const nodeTypes = useMemo(() => ({ language: LanguageNode }), []);

  const defaultEdgeOptions = useMemo(() => ({
    type: 'simplebezier' as const,
    animated: true,
    style: { stroke: '#38bdf8', strokeWidth: 2, opacity: 0.95 },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 16,
      height: 16,
      color: '#38bdf8',
    },
  }), []);

  const createEdge = useCallback((source: string, target: string) => {
    const id = `e-${source}-${target}`;
    return {
      id,
      source,
      target,
  type: 'simplebezier',
      animated: true,
      markerEnd: defaultEdgeOptions.markerEnd ? { ...defaultEdgeOptions.markerEnd } : undefined,
      style: defaultEdgeOptions.style ? { ...defaultEdgeOptions.style } : undefined,
    } as Edge;
  }, [defaultEdgeOptions]);

  const layout = useCallback((direction: 'TB' | 'LR' = layoutDirection) => {
    // Compute layout using the latest nodes/edges to avoid stale state in production batching
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(
      [...nodes.map(n => ({ ...n }))],
      [...edges.map(e => ({ ...e }))],
      direction
    );
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [nodes, edges, layoutDirection, setNodes, setEdges]);

  // After batched updates settle (esp. in production), re-apply layout once graph is complete
  useEffect(() => {
    if (!autoLayoutOnComplete) return;
    if (nodes.length && edges.length && (completeRef.current || progress >= 100)) {
      const t = setTimeout(() => layout(), 0);
      return () => clearTimeout(t);
    }
  }, [nodes.length, edges.length, progress, autoLayoutOnComplete, layout]);

  // Mapping label -> node id to avoid duplicates; stored in ref to persist across renders without causing rerenders
  const labelToIdRef = useRef<Map<string,string>>(new Map());

  const slugify = (label: string) => label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$|/g, '').slice(0,40) || 'lang';

  // Canonicalize labels to help unify variants like "Yola" vs "Yola dialect"
  const canonical = useCallback((label: string): string => {
    let s = (label || '').toLowerCase().trim();
    s = s.replace(/\([^)]*\)/g, ''); // remove parentheses
    s = s.replace(/\b(languages?|dialects?)\b/g, ''); // strip tokens
    s = s.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
    return s;
  }, []);

  const humanizeCategory = useCallback((cat?: string) => {
    if (!cat) return '';
    return cat.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());
  }, []);

  const expandNodeByQid = useCallback((qid: string) => {
    if (!qid) return;
    if (expandedQidsRef.current.has(qid)) return;
    expandedQidsRef.current.add(qid);
    setStatus(`Expanding ${qid}...`);
    setProgress(0);
    sendMessage({ action: 'expand_by_qid', qid, depth: 1 });
  }, [sendMessage]);
  
  // Build current relationships payload from edges + nodes' labels/qids/categories/types
  const buildRelationshipsPayload = useCallback((): RelationshipRecord[] => {
    const idToNode = new Map(nodes.map(n => [n.id, n] as const));
    // relationships: parent (source) -> child (target)
    return edges.map(e => {
      const parent = idToNode.get(e.source);
      const child = idToNode.get(e.target);
      const record: RelationshipRecord = {
        language1: child?.data.label ?? '',
        relationship: 'Child of',
        language2: parent?.data.label ?? '',
        language1_qid: child?.data.qid,
        language2_qid: parent?.data.qid,
        language1_category: child?.data.category,
        language2_category: parent?.data.category,
        language1_types: child?.data.types,
        language2_types: parent?.data.types,
      };
      return record;
    });
  }, [edges, nodes]);

  // New: Expand a node by label using the refined backend expansion
  const expandNodeByLabel = useCallback((label: string) => {
    const name = (label || '').trim();
    if (!name) return;
    setStatus(`Expanding "${name}"...`);
    setProgress(0);
    const existingGraph = buildRelationshipsPayload();
    sendMessage({ action: 'expand_node', label: name, existingGraph });
  }, [buildRelationshipsPayload, sendMessage]);

  const ensureNode = useCallback((label: string, category?: string, qid?: string, types?: string[]) => {
    if (!label) return null;
    const map = labelToIdRef.current;
    if (map.has(label)) return map.get(label)!;
    const base = slugify(label);
    // resolve collisions with existing ids mapping to different labels
    let id = base;
    let attempts = 1;
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
          if (types && (!n.data.types || n.data.types.length === 0)) {
            updates.types = types;
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
          types,
          // Always provide expand by label so every node can be expanded
          onExpand: () => expandNodeByLabel(label)
        }, 
        position: { x: 0, y: 0 }, 
        type: 'language' 
      }];
    });
    return id;
  }, [expandNodeByLabel, humanizeCategory, setNodes]);

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
      return [...prev, createEdge(selectedNodeId, childId!)];
    });
    setTimeout(() => layout(layoutDirection), 0);
  }, [createEdge, ensureNode, layout, layoutDirection, nodes, selectedNodeId, promptForLabel, promptForCategory, setEdges]);

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

  // Programmatic fit view button handler (moved above effects that reference it)
  const handleFitView = useCallback(() => {
    try {
      // Smoothly fit to all nodes with some padding
      fitViewApi({ padding: 0.2, duration: 500 });
      setStatus('Fitted view to graph');
    } catch {
      // ignore errors when no nodes are present
    }
  }, [fitViewApi]);

  // Ask backend for suggestions explicitly
  const requestSuggestions = useCallback((q: string, ctx: 'search' | 'expand_node', d?: number, existingGraph?: RelationshipRecord[] | null, nodeLabel?: string) => {
    if (!q || !q.trim()) return;
    setStatus('Looking up Wikipedia pages...');
    setProgress(0);
    sendMessage({ action: 'suggest_titles', query: q.trim(), context: ctx, depth: d, existingGraph, nodeLabel });
  }, [sendMessage]);

  // Start from a Wikipedia URL
  const handleUseUrl = useCallback(() => {
    const url = (wikiUrl || '').trim();
    if (!url) {
      setStatus('Please paste a Wikipedia URL.');
      return;
    }
    setStatus('Starting from Wikipedia URL...');
    setProgress(0);
    sendMessage({ action: 'start_with_url', url, context: 'search', depth });
  }, [wikiUrl, depth, sendMessage]);

  // Process streaming messages from backend (status, relationship, complete, error)
  useEffect(() => {
    if (!messages.length) return;
    for (let i = lastProcessedIndexRef.current; i < messages.length; i++) {
      const msg = messages[i] as InboundMessage;
      if (!msg || typeof msg.type !== 'string' || i < searchSessionStartRef.current) continue;
      const data = isRecord(msg.data) ? msg.data : undefined;
      switch (msg.type) {
        case 'status': {
          if (data) {
            const messageText = typeof data.message === 'string' ? data.message : '';
            const progressValue = typeof data.progress === 'number' ? data.progress : undefined;
            if (messageText) setStatus(messageText);
            if (typeof progressValue === 'number') setProgress(progressValue);
          }
          break; }
        case 'root_language': {
          const qid = data && typeof data.qid === 'string' ? data.qid : undefined;
          const label = data && typeof data.label === 'string' ? data.label : undefined;
          const primaryType = data && typeof data.primary_type === 'string' ? data.primary_type : undefined;
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
                // Ensure expand uses label-based expansion
                if (!n.data.onExpand) updates.onExpand = () => expandNodeByLabel(label);
                return Object.keys(updates).length ? { ...n, data: { ...n.data, ...updates } } : n;
              }));
            }
          }
          break; }
        case 'relationship': {
          if (data) {
            const l1 = typeof data.language1 === 'string' ? data.language1 : undefined;
            const l2 = typeof data.language2 === 'string' ? data.language2 : undefined;
            const c1 = typeof data.language1_category === 'string' ? data.language1_category : undefined;
            const c2 = typeof data.language2_category === 'string' ? data.language2_category : undefined;
            const qid1 = typeof data.language1_qid === 'string' ? data.language1_qid : undefined;
            const qid2 = typeof data.language2_qid === 'string' ? data.language2_qid : undefined;
            const relationship = typeof data.relationship === 'string' ? data.relationship : 'Child of';
            if (l1 && l2) {
              const childLabel = relationship === 'Child of' ? l1 : l1;
              const parentLabel = relationship === 'Child of' ? l2 : l2;
              const childQid = relationship === 'Child of' ? qid1 : qid1;
              const parentQid = relationship === 'Child of' ? qid2 : qid2;
              const parentId = ensureNode(parentLabel, c2, parentQid);
              const childId = ensureNode(childLabel, c1, childQid);
              if (parentId && childId) {
                const edgeId = `e-${parentId}-${childId}`;
                setEdges(prev => {
                  const edgeExists = prev.some(e => e.id === edgeId);
                  if (!edgeExists) {
                    setTimeout(() => layout('TB'), 100);
                    return [...prev, createEdge(parentId, childId)];
                  }
                  return prev;
                });

                setNodes(prev => prev.map(n => {
                  // Always ensure label-based expand is present
                  if (n.id === parentId && !n.data.onExpand) return { ...n, data: { ...n.data, onExpand: () => expandNodeByLabel(n.data.label) } };
                  if (n.id === childId && !n.data.onExpand) return { ...n, data: { ...n.data, onExpand: () => expandNodeByLabel(n.data.label) } };
                  return n;
                }));
              }
            }
          }
          break; }
        case 'expand_complete': {
          // Backend response for expansion using refined local-neighborhood logic
          type ExpandCompletePayload = { label?: string; added?: unknown[]; merged?: unknown[] };
          const payload: ExpandCompletePayload = isRecord(data) ? (data as ExpandCompletePayload) : {};
          const label = typeof payload.label === 'string' ? payload.label : undefined;
          const added = Array.isArray(payload.added) ? payload.added : [];

          // Normalize labels against existing nodes to avoid duplicates
          const labelByCanonical = new Map<string, string>();
          nodes.forEach(n => { labelByCanonical.set(canonical(n.data.label), n.data.label); });
          const preferExistingLabel = (lbl: string) => labelByCanonical.get(canonical(lbl)) || lbl;

          const parsedAdded = added.map(toRelationshipRecord).filter((r): r is RelationshipRecord => r !== null);

          // Ensure nodes exist and append only new edges
          for (const r of parsedAdded) {
            const parentLabel = preferExistingLabel(r.language2);
            const childLabel = preferExistingLabel(r.language1);
            if (!parentLabel || !childLabel) continue;
            const parentId = ensureNode(parentLabel, r.language2_category, r.language2_qid);
            const childId = ensureNode(childLabel, r.language1_category, r.language1_qid);
            if (!parentId || !childId) continue;
            const eid = `e-${parentId}-${childId}`;
            setEdges(prev => prev.some(e => e.id === eid) ? prev : [...prev, createEdge(parentId, childId)]);
          }

          // Ensure expand buttons remain available
          setNodes(prev => prev.map(n => ({ ...n, data: { ...n.data, onExpand: () => expandNodeByLabel(n.data.label) } })));

          const addedCount = parsedAdded.length;
          if (label) setStatus(`Expanded "${label}": ${addedCount} new relationship(s).`);
          if (autoLayoutOnComplete) setTimeout(() => layout(), 0);
          break; }
        case 'complete': {
          completeRef.current = true;
          setStatus('Completed');
          setProgress(100);
          if (autoLayoutOnComplete) setTimeout(() => layout(), 0);
          // Optionally process any relationships included in final payload not seen during stream
          if (data) {
            const relationshipsValue = Array.isArray(data.relationships)
              ? data.relationships
              : [];
            const parsedRelationships = relationshipsValue
              .map(toRelationshipRecord)
              .filter((r): r is RelationshipRecord => r !== null);
            for (const r of parsedRelationships) {
              const parentLabel = r.relationship === 'Child of' ? r.language2 : r.language2;
              const childLabel = r.relationship === 'Child of' ? r.language1 : r.language1;
              if (!parentLabel || !childLabel) continue;
              const parentId = ensureNode(parentLabel, r.language2_category, r.language2_qid);
              const childId = ensureNode(childLabel, r.language1_category, r.language1_qid);
              if (parentId && childId) {
                const edgeId = `e-${parentId}-${childId}`;
                setEdges(prev => prev.some(e => e.id === edgeId) ? prev : [...prev, createEdge(parentId, childId)]);
                setNodes(prev => prev.map(n => {
                  if (n.id === parentId && r.language2_qid && !n.data.onExpand) {
                    const qid = r.language2_qid;
                    return { ...n, data: { ...n.data, qid, onExpand: () => expandNodeByQid(qid) } };
                  }
                  if (n.id === childId && r.language1_qid && !n.data.onExpand) {
                    const qid = r.language1_qid;
                    return { ...n, data: { ...n.data, qid, onExpand: () => expandNodeByQid(qid) } };
                  }
                  return n;
                }));
              }
            }
          }
          // After completion, auto-fit the view so the full graph is visible
          // Use a slight delay to ensure layout/render commits before fitting
          setTimeout(() => {
            try { handleFitView(); } catch { /* no-op */ }
          }, 250);
          break; }
        case 'title_choices': {
          // { query, context, depth?, nodeLabel?, results: [{title, snippet, url}], existingGraph? }
          if (!data) break;
          const query = typeof data.query === 'string' ? data.query : '';
          const contextValue = typeof data.context === 'string' ? data.context : 'search';
          const context: 'search' | 'expand_node' | 'fetch_full_tree' =
            contextValue === 'expand_node' ? 'expand_node' : contextValue === 'fetch_full_tree' ? 'fetch_full_tree' : 'search';
          const d = typeof data.depth === 'number' ? data.depth : undefined;
          const nodeLabel = typeof data.nodeLabel === 'string' ? data.nodeLabel : undefined;
          const existingGraph = Array.isArray(data.existingGraph) ? (data.existingGraph as unknown as RelationshipRecord[]) : null;
          const results = Array.isArray(data.results)
            ? (data.results as unknown[])
                .map((r) => {
                  const rec = isRecord(r) ? (r as Record<string, unknown>) : undefined;
                  return {
                    title: rec && typeof rec.title === 'string' ? rec.title : '',
                    snippet: rec && typeof rec.snippet === 'string' ? rec.snippet : '',
                    url: rec && typeof rec.url === 'string' ? rec.url : ''
                  };
                })
                .filter((r) => r.title)
            : [];
          setTitleChoices({ query, context, depth: d, nodeLabel, results, existingGraph });
          setShowTitleModal(true);
          setStatus(`Select the correct Wikipedia page for "${query}"`);
          setProgress(0);
          break; }
        case 'error': {
          const messageText = data && typeof data.message === 'string' ? data.message : 'Unknown error';
          setStatus(`Error: ${messageText}`);
          setProgress(100);
          // If it looks like a missing or ambiguous title, auto-suggest
          const msgLower = (messageText || '').toLowerCase();
          if (/wikipedia|title|not\s*found|no\s*page/.test(msgLower)) {
            requestSuggestions(language, 'search', depth);
          }
          break; }
        default:
          break;
      }
    }
    lastProcessedIndexRef.current = messages.length;
  }, [messages, autoLayoutOnComplete, layout, ensureNode, setEdges, createEdge, expandNodeByQid, humanizeCategory, setNodes, expandNodeByLabel, canonical, nodes, handleFitView, requestSuggestions, language, depth]);

  const resetGraphState = useCallback((statusMessage: string) => {
    setNodes([]);
    setEdges([]);
    labelToIdRef.current = new Map();
    setStatus(statusMessage);
    setProgress(0);
    completeRef.current = false;
    searchSessionStartRef.current = messages.length;
    lastProcessedIndexRef.current = messages.length;
  }, [messages.length, setEdges, setNodes]);

  const handleSearch = useCallback(() => {
    console.info(`[RF] New search: language='${language}', depth=${depth}`);
    setIsFullTreeMode(false); // Depth-based search
    resetGraphState('Searching...');
    sendMessage(`${language},${depth}`);
  }, [language, depth, resetGraphState, sendMessage]);

  const handleSearchFull = useCallback(() => {
    console.info(`[RF] New full-tree search: language='${language}'`);
    const rootLabel = language.trim();
    if (!rootLabel) {
      setStatus('Please enter a language name.');
      return;
    }
    setIsFullTreeMode(true); // Full tree mode (no depth limit)
    resetGraphState('Fetching full language tree...');
    sendMessage({ action: 'fetch_full_tree', language: rootLabel });
  }, [language, resetGraphState, sendMessage]);

  const changeLayout = (dir: 'TB' | 'LR') => {
    setLayoutDirection(dir);
    layout(dir);
  };

  // Classify current node labels using backend batch endpoint (<=50 per call)
  const classifyRelationships = useCallback(async () => {
    if (nodes.length === 0) {
      alert('No nodes to classify. Add or fetch some languages first.');
      return;
    }
    if (classifying) return;
    setClassifying(true);
    try {
      const uniqueLabels = Array.from(new Set(nodes.map(n => (n.data.label || '').trim()).filter(Boolean)));
      const chunkSize = 50;
      let processed = 0;
      const chooseCategory = (types?: string[]): string | undefined => {
        if (!types || !types.length) return undefined;
        const tset = new Set(types.map(t => t.toLowerCase().replace(/\s+/g, '_')));
        if (tset.has('language_family')) return 'language_family';
        if (tset.has('proto_language')) return 'proto_language';
        
        if (tset.has('sign_language')) return 'sign_language';
        if (tset.has('creole_language')) return 'creole_language';
        if (tset.has('pidgin_language')) return 'pidgin_language';
        if (tset.has('extinct_language')) return 'extinct_language';
        if (tset.has('dead_language')) return 'dead_language';
        
        if (tset.has('modern_language')) return 'modern_language';
        if (tset.has('historical_language')) return 'historical_language';
        if (tset.has('ancient_language')) return 'ancient_language';
        if (tset.has('dialect')) return 'dialect';
        if (tset.has('language')) return 'language';
        return undefined;
      };

      for (let i = 0; i < uniqueLabels.length; i += chunkSize) {
        const batch = uniqueLabels.slice(i, i + chunkSize);
        setStatus(`Classifying languages ${i + 1}-${Math.min(i + batch.length, uniqueLabels.length)} of ${uniqueLabels.length}...`);
        setProgress(Math.round(((i) / uniqueLabels.length) * 100));
        const token = getToken();
        if (!token) {
        router.push('/login');
        return;
        }
        const resp = await fetch(`${httpBase}/classify/languages`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json','Authorization': `Bearer ${token}` },
          body: JSON.stringify({ names: batch })
        });
        if (!resp.ok) {
          const err = await resp.text();
          throw new Error(err || 'Classification request failed');
        }
  const data: Record<string, { qid?: string; types?: string[] } | null> = await resp.json();
        // Update nodes with qids, raw types, and inferred categories (non-destructive: don't overwrite existing category)
        setNodes(prev => prev.map(n => {
          const lbl = n.data.label;
          if (!batch.includes(lbl)) return n;
          const res = data[lbl];
          const updates: Partial<LanguageNodeData> = {};
          if (res && res.qid && n.data.qid !== res.qid) updates.qid = res.qid;
          if (res && res.types && res.types.length) updates.types = res.types;
          if (!res || !res.types || res.types.length === 0) {
            // No type resolved: mark as unresolved
            updates.category = 'unresolved';
            updates.meta = 'Unresolved';
          } else {
            const inferredCat = chooseCategory(res.types);
            if (inferredCat) {
              updates.category = inferredCat;
              updates.meta = humanizeCategory(inferredCat);
            }
          }
          return Object.keys(updates).length ? { ...n, data: { ...n.data, ...updates } } : n;
        }));
        processed += batch.length;
        setProgress(Math.round((processed / uniqueLabels.length) * 100));
      }
      setStatus('Classification complete');
      // Optional: relayout if categories changed visual sizing
      setTimeout(() => layout(), 0);
    } catch (err) {
      console.error('Classification error:', err);
      const msg = err instanceof Error ? err.message : 'Unknown error';
      setStatus(`Classification error: ${msg}`);
    } finally {
      setClassifying(false);
    }
  }, [classifying, httpBase, humanizeCategory, layout, nodes, setNodes, setStatus, setProgress, getToken, router]);

  
  // (Save graph removed for now to reduce lint noise; can be reintroduced in toolbar when needed)

  // Highlight edges connected to selected node without mutating core edge state
  const displayEdges = useMemo(() => {
    if (!selectedNodeId) return edges;
    const tintMarker = (marker: Edge['markerEnd'], color: string): Edge['markerEnd'] => {
      if (marker && typeof marker === 'object') {
        return { ...marker, color };
      }
      return marker;
    };
    return edges.map(e => {
      const isConnected = e.source === selectedNodeId || e.target === selectedNodeId;
      if (isConnected) {
        return {
          ...e,
          markerEnd: tintMarker(e.markerEnd, '#a855f7'),
          style: { ...(e.style || {}), stroke: '#c084fc', strokeWidth: 3, opacity: 1 },
          animated: true,
          className: (e.className ? e.className + ' ' : '') + 'edge-highlight'
        };
      }
      return {
        ...e,
        markerEnd: tintMarker(e.markerEnd, '#475569'),
  style: { ...(e.style || {}), stroke: '#475569', strokeWidth: 1, opacity: 0.25 },
        className: (e.className ? e.className + ' ' : '') + 'edge-dim'
      };
    });
  }, [edges, selectedNodeId]);

  // Handle node click: only select/deselect, do not auto-open sidebar
  const handleNodeClick = useCallback((event: React.MouseEvent, node: LanguageRFNode) => {
    setSelectedNodeId(prev => prev === node.id ? null : node.id);
    setSelectedLanguage({
      name: node.data.label,
      qid: node.data.qid,
      category: node.data.category
    });
    // Sidebar opening is now controlled via toolbar button
  }, []);

  const handleCloseSidebar = useCallback(() => {
    setSidebarOpen(false);
    setSelectedLanguage(null);
  }, []);

  // Export graph as PNG
  const exportAsPNG = useCallback(() => {
    const viewport = reactFlowRef.current?.querySelector('.react-flow__viewport') as HTMLElement;
    if (!viewport) {
      console.error('Viewport not found');
      return;
    }

    const nodesBounds = getRectOfNodes(getNodes());
    const transform = getTransformForBounds(
      nodesBounds,
      nodesBounds.width,
      nodesBounds.height,
      0.5,
      2,
      0.2
    );

    toPng(viewport, {
      backgroundColor: '#0f172a',
      width: nodesBounds.width,
      height: nodesBounds.height,
      style: {
        width: `${nodesBounds.width}px`,
        height: `${nodesBounds.height}px`,
        transform: `translate(${transform[0]}px, ${transform[1]}px) scale(${transform[2]})`,
      },
    }).then((dataUrl) => {
      const link = document.createElement('a');
      link.download = `${language || 'language-tree'}-graph.png`;
      link.href = dataUrl;
      link.click();
      setStatus('Graph exported as PNG');
    }).catch((err) => {
      console.error('Failed to export PNG:', err);
      setStatus('Error exporting PNG');
    });
  }, [getNodes, language]);

  // Export graph as PDF
  const exportAsPDF = useCallback(() => {
    const viewport = reactFlowRef.current?.querySelector('.react-flow__viewport') as HTMLElement;
    if (!viewport) {
      console.error('Viewport not found');
      return;
    }

    const nodesBounds = getRectOfNodes(getNodes());
    const transform = getTransformForBounds(
      nodesBounds,
      nodesBounds.width,
      nodesBounds.height,
      0.5,
      2,
      0.2
    );

    toJpeg(viewport, {
      backgroundColor: '#0f172a',
      width: nodesBounds.width,
      height: nodesBounds.height,
      quality: 0.95,
      style: {
        width: `${nodesBounds.width}px`,
        height: `${nodesBounds.height}px`,
        transform: `translate(${transform[0]}px, ${transform[1]}px) scale(${transform[2]})`,
      },
    }).then((dataUrl) => {
      const pdf = new jsPDF({
        orientation: nodesBounds.width > nodesBounds.height ? 'landscape' : 'portrait',
        unit: 'px',
        format: [nodesBounds.width, nodesBounds.height],
      });

      pdf.addImage(dataUrl, 'JPEG', 0, 0, nodesBounds.width, nodesBounds.height);
      pdf.save(`${language || 'language-tree'}-graph.pdf`);
      setStatus('Graph exported as PDF');
    }).catch((err) => {
      console.error('Failed to export PDF:', err);
      setStatus('Error exporting PDF');
    });
  }, [getNodes, language]);

  // Save graph to backend
  const handleSaveGraph = useCallback(async () => {
    if (!graphName.trim()) {
      alert('Please enter a graph name');
      return;
    }

    if (nodes.length === 0) {
      alert('Cannot save an empty graph');
      return;
    }

    setSavingGraph(true);
    try {
      const relationships = buildRelationshipsPayload();
      const token = getToken();

      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      const response = await fetch(`${apiBase}/api/users/graphs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          graph_name: graphName,
          graph_type: 'language',
          depth_usage: !isFullTreeMode && depth > 0,
          depth: !isFullTreeMode && depth > 0 ? depth : undefined,
          graph_data: relationships,
          description: graphDescription || undefined
        })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to save graph');
      }

      await response.json();
      setStatus(`Graph "${graphName}" saved successfully!`);
      setShowSaveModal(false);
      setGraphName('');
      setGraphDescription('');
    } catch (error) {
      console.error('Error saving graph:', error);
      const msg = error instanceof Error ? error.message : typeof error === 'string' ? error : 'Unknown error';
      alert(`Failed to save graph: ${msg}`);
      setStatus(`Error: ${msg}`);
    } finally {
      setSavingGraph(false);
    }
  }, [graphName, graphDescription, nodes, buildRelationshipsPayload, depth, getToken, isFullTreeMode]);

  // Load saved graphs list
  const loadSavedGraphs = useCallback(async () => {
    setLoadingGraphs(true);
    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
      const response = await fetch(`${apiBase}/api/users/graphs?graph_type=language`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load saved graphs');
      }

      const graphs = await response.json();
      setSavedGraphs(graphs);
    } catch (error) {
      console.error('Error loading graphs:', error);
      const msg = error instanceof Error ? error.message : typeof error === 'string' ? error : 'Unknown error';
      alert(`Failed to load saved graphs: ${msg}`);
    } finally {
      setLoadingGraphs(false);
    }
  }, [getToken]);

  // Load a specific graph
  const handleLoadGraph = useCallback(async (graphId: string) => {
    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
      const response = await fetch(`${apiBase}/api/users/graphs/${graphId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load graph');
      }

      const graph = await response.json();
      
      // Clear existing graph
      resetGraphState(`Loading "${graph.graph_name}"...`);
      
      // Rebuild graph from saved data
  const relationships = graph.graph_data as RelationshipRecord[];
      
      relationships.forEach((rel: RelationshipRecord) => {
        const parentLabel = rel.language2;
        const childLabel = rel.language1;
        
        if (parentLabel && childLabel) {
          const parentId = ensureNode(parentLabel, rel.language2_category, rel.language2_qid, rel.language2_types);
          const childId = ensureNode(childLabel, rel.language1_category, rel.language1_qid, rel.language1_types);
          
          if (parentId && childId) {
            const edgeId = `e-${parentId}-${childId}`;
            setEdges(prev => {
              if (prev.some(e => e.id === edgeId)) return prev;
              return [...prev, createEdge(parentId, childId)];
            });
          }
        }
      });

      setStatus(`Loaded "${graph.graph_name}" with ${relationships.length} relationships`);
      setShowLoadModal(false);
      
      // Layout after a short delay
      setTimeout(() => layout(), 100);
    } catch (error) {
      console.error('Error loading graph:', error);
      const msg = error instanceof Error ? error.message : typeof error === 'string' ? error : 'Unknown error';
      alert(`Failed to load graph: ${msg}`);
    }
  }, [getToken, resetGraphState, ensureNode, setEdges, createEdge, layout]);

  // Delete a saved graph
  const handleDeleteGraph = useCallback(async (graphId: string, graphName: string) => {
    if (!confirm(`Are you sure you want to delete "${graphName}"?`)) {
      return;
    }

    try {
      const token = getToken();
      const apiBase = process.env.NEXT_PUBLIC_API_GATEWAY_URL;
      
      const response = await fetch(`${apiBase}/api/users/graphs/${graphId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to delete graph');
      }

      // Refresh the list
      loadSavedGraphs();
    } catch (error) {
      console.error('Error deleting graph:', error);
      const msg = error instanceof Error ? error.message : typeof error === 'string' ? error : 'Unknown error';
      alert(`Failed to delete graph: ${msg}`);
    }
  }, [getToken, loadSavedGraphs]);

  // Open save modal
  const openSaveModal = useCallback(() => {
    if (nodes.length === 0) {
      alert('Cannot save an empty graph. Please create a graph first.');
      return;
    }
    setGraphName(`${language} Language Tree - ${new Date().toLocaleDateString()}`);
    setGraphDescription('');
    setShowSaveModal(true);
  }, [nodes.length, language]);

  // Open load modal
  const openLoadModal = useCallback(() => {
    setShowLoadModal(true);
    loadSavedGraphs();
  }, [loadSavedGraphs]);

  // Auto-load graph from URL parameter
  useEffect(() => {
    const loadGraphId = searchParams.get('loadGraph');
    if (loadGraphId && connectionStatus === 'connected') {
      // Auto-load the graph
      handleLoadGraph(loadGraphId);
      // Clean up URL parameter
      router.replace('/language_tree', { scroll: false });
    }
  }, [searchParams, connectionStatus, handleLoadGraph, router]);

  return (
    <div className="h-screen w-full flex flex-col bg-[#0E0F19] relative overflow-hidden">
      {/* Vertical Navbar */}
      <VerticalNavbar />
      
      {/* Animated gradient background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -inset-[10px] opacity-30">
          <div className="absolute top-0 -left-4 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
          <div className="absolute top-0 -right-4 w-96 h-96 bg-[#8B7BFF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-96 h-96 bg-[#5B62FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
        </div>
      </div>

      {/* Modern Dark Header with Glass Effect */}
      <div className="relative backdrop-blur-xl bg-white/5 border-b border-white/10 shadow-lg shadow-[#6B72FF]/10">
        <div className="relative px-6 py-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] rounded-xl flex items-center justify-center shadow-lg shadow-[#6B72FF]/30">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h1 className="text-[20px] font-bold bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
                Language Tree Explorer
              </h1>
            </div>
            
            {/* Connection Status with Modern Badge */}
            <div className="flex text-[12px] items-center space-x-2">
              <div className={`px-3 py-1.5 rounded-lg text-xs font-medium backdrop-blur-lg bg-white/5 border ${
                connectionStatus === 'connected' 
                  ? 'border-emerald-500/30 text-emerald-300' 
                  : connectionStatus === 'connecting'
                  ? 'border-amber-500/30 text-amber-300'
                  : 'border-red-500/30 text-red-300'
              }`}>
                <div className="flex items-center space-x-1.5">
                  <div className={`w-2 h-2 rounded-full ${
                    connectionStatus === 'connected' ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]' : 
                    connectionStatus === 'connecting' ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.6)] animate-pulse' : 
                    'bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.6)]'
                  }`}></div>
                  <span>{connectionStatus === 'connected' ? 'Connected' : connectionStatus === 'connecting' ? 'Connecting...' : 'Disconnected'}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Search Controls in Modern Card Layout */}
          <div className="flex text-[12px] items-center space-x-4 flex-wrap">
            {/* Language Input */}
            <div className="flex-1 min-w-48">
              <div className="relative">
                <input 
                  type="text" 
                  value={language} 
                  onChange={(e) => setLanguage(e.target.value)} 
                  placeholder="Enter language name..."
                  className="w-full px-4 py-3 pl-10 backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#6B72FF]/50 focus:border-[#6B72FF] transition-all duration-200 shadow-sm hover:shadow-md text-[#F5F7FA] placeholder-[#9CA3B5]"
                />
                <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#9CA3B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
            </div>

            {/* OR paste Wikipedia URL */}
            <div className="flex-1 min-w-64">
              <div className="relative">
                <input
                  type="url"
                  value={wikiUrl}
                  onChange={(e) => setWikiUrl(e.target.value)}
                  placeholder="Or paste a Wikipedia URL (e.g., https://en.wikipedia.org/wiki/English_language)"
                  className="w-full px-4 py-3 pl-10 backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#6B72FF]/50 focus:border-[#6B72FF] transition-all duration-200 shadow-sm hover:shadow-md text-[#F5F7FA] placeholder-[#9CA3B5]"
                />
                <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#9CA3B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 010 5.656l-2 2a4 4 0 11-5.656-5.656l1-1M10.172 13.828a4 4 0 010-5.656l2-2a4 4 0 115.656 5.656l-1 1" />
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
                className="w-full px-3 py-3 backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#6B72FF]/50 focus:border-[#6B72FF] transition-all duration-200 shadow-sm hover:shadow-md text-[#F5F7FA] text-center"
              />
            </div>

            {/* Explore Button */}
            <button 
              onClick={handleSearch} 
              disabled={connectionStatus !== 'connected'} 
              className="px-6 py-3 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] hover:from-[#7B82FF] hover:to-[#9B8BFF] disabled:from-gray-600 disabled:to-gray-700 text-white font-medium rounded-xl transition-all duration-200 shadow-lg shadow-[#6B72FF]/30 hover:shadow-[#6B72FF]/50 disabled:cursor-not-allowed disabled:shadow-sm transform hover:scale-105 disabled:hover:scale-100"
            >
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span>{connectionStatus === 'connected' ? 'Explore Depth' : 'Connecting...'}</span>
              </div>
            </button>

            <button
              onClick={handleSearchFull}
              disabled={connectionStatus !== 'connected'}
              className="px-6 py-3 bg-gradient-to-r from-[#5B62FF] to-[#7B72FF] hover:from-[#6B72FF] hover:to-[#8B82FF] disabled:from-gray-600 disabled:to-gray-700 text-white font-medium rounded-xl transition-all duration-200 shadow-lg shadow-[#5B62FF]/30 hover:shadow-[#5B62FF]/50 disabled:cursor-not-allowed disabled:shadow-sm transform hover:scale-105 disabled:hover:scale-100"
            >
              <div className="flex items-center space-x-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
                </svg>
                <span>{connectionStatus === 'connected' ? 'Explore Full Tree' : 'Connecting...'}</span>
              </div>
            </button>

            {/* Use URL Button */}
            <button 
              onClick={handleUseUrl}
              disabled={connectionStatus !== 'connected' || !wikiUrl.trim()}
              className="px-6 py-3 bg-white/5 hover:bg-white/10 disabled:bg-white/5 text-[#F5F7FA] font-medium rounded-xl transition-all duration-200 border border-white/10 disabled:cursor-not-allowed"
            >
              Use URL
            </button>

            {/* Find Pages Button */}
            <button 
              onClick={() => requestSuggestions(language, 'search', depth)}
              disabled={connectionStatus !== 'connected' || !language.trim()}
              className="px-6 py-3 bg-white/5 hover:bg-white/10 disabled:bg-white/5 text-[#F5F7FA] font-medium rounded-xl transition-all duration-200 border border-white/10 disabled:cursor-not-allowed"
            >
              Find Pages
            </button>

            {/* Layout Controls */}
            <div className="flex items-center space-x-2">
              <button 
                onClick={() => changeLayout('TB')} 
                className={`p-3 rounded-xl transition-all duration-200 shadow-sm hover:shadow-md ${
                  layoutDirection === 'TB' 
                    ? 'bg-[#6B72FF]/20 text-[#8B7BFF] border border-[#6B72FF]/30 shadow-[#6B72FF]/20' 
                    : 'backdrop-blur-lg bg-white/5 text-[#9CA3B5] border border-white/10 hover:bg-[#6B72FF]/10'
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
                    ? 'bg-[#6B72FF]/20 text-[#8B7BFF] border border-[#6B72FF]/30 shadow-[#6B72FF]/20' 
                    : 'backdrop-blur-lg bg-white/5 text-[#9CA3B5] border border-white/10 hover:bg-[#6B72FF]/10'
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
                className="w-4 h-4 text-[#6B72FF] bg-white/5 border-2 border-white/20 rounded focus:ring-[#6B72FF] focus:ring-2"
              />
              <span className=" font-medium text-[#F5F7FA]">Auto layout</span>
            </label>
          </div>

          {/* Progress info moved to floating status bar for consistency with family tree */}
        </div>
      </div>

      {/* React Flow Container with Modern Styling */}
      <div className="flex-1 text-[12px] relative" ref={reactFlowRef}>
        {/* Status toggle (collapsed) */}
        {isStatusCollapsed && (
          <button
            onClick={() => { setIsStatusCollapsed(false); setStatusPinnedOpen(true); }}
            className="absolute top-4 left-4 z-20 px-2 py-1  rounded-md bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10 shadow"
            title="Show status"
          >
            Status
          </button>
        )}

        {/* Horizontal Status Bar (collapsible) */}
        {!isStatusCollapsed && (
          <div className="absolute w-fit top-4 left-4 z-10 backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl shadow-lg">
            <div className="px-6 py-3 relative">
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  {connectionStatus === 'connecting' && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#8B7BFF]"></div>
                  )}
                  <span className=" w-full font-medium text-[#F5F7FA] flex-1 min-w-0 whitespace-pre-wrap break-words">
                    {status || (connectionStatus === 'connected' ? 'Idle' : 'Connecting...')}
                  </span>
                  <button
                    onClick={() => { setIsStatusCollapsed(true); setStatusPinnedOpen(false); }}
                    className="px-2 py-1 rounded bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10"
                    title="Hide status"
                  >
                    Hide
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  

                  {progress > 0 && (
                    <div className="flex items-center space-x-3">
                      <span className=" font-medium text-[#9CA3B5]">{progress}%</span>
                      <div className="w-32 backdrop-blur-lg bg-white/5 rounded-full h-2 overflow-hidden border border-white/10">
                        <div
                          className="h-full bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] rounded-full transition-all duration-300 ease-out shadow-lg shadow-[#6B72FF]/50"
                          style={{ width: `${progress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Toolbar toggle (collapsed) */}
        {isToolbarCollapsed && (
          <button
            onClick={() => { setIsToolbarCollapsed(false); setToolbarPinnedOpen(true); }}
            className="absolute top-4 right-4 z-20 px-2 py-1 text-[12px] rounded-md bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10 shadow"
            title="Show tools"
          >
            Tools
          </button>
        )}
        <ReactFlow
          nodes={nodes}
          edges={displayEdges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={(params: Connection) => setEdges((eds) => addEdge({ ...params, ...defaultEdgeOptions }, eds))}
          onNodeClick={handleNodeClick}
          onPaneClick={() => {
            setSelectedNodeId(null);
            setSidebarOpen(false);
            setSelectedLanguage(null);
          }}
          nodeTypes={nodeTypes}
          defaultEdgeOptions={defaultEdgeOptions}
          fitView
          className="bg-transparent"
          style={{ background: 'transparent' }}
        >
          <Controls 
            className="!bg-white/5 !backdrop-blur-xl !border-white/10 !shadow-lg !rounded-xl"
            style={{
              background: 'rgba(255, 255, 255, 0.05)',
              backdropFilter: 'blur(12px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              boxShadow: '0 8px 32px rgba(107, 114, 255, 0.2)'
            }}
          />
          <Background 
            color="#9CA3B5" 
            gap={20}
            size={1}
            className="opacity-10"
          />
          {/* Floating toolbar for CRUD operations (collapsible) */}
          {!isToolbarCollapsed && (
          <div className="absolute text-[12px] top-4 right-4 z-10 flex items-center gap-2 backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-2 shadow-lg shadow-[#6B72FF]/10">
            <button
              onClick={() => { setIsToolbarCollapsed(true); setToolbarPinnedOpen(false); }}
              className="px-2 py-1  rounded-md bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10"
              title="Hide tools"
            >
              Hide
            </button>
            <button
              onClick={addStandaloneNode}
              className="px-3 py-2  rounded-lg bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white hover:from-[#7B82FF] hover:to-[#9B8BFF] transition-all shadow-lg shadow-[#6B72FF]/30 hover:scale-105"
              title="Add node"
            >
              Add Node
            </button>
            <button
              onClick={addChildNode}
              disabled={!selectedNodeId}
              className={`px-3 py-2 rounded-lg transition-all shadow ${selectedNodeId ? 'backdrop-blur-lg bg-white/5 text-[#F5F7FA] hover:bg-[#6B72FF]/20 border border-white/10' : 'bg-white/5 text-[#9CA3B5] border border-white/10 cursor-not-allowed opacity-50'}`}
              title="Add child to selected"
            >
              Add Child
            </button>
            <button
              onClick={editSelectedNode}
              disabled={!selectedNodeId}
              className={`px-3 py-2  rounded-lg transition-all shadow ${selectedNodeId ? 'backdrop-blur-lg bg-white/5 text-[#F5F7FA] hover:bg-[#6B72FF]/20 border border-white/10' : 'bg-white/5 text-[#9CA3B5] border border-white/10 cursor-not-allowed opacity-50'}`}
              title="Edit selected node"
            >
              Edit
            </button>
            <button
              onClick={() => selectedNodeId && setSidebarOpen(true)}
              disabled={!selectedNodeId}
              className={`px-3 py-2  rounded-lg transition-all shadow ${selectedNodeId ? 'backdrop-blur-lg bg-white/5 text-[#F5F7FA] hover:bg-[#6B72FF]/20 border border-white/10' : 'bg-white/5 text-[#9CA3B5] border border-white/10 cursor-not-allowed opacity-50'}`}
              title="Open details sidebar for selected node"
            >
              View Info
            </button>
            <button
              onClick={deleteSelectedNode}
              disabled={!selectedNodeId}
              className={`px-3 py-2  rounded-lg transition-all shadow ${selectedNodeId ? 'bg-rose-600/80 text-white hover:bg-rose-600 hover:scale-105' : 'bg-white/5 text-[#9CA3B5] border border-white/10 cursor-not-allowed opacity-50'}`}
              title="Delete selected node"
            >
              Delete
            </button>
            <button
              onClick={deleteSelectedNode}
              disabled={!selectedNodeId}
              title="Delete Selected Node"
              className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-red-600/80 text-[#9CA3B5] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg border border-white/10 hover:scale-105"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
            <div className="w-px h-6 bg-white/10 mx-1" />
            <button
              onClick={openSaveModal}
              disabled={nodes.length === 0}
              title="Save Graph"
              className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-green-600/80 text-[#9CA3B5] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg border border-white/10 hover:scale-105"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
              </svg>
            </button>
            <button
              onClick={openLoadModal}
              title="Load Saved Graph"
              className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-amber-600/80 text-[#9CA3B5] hover:text-white transition-all shadow-md hover:shadow-lg border border-white/10 hover:scale-105"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
              </svg>
            </button>
            <div className="w-px h-6 bg-white/10 mx-1" />
            <button
              onClick={classifyRelationships}
              disabled={nodes.length === 0 || classifying}
              title="Classify Relationships"
              className={`px-3 py-2 rounded-lg transition-all shadow ${nodes.length && !classifying ? 'backdrop-blur-lg bg-white/5 text-[#F5F7FA] hover:bg-[#6B72FF]/20 border border-white/10 hover:scale-105' : 'bg-white/5 text-[#9CA3B5] border border-white/10 cursor-not-allowed opacity-50'}`}
            >
              {classifying ? 'Classifying…' : 'Classify Relationships'}
            </button>
            <div className="w-px h-6 bg-white/10 mx-1" />
            <button
              onClick={exportAsPNG}
              disabled={nodes.length === 0}
              title="Export as PNG"
              className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-blue-600/80 text-[#9CA3B5] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg border border-white/10 hover:scale-105"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </button>
            <button
              onClick={exportAsPDF}
              disabled={nodes.length === 0}
              title="Export as PDF"
              className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-purple-600/80 text-[#9CA3B5] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg border border-white/10 hover:scale-105"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
            </button>
          </div>
          )}
        </ReactFlow>
      </div>

      {/* Save Graph Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-[#1E1F2E] border border-white/10 rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-[#F5F7FA]">Save Language Tree</h2>
              <button
                onClick={() => setShowSaveModal(false)}
                className="text-[#9CA3B5] hover:text-[#F5F7FA] transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="graphName" className="block text-sm font-medium text-[#F5F7FA] mb-2">
                  Graph Name *
                </label>
                <input
                  id="graphName"
                  type="text"
                  value={graphName}
                  onChange={(e) => setGraphName(e.target.value)}
                  placeholder="e.g., Indo-European Language Family"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B72FF] text-[#F5F7FA] placeholder-[#9CA3B5]"
                />
              </div>
              
              <div>
                <label htmlFor="graphDescription" className="block text-sm font-medium text-[#F5F7FA] mb-2">
                  Description (Optional)
                </label>
                <textarea
                  id="graphDescription"
                  value={graphDescription}
                  onChange={(e) => setGraphDescription(e.target.value)}
                  placeholder="Add notes about this language tree..."
                  rows={3}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B72FF] text-[#F5F7FA] placeholder-[#9CA3B5] resize-none"
                />
              </div>

              <div className="bg-[#6B72FF]/10 border border-[#6B72FF]/20 rounded-lg p-3">
                <p className="text-sm text-[#9CA3B5]">
                  💾 This will save {buildRelationshipsPayload().length} language relationships
                  {!isFullTreeMode && depth > 0 && ` (depth: ${depth})`}
                  {isFullTreeMode && ' (full tree - no depth limit)'}
                </p>
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowSaveModal(false)}
                disabled={savingGraph}
                className="flex-1 px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-[#F5F7FA] rounded-lg transition-all disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                onClick={handleSaveGraph}
                disabled={!graphName.trim() || savingGraph}
                className="flex-1 px-4 py-3 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] hover:from-[#7B82FF] hover:to-[#9B8BFF] disabled:from-gray-600 disabled:to-gray-700 text-white rounded-lg transition-all disabled:cursor-not-allowed shadow-lg"
              >
                {savingGraph ? 'Saving...' : 'Save Graph'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Title Choices Modal */}
      {showTitleModal && titleChoices && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-[#1E1F2E] border border-white/10 rounded-2xl shadow-2xl max-w-3xl w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-[#F5F7FA]">Choose the correct Wikipedia page</h2>
              <button
                onClick={() => { setShowTitleModal(false); setTitleChoices(null); }}
                className="text-[#9CA3B5] hover:text-[#F5F7FA] transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <p className="text-sm text-[#9CA3B5] mb-4">We couldn&apos;t match &quot;{titleChoices.query}&quot; exactly. Pick one of the top results below, or paste a specific URL.</p>

            {/* Quick URL input inside modal */}
            <div className="flex items-center gap-2 mb-6">
              <input
                type="url"
                value={wikiUrl}
                onChange={(e) => setWikiUrl(e.target.value)}
                placeholder="Wikipedia URL (e.g., https://en.wikipedia.org/wiki/English_language)"
                className="flex-1 px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B72FF] text-[#F5F7FA] placeholder-[#9CA3B5]"
              />
              <button
                onClick={() => {
                  const url = (wikiUrl || '').trim();
                  if (!url || !titleChoices) return;
                  const payload: Record<string, unknown> = { action: 'start_with_url', url, context: titleChoices.context };
                  if (titleChoices.context === 'search') payload.depth = typeof titleChoices.depth === 'number' ? titleChoices.depth : depth;
                  if (titleChoices.context === 'expand_node') {
                    payload.existingGraph = titleChoices.existingGraph || buildRelationshipsPayload();
                    if (titleChoices.nodeLabel) payload.nodeLabel = titleChoices.nodeLabel;
                  }
                  setShowTitleModal(false);
                  setTitleChoices(null);
                  setStatus('Using Wikipedia URL...');
                  setProgress(0);
                  sendMessage(payload);
                }}
                disabled={!wikiUrl.trim()}
                className="px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-[#F5F7FA] rounded-lg transition-all disabled:opacity-50"
              >
                Use URL
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-[60vh] overflow-y-auto pr-1">
              {titleChoices.results.map((r, idx) => (
                <div key={`${r.title}-${idx}`} className="bg-white/5 border border-white/10 rounded-xl p-4 hover:bg-white/10 transition-all">
                  <div className="flex items-start justify-between">
                    <div className="pr-3">
                      <h3 className="text-[#F5F7FA] font-semibold">{r.title}</h3>
                      {r.snippet && <p className="text-sm text-[#9CA3B5] mt-2 line-clamp-3">{r.snippet}</p>}
                      <a href={r.url} target="_blank" rel="noreferrer" className="text-xs text-[#8B7BFF] hover:underline mt-2 inline-block">Open Wikipedia</a>
                    </div>
                    <button
                      onClick={() => {
                        // Choose this title
                        const chooseTitle = (title: string) => {
                          const payload: Record<string, unknown> = { action: 'choose_title', title, context: titleChoices.context };
                          if (titleChoices.context === 'search') {
                            payload.depth = typeof titleChoices.depth === 'number' ? titleChoices.depth : depth;
                          } else if (titleChoices.context === 'expand_node') {
                            payload.existingGraph = titleChoices.existingGraph || buildRelationshipsPayload();
                            if (titleChoices.nodeLabel) payload.nodeLabel = titleChoices.nodeLabel;
                          } else if (titleChoices.context === 'fetch_full_tree') {
                            // No extra fields; backend will do a full-tree fetch (depth=None)
                          }
                          setShowTitleModal(false);
                          setTitleChoices(null);
                          setStatus(`Using "${title}"...`);
                          setProgress(0);
                          sendMessage(payload);
                        };
                        chooseTitle(r.title);
                      }}
                      className="px-3 py-2 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white rounded-lg hover:scale-105 transition-all shadow-lg shadow-[#6B72FF]/30"
                    >
                      Use
                    </button>
                  </div>
                </div>
              ))}
            </div>

            {titleChoices.results.length === 0 && (
              <div className="text-center py-10 text-[#9CA3B5]">No results from Wikipedia search.</div>
            )}

            <div className="mt-6">
              <button
                onClick={() => { setShowTitleModal(false); setTitleChoices(null); }}
                className="w-full px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-[#F5F7FA] rounded-lg transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Load Graph Modal */}
      {showLoadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-[#1E1F2E] border border-white/10 rounded-2xl shadow-2xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-[#F5F7FA]">Load Saved Language Tree</h2>
              <button
                onClick={() => setShowLoadModal(false)}
                className="text-[#9CA3B5] hover:text-[#F5F7FA] transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {loadingGraphs ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-[#6B72FF]"></div>
              </div>
            ) : savedGraphs.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-16 h-16 mx-auto text-[#9CA3B5] mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
                </svg>
                <p className="text-[#9CA3B5]">No saved language trees found</p>
                <p className="text-sm text-[#9CA3B5] mt-2">Create and save a tree to see it here</p>
              </div>
            ) : (
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {savedGraphs.map((graph) => (
                  <div
                    key={graph.id}
                    className="bg-white/5 border border-white/10 rounded-lg p-4 hover:bg-white/10 transition-all"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h3 className="text-[#F5F7FA] font-semibold">{graph.graph_name}</h3>
                        {graph.description && (
                          <p className="text-sm text-[#9CA3B5] mt-1">{graph.description}</p>
                        )}
                        <div className="flex items-center space-x-4 mt-2 text-xs text-[#9CA3B5]">
                          <span>📊 {graph.nodes_count} relationships</span>
                          {graph.depth_usage && <span>🔍 Depth: {graph.depth}</span>}
                          <span>📅 {new Date(graph.updated_at).toLocaleDateString()}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        <button
                          onClick={() => handleLoadGraph(graph.id)}
                          className="px-3 py-2 bg-[#6B72FF]/20 hover:bg-[#6B72FF]/30 text-[#8B7BFF] rounded-lg transition-all text-sm"
                        >
                          Load
                        </button>
                        <button
                          onClick={() => handleDeleteGraph(graph.id, graph.graph_name)}
                          className="px-3 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-all text-sm"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="mt-6">
              <button
                onClick={() => setShowLoadModal(false)}
                className="w-full px-4 py-3 bg-white/5 hover:bg-white/10 border border-white/10 text-[#F5F7FA] rounded-lg transition-all"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Language Details Sidebar */}
      <LanguageDetailsSidebar
        isOpen={sidebarOpen}
        onClose={handleCloseSidebar}
        languageName={selectedLanguage?.name || ''}
        qid={selectedLanguage?.qid}
        category={selectedLanguage?.category}
      />

      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .animate-blob {
          /* Animation disabled for performance */
          animation: none;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
      `}</style>
    </div>
  );
};

const LanguageTreePageWrapper = () => (
    <ReactFlowProvider>
        <LanguageTreePage />
    </ReactFlowProvider>
);

export default function ProtectedLanguageTree(){
  return (
    <AuthGuard>
      <LanguageTreePageWrapper />
    </AuthGuard>
  );
}