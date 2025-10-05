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
import TaxonomyNode from '../../components/TaxonomyNode';

// Dagre layouting
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 220;
const nodeHeight = 60;

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

  // Create initial graph from scientific name
  const createTaxonomyGraph = useCallback(async (speciesName: string) => {
    setLoading(true);
    setStatus(`Loading taxonomy for ${speciesName}...`);
    
    try {
      // Try the real API first, fallback to mock data if service is not available
      let data;
      try {
        const response = await fetch(`http://127.0.0.1:8002/api/v1/taxonomy/${encodeURIComponent(speciesName)}`);
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
            { parent_taxon: "Eukarya", has_child: true, child_taxon: "Animalia" },
            { parent_taxon: "Animalia", has_child: true, child_taxon: "Chordata" }, 
            { parent_taxon: "Chordata", has_child: true, child_taxon: "Mammalia" },
            { parent_taxon: "Mammalia", has_child: true, child_taxon: "Primates" },
            { parent_taxon: "Primates", has_child: true, child_taxon: "Hominidae" },
            { parent_taxon: "Hominidae", has_child: true, child_taxon: "Homo" },
            { parent_taxon: "Homo", has_child: true, child_taxon: "Homo sapiens" },
            { parent_taxon: "Homo sapiens", has_child: false, child_taxon: speciesName }
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
        
        data.tuples.forEach((tuple: { parent_taxon: string; has_child: boolean; child_taxon: string }) => {
          const { parent_taxon: parentTaxon, has_child: hasChild, child_taxon: childTaxon } = tuple;
          
          // Create parent node if not exists
          if (!processedNodes.has(parentTaxon)) {
            ensureNode(parentTaxon, undefined, parentTaxon === speciesName ? speciesName : undefined);
            processedNodes.add(parentTaxon);
          }
          
          // Create child node if not exists
          if (!processedNodes.has(childTaxon)) {
            ensureNode(childTaxon, undefined, childTaxon === speciesName ? speciesName : undefined);
            processedNodes.add(childTaxon);
          }
          
          // Create edge from parent to child
          const parentId = slugify(parentTaxon);
          const childId = slugify(childTaxon);
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
    const expandKey = taxonName; // Simplified key since we don't need rank anymore
    
    // Prevent duplicate expansions
    if (expandedNodesRef.current.has(expandKey)) {
      return;
    }
    
    expandedNodesRef.current.add(expandKey);
    setStatus(`Expanding ${taxonName}...`);
    
    try {
      // Try the real API first, fallback to mock data if service is not available
      let data;
      try {
        const response = await fetch(`http://127.0.0.1:8002/api/v1/expand/${encodeURIComponent(taxonName)}`);
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
        data = {
          parent_taxon: taxonName,
          parent_rank: rank || 'unknown',
          child_rank: 'order',
          total_children: children.length,
          tuples: children.map(child => ({ parent_taxon: taxonName, has_child: true, child_taxon: child }))
        };
        setStatus(`Mock expansion for ${taxonName} (API not available)`);
      }
      
      if (data.tuples && Array.isArray(data.tuples)) {
        data.tuples.forEach((tuple: { parent_taxon: string; has_child: boolean; child_taxon: string }) => {
          const { parent_taxon: parentTaxon, has_child: hasChild, child_taxon: childTaxon } = tuple;
          
          // Create child node if not exists
          const childId = ensureNode(childTaxon, data.child_rank);
          
          // Create edge from parent to child
          const parentId = slugify(parentTaxon);
          if (childId && parentId) {
            ensureEdge(parentId, childId);
          }
        });
        
        setStatus(`Expanded ${taxonName}: found ${data.tuples.length} children`);
        
        // Re-layout the graph
        setTimeout(() => layout(), 100);
      } else {
        setStatus(`No children found for ${taxonName}`);
      }
      
    } catch (error: any) {
      console.error('Error expanding node:', error);
      setStatus(`Error expanding ${taxonName}: ${error.message}`);
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
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="flex-shrink-0 bg-white shadow-sm border-b p-4">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">Taxonomic Tree Explorer</h1>
        
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex gap-2">
            <input
              type="text"
              value={scientificName}
              onChange={(e) => setScientificName(e.target.value)}
              placeholder="Enter scientific name (e.g., Homo sapiens)"
              className="border rounded px-3 py-2 w-64 text-sm"
              disabled={loading}
            />
            <button
              onClick={handleSearch}
              disabled={loading}
              className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Loading...' : 'Create Tree'}
            </button>
          </div>
          
          <div className="flex gap-2">
            <button
              onClick={() => changeLayout('TB')}
              className={`px-3 py-2 rounded text-sm ${layoutDirection === 'TB' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Vertical
            </button>
            <button
              onClick={() => changeLayout('LR')}
              className={`px-3 py-2 rounded text-sm ${layoutDirection === 'LR' ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}
            >
              Horizontal
            </button>
          </div>
          
          <button
            onClick={clearGraph}
            className="bg-red-600 text-white px-4 py-2 rounded text-sm hover:bg-red-700"
          >
            Clear
          </button>
        </div>
        
        <div className="mt-2 text-sm text-gray-600">
          Status: {status}
        </div>
      </div>

      {/* React Flow Graph */}
      <div className="flex-1">
        <ReactFlowProvider>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            fitView
            fitViewOptions={{ padding: 0.1 }}
            className="bg-gray-50"
          >
            <Controls />
            <Background color="#aaa" gap={16} />
          </ReactFlow>
        </ReactFlowProvider>
      </div>
      
      {/* Info Panel */}
      <div className="flex-shrink-0 bg-white border-t p-4">
        <div className="text-sm text-gray-600">
          <div className="flex gap-6">
            <span>Nodes: {nodes.length}</span>
            <span>Edges: {edges.length}</span>
            <span>Click nodes to expand • Double-click to focus</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TaxonomyTreePage;