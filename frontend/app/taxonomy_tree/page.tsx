"use client";

import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import AuthGuard from '@/components/AuthGuard';
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
import TaxonomyNode from '../../components/TaxonomyNode';

// Dagre layouting
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 220;
const nodeHeight = 60;

// TypeScript interfaces for the new API structure
interface TaxonomicEntity {
  rank: string;
  name: string;
}

interface TaxonomicTuple {
  parent_taxon: TaxonomicEntity;
  has_child: boolean;
  child_taxon: TaxonomicEntity;
}

interface TaxonomyApiResponse {
  scientific_name: string;
  total_relationships: number;
  tuples: TaxonomicTuple[];
  extraction_method?: string;
}

interface ExpansionApiResponse {
  parent_taxon: TaxonomicEntity;
  children: TaxonomicEntity[];
  tuples: TaxonomicTuple[];
  total_children: number;
}

type TaxonomyNodeData = { 
  label: string; 
  rank?: string; 
  scientificName?: string;
  onExpand?: () => void 
};
type TaxonomyRFNode = Node<TaxonomyNodeData>;

const getLayoutedElements = (nodes: TaxonomyRFNode[], edges: Edge[], direction = 'TB') => {
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

const TaxonomyTreePage = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState<TaxonomyNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
  const [scientificName, setScientificName] = useState('Homo sapiens');
  const [status, setStatus] = useState('Ready');
  const [layoutDirection, setLayoutDirection] = useState<'TB' | 'LR'>('TB');
  const [loading, setLoading] = useState(false);
  
  // Track expanded nodes to prevent duplicate expansions
  const expandedNodesRef = useRef<Set<string>>(new Set());
  
  // Track which nodes exist to prevent duplicates
  const existingNodesRef = useRef<Set<string>>(new Set());

  const nodeTypes = useMemo(() => ({ taxonomy: TaxonomyNode }), []);

  const layout = useCallback((direction: 'TB' | 'LR' = layoutDirection) => {
    setNodes(prevNodes => {
      setEdges(prevEdges => {
        const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements([...prevNodes.map(n => ({ ...n }))], [...prevEdges], direction);
        setNodes(layoutedNodes);
        return layoutedEdges;
      });
      return prevNodes; 
    });
  }, [layoutDirection, setNodes, setEdges]);

  const slugify = (label: string) => 
    label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$|/g, '').slice(0,40) || 'taxon';

  const ensureNode = useCallback((label: string, rank?: string, scientificName?: string) => {
    if (!label) return null;
    
    const nodeId = slugify(label);
    
    // Check if node already exists
    if (existingNodesRef.current.has(nodeId)) {
      return nodeId;
    }
    
    existingNodesRef.current.add(nodeId);
    
    setNodes(prev => {
      // Double check if node exists in current state
      if (prev.some(n => n.id === nodeId)) {
        return prev;
      }
      
      return [...prev, { 
        id: nodeId, 
        data: { 
          label,
          rank,
          scientificName,
          onExpand: () => expandNode(label, rank)
        }, 
        position: { x: 0, y: 0 },
        type: 'taxonomy'
      }];
    });
    
    return nodeId;
  }, [setNodes]);

  const ensureEdge = useCallback((sourceId: string, targetId: string) => {
    if (!sourceId || !targetId) return;
    
    const edgeId = `${sourceId}-${targetId}`;
    
    setEdges(prev => {
      // Check if edge already exists
      if (prev.some(e => e.id === edgeId)) {
        return prev;
      }
      
      return [...prev, {
        id: edgeId,
        source: sourceId,
        target: targetId,
        type: 'default',
        style: { stroke: '#64748b', strokeWidth: 2 }
      }];
    });
  }, [setEdges]);

  // Get authentication token from localStorage
  const getAuthToken = () => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  };

  // Create initial graph from scientific name
  const createTaxonomyGraph = useCallback(async (speciesName: string) => {
    setLoading(true);
    setStatus(`Loading taxonomy for ${speciesName}...`);
    
    try {
      // Try the real API first, fallback to mock data if service is not available
      let data;
      try {
        const base = process.env.NEXT_PUBLIC_SPECIES_API_URL || 'http://127.0.0.1:8002';
        const token = getAuthToken();
        
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
        };
        
        // Add Authorization header if token exists
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${base}/taxonomy/${encodeURIComponent(speciesName)}`, {
          headers
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        data = await response.json();
      } catch (apiError) {
        console.warn('API not available, using mock data:', apiError);
        // Mock data for testing
        data = {
          scientific_name: speciesName,
          total_relationships: 8,
          tuples: [
            { parent_taxon: { rank: "Domain", name: "Eukarya" }, has_child: true, child_taxon: { rank: "Kingdom", name: "Animalia" } },
            { parent_taxon: { rank: "Kingdom", name: "Animalia" }, has_child: true, child_taxon: { rank: "Phylum", name: "Chordata" } }, 
            { parent_taxon: { rank: "Phylum", name: "Chordata" }, has_child: true, child_taxon: { rank: "Class", name: "Mammalia" } },
            { parent_taxon: { rank: "Class", name: "Mammalia" }, has_child: true, child_taxon: { rank: "Order", name: "Primates" } },
            { parent_taxon: { rank: "Order", name: "Primates" }, has_child: true, child_taxon: { rank: "Family", name: "Hominidae" } },
            { parent_taxon: { rank: "Family", name: "Hominidae" }, has_child: true, child_taxon: { rank: "Genus", name: "Homo" } },
            { parent_taxon: { rank: "Genus", name: "Homo" }, has_child: true, child_taxon: { rank: "Species", name: "Homo sapiens" } },
            { parent_taxon: { rank: "Species", name: "Homo sapiens" }, has_child: false, child_taxon: { rank: "Species", name: speciesName } }
          ]
        };
        setStatus('Using mock data (API service not available)');
      }
      
      // Clear existing graph
      setNodes([]);
      setEdges([]);
      existingNodesRef.current.clear();
      expandedNodesRef.current.clear();
      
      // Process the tuples to create nodes and edges
      if (data.tuples && Array.isArray(data.tuples)) {
        const processedNodes = new Set<string>();
        
        data.tuples.forEach((tuple: TaxonomicTuple) => {
          const { parent_taxon: parentTaxon, has_child: hasChild, child_taxon: childTaxon } = tuple;
          
          // Create parent node if not exists
          if (!processedNodes.has(parentTaxon.name)) {
            ensureNode(parentTaxon.name, parentTaxon.rank, parentTaxon.name === speciesName ? speciesName : undefined);
            processedNodes.add(parentTaxon.name);
          }
          
          // Create child node if not exists
          if (!processedNodes.has(childTaxon.name)) {
            ensureNode(childTaxon.name, childTaxon.rank, childTaxon.name === speciesName ? speciesName : undefined);
            processedNodes.add(childTaxon.name);
          }
          
          // Create edge from parent to child
          const parentId = slugify(parentTaxon.name);
          const childId = slugify(childTaxon.name);
          ensureEdge(parentId, childId);
        });
        
        setStatus(`Loaded ${data.tuples.length} taxonomic relationships`);
        
        // Layout the graph after a short delay to ensure nodes are created
        setTimeout(() => layout(), 100);
      } else {
        setStatus('No taxonomic relationships found');
      }
      
    } catch (error: any) {
      console.error('Error loading taxonomy:', error);
      setStatus(`Error: ${error.message}`);
    } finally {
      setLoading(false);
    }
  }, [ensureNode, ensureEdge, setNodes, setEdges, layout]);

  // Expand a specific node to show its children
  const expandNode = useCallback(async (taxonName: string, rank?: string) => {
    const expandKey = `${taxonName}-${rank}`; // Include rank in the key to prevent duplicates
    
    // Validate that we have the rank parameter
    if (!rank) {
      console.warn(`Cannot expand ${taxonName}: rank is required`);
      setStatus(`Cannot expand ${taxonName}: taxonomic rank is required`);
      return;
    }
    
    // Prevent duplicate expansions
    if (expandedNodesRef.current.has(expandKey)) {
      return;
    }
    
    expandedNodesRef.current.add(expandKey);
    setStatus(`Expanding ${taxonName} (${rank})...`);
    
    try {
      // Try the real API first, fallback to mock data if service is not available
      let data;
      try {
        const base = process.env.NEXT_PUBLIC_SPECIES_API_URL || 'http://127.0.0.1:8002';
        const token = getAuthToken();
        
        const headers: HeadersInit = {
          'Content-Type': 'application/json',
        };
        
        // Add Authorization header if token exists
        if (token) {
          headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${base}/expand/${encodeURIComponent(taxonName)}/${encodeURIComponent(rank.toLowerCase())}`, {
          headers
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        data = await response.json();
      } catch (apiError) {
        console.warn('Expand API not available, using mock data:', apiError);
        // Mock expansion data
        const mockChildren = {
          'Mammalia': ['Primates', 'Carnivora', 'Cetacea', 'Ungulata'],
          'Primates': ['Hominidae', 'Cercopithecidae', 'Lemuridae'],
          'Carnivora': ['Felidae', 'Canidae', 'Ursidae'],
          'Chordata': ['Mammalia', 'Aves', 'Reptilia', 'Amphibia', 'Pisces']
        };
        
        const children = mockChildren[taxonName as keyof typeof mockChildren] || [];
        const childRank = rank === 'Class' ? 'Order' : rank === 'Order' ? 'Family' : 'species';
        data = {
          parent_taxon: { rank: rank || 'unknown', name: taxonName },
          children: children.map(child => ({ rank: childRank, name: child })),
          total_children: children.length,
          tuples: children.map(child => ({ 
            parent_taxon: { rank: rank || 'unknown', name: taxonName }, 
            has_child: true, 
            child_taxon: { rank: childRank, name: child }
          }))
        };
        setStatus(`Mock expansion for ${taxonName} (${rank}) - API not available`);
      }
      
      if (data.tuples && Array.isArray(data.tuples)) {
        data.tuples.forEach((tuple: TaxonomicTuple) => {
          const { parent_taxon: parentTaxon, has_child: hasChild, child_taxon: childTaxon } = tuple;
          
          // Create child node if not exists
          const childId = ensureNode(childTaxon.name, childTaxon.rank);
          
          // Create edge from parent to child
          const parentId = slugify(parentTaxon.name);
          if (childId && parentId) {
            ensureEdge(parentId, childId);
          }
        });
        
        setStatus(`Expanded ${taxonName} (${rank}): found ${data.tuples.length} children`);
        
        // Re-layout the graph
        setTimeout(() => layout(), 100);
      } else {
        setStatus(`No children found for ${taxonName} (${rank})`);
      }
      
    } catch (error: any) {
      console.error('Error expanding node:', error);
      setStatus(`Error expanding ${taxonName} (${rank}): ${error.message}`);
      // Remove from expanded set so user can retry
      expandedNodesRef.current.delete(expandKey);
    }
  }, [ensureNode, ensureEdge, layout]);

  const handleSearch = useCallback(() => {
    if (!scientificName.trim()) {
      setStatus('Please enter a scientific name');
      return;
    }
    
    createTaxonomyGraph(scientificName.trim());
  }, [scientificName, createTaxonomyGraph]);

  const changeLayout = (dir: 'TB' | 'LR') => {
    setLayoutDirection(dir);
    layout(dir);
  };

  const clearGraph = useCallback(() => {
    setNodes([]);
    setEdges([]);
    existingNodesRef.current.clear();
    expandedNodesRef.current.clear();
    setStatus('Graph cleared');
  }, [setNodes, setEdges]);

  // Auto-load on component mount
  useEffect(() => {
    if (scientificName) {
      createTaxonomyGraph(scientificName);
    }
  }, []);

  return (
    <div className="flex flex-col h-screen bg-[#0E0F19] relative overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -inset-[10px] opacity-30">
          <div className="absolute top-0 -left-4 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
          <div className="absolute top-0 -right-4 w-96 h-96 bg-[#8B7BFF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
          <div className="absolute -bottom-8 left-20 w-96 h-96 bg-[#5B62FF] rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
        </div>
      </div>

      {/* Header */}
      <div className="relative flex-shrink-0 backdrop-blur-xl bg-white/5 border-b border-white/10 shadow-lg shadow-[#6B72FF]/10 p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] rounded-xl flex items-center justify-center shadow-lg shadow-[#6B72FF]/30">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
            Taxonomic Tree Explorer
          </h1>
        </div>
        
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex gap-2 flex-1 min-w-[300px]">
            <div className="relative flex-1">
              <input
                type="text"
                value={scientificName}
                onChange={(e) => setScientificName(e.target.value)}
                placeholder="Enter scientific name (e.g., Homo sapiens)"
                disabled={loading}
                className="w-full px-4 py-3 pl-10 backdrop-blur-lg bg-white/5 border border-white/10 rounded-xl focus:outline-none focus:ring-2 focus:ring-[#6B72FF]/50 focus:border-[#6B72FF] transition-all duration-200 shadow-sm hover:shadow-md text-[#F5F7FA] placeholder-[#9CA3B5] disabled:opacity-50"
              />
              <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[#9CA3B5]" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="px-6 py-3 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] hover:from-[#7B82FF] hover:to-[#9B8BFF] disabled:from-gray-600 disabled:to-gray-700 text-white font-medium rounded-xl transition-all duration-200 shadow-lg shadow-[#6B72FF]/30 hover:shadow-[#6B72FF]/50 disabled:cursor-not-allowed disabled:shadow-sm transform hover:scale-105 disabled:hover:scale-100"
            >
              {loading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                  <span>Loading...</span>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                  </svg>
                  <span>Create Tree</span>
                </div>
              )}
            </button>
          </div>
          
          <div className="flex gap-2">
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
          
          <button
            onClick={clearGraph}
            className="px-4 py-3 bg-rose-600/80 hover:bg-rose-600 text-white font-medium rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl transform hover:scale-105"
          >
            <div className="flex items-center space-x-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
              <span>Clear</span>
            </div>
          </button>
        </div>
        
        <div className="mt-4 flex items-center space-x-2">
          <div className={`px-3 py-1.5 rounded-lg text-sm font-medium backdrop-blur-lg bg-white/5 border border-white/10 text-[#F5F7FA]`}>
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-[#6B72FF] shadow-[0_0_8px_rgba(107,114,255,0.6)]"></div>
              <span>{status}</span>
            </div>
          </div>
        </div>
      </div>

      {/* React Flow Graph */}
      <div className="flex-1 relative">
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.1 }}
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
          </ReactFlow>
        </ReactFlowProvider>
      </div>
      
      {/* Info Panel */}
      <div className="relative flex-shrink-0 backdrop-blur-xl bg-white/5 border-t border-white/10 p-4">
        <div className="text-sm text-[#9CA3B5]">
          <div className="flex gap-6">
            <span className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-[#6B72FF]"></div>
              <span>Nodes: <span className="text-[#F5F7FA] font-medium">{nodes.length}</span></span>
            </span>
            <span className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-[#8B7BFF]"></div>
              <span>Edges: <span className="text-[#F5F7FA] font-medium">{edges.length}</span></span>
            </span>
            <span className="text-[#F5F7FA]">Click nodes to expand • Double-click to focus</span>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes blob {
          0%, 100% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
        }
        .animate-blob {
          animation: blob 7s infinite;
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

const TaxonomyTreePageWrapper = () => (
    <ReactFlowProvider>
        <TaxonomyTreePage />
    </ReactFlowProvider>
);

export default function ProtectedTaxonomyTree(){
  return (
    <AuthGuard>
      <TaxonomyTreePageWrapper />
    </AuthGuard>
  );
}