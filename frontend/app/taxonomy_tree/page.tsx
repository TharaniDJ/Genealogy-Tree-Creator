"use client";

import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import AuthGuard from '@/components/AuthGuard';
import VerticalNavbar from '@/components/VerticalNavbar';
import ReactFlow, {
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  ReactFlowProvider,
  Node,
  Edge,
  Position,
  useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import TaxonomyNode from '../../components/TaxonomyNode';
import useAuth from '@/hooks/useAuth';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { useRouter, useSearchParams } from 'next/navigation';

// Dagre layouting
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 220;
const nodeHeight = 100;

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

interface SavedGraph {
  id: string;
  graph_name: string;
  description?: string;
  nodes_count?: number;
  depth_usage?: boolean;
  depth?: number;
  updated_at: string;
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
  const router = useRouter();
  const searchParams = useSearchParams();
  const [nodes, setNodes, onNodesChange] = useNodesState<TaxonomyNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
  const [scientificName, setScientificName] = useState('Homo sapiens');
  const [status, setStatus] = useState('Ready');
  // Default to horizontal (Left-to-Right) layout for species/taxonomy trees
  const [layoutDirection, setLayoutDirection] = useState<'TB' | 'LR'>('LR');
  const [loading, setLoading] = useState(false);
  // Status bar visibility and auto-hide timer
  const [showStatusBar, setShowStatusBar] = useState(false);
  const statusTimeoutRef = useRef<number | null>(null);
  
  // Track expanded nodes to prevent duplicate expansions
  const expandedNodesRef = useRef<Set<string>>(new Set());
  
  // Track which nodes exist to prevent duplicates
  const existingNodesRef = useRef<Set<string>>(new Set());

  // Collapsible UI state for toolbar
  const [isToolbarCollapsed, setIsToolbarCollapsed] = useState(true);
  const [toolbarPinnedOpen, setToolbarPinnedOpen] = useState(false);
  
  // Graph saving state
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [showLoadModal, setShowLoadModal] = useState(false);
  const [graphName, setGraphName] = useState('');
  const [graphDescription, setGraphDescription] = useState('');
  const [savedGraphs, setSavedGraphs] = useState<SavedGraph[]>([]);
  const [loadingGraphs, setLoadingGraphs] = useState(false);
  const [savingGraph, setSavingGraph] = useState(false);

  const { fitView: fitViewApi } = useReactFlow();
  const reactFlowRef = useRef<HTMLDivElement>(null);
  const { getToken } = useAuth();

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
          // eslint-disable-next-line react-hooks/exhaustive-deps
          onExpand: () => expandNode(label, rank)
        }, 
        position: { x: 0, y: 0 },
        type: 'taxonomy'
      }];
    });
    
    return nodeId;
    // eslint-disable-next-line react-hooks/exhaustive-deps
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
          const { parent_taxon: parentTaxon, child_taxon: childTaxon } = tuple;
          
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
      
    } catch (error) {
      console.error('Error loading taxonomy:', error);
      setStatus(`Error: ${(error as Error).message}`);
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
          const { parent_taxon: parentTaxon, child_taxon: childTaxon } = tuple;
          
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
      
    } catch (error) {
      console.error('Error expanding node:', error);
      setStatus(`Error expanding ${taxonName} (${rank}): ${(error as Error).message}`);
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

  // Auto-load on component mount (create graph then apply initial layout)
  useEffect(() => {
    if (scientificName) {
      // Create graph then apply horizontal layout by default
      (async () => {
        await createTaxonomyGraph(scientificName);
        // ensure layout uses current layoutDirection (default LR)
        layout(layoutDirection);
      })();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Show the status bar when status text appears and auto-hide after idle
  useEffect(() => {
    // Clear existing timer
    if (statusTimeoutRef.current) {
      window.clearTimeout(statusTimeoutRef.current as unknown as number);
      statusTimeoutRef.current = null;
    }

    if (status && status !== 'Ready' && status !== '') {
      setShowStatusBar(true);
      // Auto-hide after 4 seconds of idle
      statusTimeoutRef.current = window.setTimeout(() => {
        setShowStatusBar(false);
      }, 4000);
    } else {
      // Hide immediately when status cleared or set to 'Ready'
      setShowStatusBar(false);
    }

    return () => {
      if (statusTimeoutRef.current) {
        window.clearTimeout(statusTimeoutRef.current as unknown as number);
        statusTimeoutRef.current = null;
      }
    };
  }, [status]);

  // Auto-manage toolbar collapse based on activity
  useEffect(() => {
    const hasActiveStatus = status && status !== 'Ready';
    const eventActive = loading || hasActiveStatus;

    if (eventActive) {
      setIsToolbarCollapsed(false);
    } else {
      if (!toolbarPinnedOpen) {
        setIsToolbarCollapsed(true);
      }
    }
  }, [loading, status, toolbarPinnedOpen]);

  // Build current relationships payload from edges + nodes
  const buildRelationshipsPayload = useCallback(() => {
    const idToNode = new Map(nodes.map(n => [n.id, n] as const));
    return edges.map(e => {
      const parentNode = idToNode.get(e.source);
      const childNode = idToNode.get(e.target);
      return {
        parent_taxon: {
          rank: parentNode?.data.rank || 'unknown',
          name: parentNode?.data.label || e.source,
        },
        has_child: true,
        child_taxon: {
          rank: childNode?.data.rank || 'unknown',
          name: childNode?.data.label || e.target,
        },
      };
    });
  }, [edges, nodes]);

  // Programmatic fit view button handler
  const handleFitView = useCallback(() => {
    setTimeout(() => {
      fitViewApi({ padding: 0.2, duration: 400 });
    }, 100);
  }, [fitViewApi]);

  // Export graph as PNG
  const exportAsPNG = useCallback(() => {
    if (!reactFlowRef.current) return;
    
    const viewport = reactFlowRef.current.querySelector('.react-flow__viewport') as HTMLElement;
    if (!viewport) {
      setStatus('Failed to find graph viewport');
      return;
    }

    setStatus('Exporting to PNG...');

    // Use html2canvas to capture the viewport
    html2canvas(viewport, {
      backgroundColor: '#0E0F19',
      scale: 3, // 3x resolution for high quality
      logging: false,
      useCORS: true,
      allowTaint: true,
    })
      .then((canvas) => {
        // Convert canvas to data URL
        const dataUrl = canvas.toDataURL('image/png', 1.0);
        
        // Download the image
        const link = document.createElement('a');
        link.download = `taxonomy-tree-${scientificName.replace(/\s+/g, '-')}-${Date.now()}.png`;
        link.href = dataUrl;
        link.click();
        
        setStatus('PNG exported successfully!');
      })
      .catch((err) => {
        console.error('Failed to export PNG:', err);
        setStatus('Failed to export PNG');
      });
  }, [scientificName]);

  // Export graph as PDF - captures full graph
  const exportAsPDF = useCallback(() => {
    if (!reactFlowRef.current) return;
    
    setStatus('Preparing PDF export...');

    // First, fit the view to show all nodes
    fitViewApi({ padding: 0.15, duration: 0 });

    // Wait for the fit to complete and render
    setTimeout(() => {
      const viewport = reactFlowRef.current?.querySelector('.react-flow__viewport') as HTMLElement;
      
      if (!viewport) {
        setStatus('Failed to find graph viewport');
        return;
      }

      setStatus('Capturing full graph...');

      // Use html2canvas to capture the entire viewport with all nodes visible
      html2canvas(viewport, {
        backgroundColor: '#0E0F19',
        scale: 2, // 2x resolution for good quality
        logging: false,
        useCORS: true,
        allowTaint: true,
        width: viewport.scrollWidth, // Capture full width including overflow
        height: viewport.scrollHeight, // Capture full height including overflow
      })
        .then((canvas) => {
          // Convert canvas to data URL
          const dataUrl = canvas.toDataURL('image/png', 1.0);
          
          // Get canvas dimensions
          const canvasWidth = canvas.width;
          const canvasHeight = canvas.height;
          
          // Determine orientation
          const orientation = canvasWidth > canvasHeight ? 'landscape' : 'portrait';
          
          // Convert pixels to mm for PDF (at 96 DPI: 1px = 0.264583mm)
          // Divide by scale to get actual dimensions
          const mmWidth = (canvasWidth / 2) * 0.264583;
          const mmHeight = (canvasHeight / 2) * 0.264583;
          
          setStatus('Creating PDF...');
          
          // Create PDF with custom page size matching the graph
          const pdf = new jsPDF({
            orientation: orientation,
            unit: 'mm',
            format: [mmWidth, mmHeight],
            compress: true,
          });

          // Add the image to PDF
          pdf.addImage(
            dataUrl,
            'PNG',
            0,
            0,
            mmWidth,
            mmHeight,
            undefined,
            'FAST'
          );
          
          // Save the PDF
          pdf.save(`taxonomy-tree-${scientificName.replace(/\s+/g, '-')}-${Date.now()}.pdf`);
          setStatus('PDF exported successfully!');
        })
        .catch((err) => {
          console.error('Failed to export PDF:', err);
          setStatus(`Failed to export PDF: ${err.message}`);
        });
    }, 500); // Give enough time for fitView to complete
  }, [scientificName, fitViewApi]);

  // Save graph to backend
  const handleSaveGraph = useCallback(async () => {
    if (!graphName.trim()) {
      setStatus('Please enter a graph name');
      return;
    }

    setSavingGraph(true);
    try {
      const base = process.env.NEXT_PUBLIC_USER_API_URL || 'http://localhost:8080/api/users';
      const token = getToken();

      if (!token) {
        setStatus('Please log in to save graphs');
        setSavingGraph(false);
        return;
      }

      const payload = {
        graph_name: graphName.trim(),
        graph_type: 'species',
        depth_usage: false,
        depth: null,
        graph_data: buildRelationshipsPayload(),
        description: graphDescription.trim() || null,
      };

      const response = await fetch(`${base}/graphs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save graph');
      }

      setStatus('Graph saved successfully!');
      setShowSaveModal(false);
      setGraphName('');
      setGraphDescription('');
    } catch (error) {
      console.error('Error saving graph:', error);
      setStatus(`Failed to save graph: ${(error as Error).message}`);
    } finally {
      setSavingGraph(false);
    }
  }, [graphName, graphDescription, buildRelationshipsPayload, getToken]);

  // Load saved graphs list
  const loadSavedGraphs = useCallback(async () => {
    setLoadingGraphs(true);
    try {
      const base = process.env.NEXT_PUBLIC_USER_API_URL || 'http://localhost:8080/api/users';
      const token = getToken();

      if (!token) {
        setStatus('Please log in to load graphs');
        setLoadingGraphs(false);
        return;
      }

      const response = await fetch(`${base}/graphs?graph_type=species`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error('Failed to load graphs');

      const graphs = await response.json();
      setSavedGraphs(graphs);
    } catch (error) {
      console.error('Error loading graphs:', error);
      setStatus(`Failed to load graphs: ${(error as Error).message}`);
    } finally {
      setLoadingGraphs(false);
    }
  }, [getToken]);

  // Load a specific graph
  const handleLoadGraph = useCallback(
    async (graphId: string) => {
      try {
        const base = process.env.NEXT_PUBLIC_USER_API_URL || 'http://localhost:8080/api/users';
        const token = getToken();

        if (!token) {
          setStatus('Please log in to load graphs');
          return;
        }

        const response = await fetch(`${base}/graphs/${graphId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) throw new Error('Failed to load graph');

        const graph = await response.json();
        setShowLoadModal(false);

        // Clear existing graph
        setNodes([]);
        setEdges([]);
        existingNodesRef.current.clear();
        expandedNodesRef.current.clear();

        // Process the tuples to create nodes and edges
        if (graph.graph_data && Array.isArray(graph.graph_data)) {
          graph.graph_data.forEach((tuple: TaxonomicTuple) => {
            const { parent_taxon: parentTaxon, child_taxon: childTaxon } = tuple;

            // Create nodes
            ensureNode(parentTaxon.name, parentTaxon.rank);
            ensureNode(childTaxon.name, childTaxon.rank);

            // Create edge
            const parentId = slugify(parentTaxon.name);
            const childId = slugify(childTaxon.name);
            ensureEdge(parentId, childId);
          });

          setStatus(`Loaded graph: ${graph.graph_name}`);
          setTimeout(() => layout(layoutDirection), 100);
        }
      } catch (error) {
        console.error('Error loading graph:', error);
        setStatus(`Failed to load graph: ${(error as Error).message}`);
      }
    },
    [getToken, setNodes, setEdges, ensureNode, ensureEdge, layout, layoutDirection]
  );

  // Delete a saved graph
  const handleDeleteGraph = useCallback(
    async (graphId: string, graphName: string) => {
      if (!confirm(`Are you sure you want to delete "${graphName}"?`)) return;

      try {
        const base = process.env.NEXT_PUBLIC_USER_API_URL || 'http://localhost:8080/api/users';
        const token = getToken();

        if (!token) {
          setStatus('Please log in to delete graphs');
          return;
        }

        const response = await fetch(`${base}/graphs/${graphId}`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) throw new Error('Failed to delete graph');

        setStatus(`Deleted graph: ${graphName}`);
        loadSavedGraphs();
      } catch (error) {
        console.error('Error deleting graph:', error);
        setStatus(`Failed to delete graph: ${(error as Error).message}`);
      }
    },
    [getToken, loadSavedGraphs]
  );

  // Open save modal
  const openSaveModal = useCallback(() => {
    if (nodes.length === 0) {
      setStatus('No graph to save');
      return;
    }
    setGraphName(`${scientificName} Taxonomy Tree`);
    setGraphDescription('');
    setShowSaveModal(true);
  }, [nodes.length, scientificName]);

  // Open load modal
  const openLoadModal = useCallback(() => {
    setShowLoadModal(true);
    loadSavedGraphs();
  }, [loadSavedGraphs]);

  // Auto-load graph from URL parameter
  useEffect(() => {
    const graphId = searchParams?.get('graphId');
    if (graphId) {
      handleLoadGraph(graphId);
      router.replace('/taxonomy_tree');
    }
  }, [searchParams, handleLoadGraph, router]);

  return (
    <div className="flex flex-col h-screen bg-[#0E0F19] relative overflow-hidden">
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

      {/* Header */}
      <div className="relative flex-shrink-0 backdrop-blur-xl bg-white/5 border-b border-white/10 shadow-lg shadow-[#6B72FF]/10 p-6">
        <div className="flex items-center space-x-3 mb-4">
          <div className="w-10 h-10 bg-gradient-to-br from-[#6B72FF] to-[#8B7BFF] rounded-xl flex items-center justify-center shadow-lg shadow-[#6B72FF]/30">
            <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
            </svg>
          </div>
          <h1 className="text-[20px] font-bold bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] bg-clip-text text-transparent">
            Taxonomic Tree Explorer
          </h1>
        </div>

        <div className="flex text-[12px] flex-wrap gap-4 items-center">
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
      </div>

      {/* React Flow Graph */}
      <div className="flex-1 relative" ref={reactFlowRef}>
        {/* Floating status overlay (does not take layout space). Centered horizontally near top of ReactFlow area. */}
        <div
          className={`absolute z-50 top-4 left-4 transition-all duration-300 flex items-center ${showStatusBar ? 'opacity-100 scale-100 pointer-events-auto' : 'opacity-0 scale-95 pointer-events-none'}`}
          style={{
            border: '2px solid rgba(255,255,255,0.95)',
            background: 'rgba(6,7,12,0.65)',
            padding: '6px 12px',
            borderRadius: 8,
            whiteSpace: 'nowrap',
            backdropFilter: 'blur(6px)'
          }}
        >
          <div className="text-sm text-white">{status}</div>
        </div>

        {/* Toolbar toggle (collapsed) */}
        {isToolbarCollapsed && (
          <button
            onClick={() => { setIsToolbarCollapsed(false); setToolbarPinnedOpen(true); }}
            className="absolute top-4 right-4 z-20 px-2 py-1 text-xs rounded-md bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10 shadow"
            title="Show tools"
          >
            Tools
          </button>
        )}

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
            
            {/* Floating toolbar for operations (collapsible) */}
            {!isToolbarCollapsed && (
              <div className="absolute top-4 right-4 z-10 flex items-center gap-2 backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-2 shadow-lg shadow-[#6B72FF]/10">
                <button
                  onClick={() => { setIsToolbarCollapsed(true); setToolbarPinnedOpen(false); }}
                  className="px-2 py-1 text-xs rounded-md bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10"
                  title="Hide tools"
                >
                  Hide
                </button>
                <button
                  onClick={handleFitView}
                  title="Fit View"
                  className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-[#6B72FF]/20 text-[#9CA3B5] hover:text-[#F5F7FA] transition-all shadow-md hover:shadow-lg border border-white/10 hover:scale-105"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
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
        </ReactFlowProvider>
      </div>
      
      {/* Info Panel */}
      <div className="relative rounded-r-lg w-2/12 flex-shrink-0 backdrop-blur-xl bg-white/5 border-t border-white/10 p-4">
        <div className="text-[12px] text-[#9CA3B5]">
          <div className="flex gap-6">
            <span className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-[#6B72FF]"></div>
              <span>Nodes: <span className="text-[#F5F7FA] font-medium">{nodes.length}</span></span>
            </span>
            <span className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-[#8B7BFF]"></div>
              <span>Edges: <span className="text-[#F5F7FA] font-medium">{edges.length}</span></span>
            </span>
           </div>
        </div>
      </div>

      {/* Save Graph Modal */}
      {showSaveModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-[#1E1F2E] border border-white/10 rounded-2xl shadow-2xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-[#F5F7FA]">Save Taxonomy Tree</h2>
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
                  placeholder="e.g., Homo sapiens Taxonomy"
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
                  placeholder="Add notes about this taxonomy tree..."
                  rows={3}
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B72FF] text-[#F5F7FA] placeholder-[#9CA3B5] resize-none"
                />
              </div>

              <div className="bg-[#6B72FF]/10 border border-[#6B72FF]/20 rounded-lg p-3">
                <p className="text-sm text-[#9CA3B5]">
                  💾 This will save {buildRelationshipsPayload().length} taxonomic relationships for {scientificName}
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

      {/* Load Graph Modal */}
      {showLoadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
          <div className="bg-[#1E1F2E] border border-white/10 rounded-2xl shadow-2xl max-w-2xl w-full p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold text-[#F5F7FA]">Load Saved Taxonomy Tree</h2>
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
                <p className="text-[#9CA3B5]">No saved taxonomy trees found</p>
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