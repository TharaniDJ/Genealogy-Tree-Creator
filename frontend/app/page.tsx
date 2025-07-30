'use client';
import React, { useState, useCallback, useEffect, useRef } from 'react';
import ReactFlow, {
  Node,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  MarkerType,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { NodeData, GenerationInfo, Marriage,PersonData } from '@/lib/types';
import PersonNode from '@/components/person-node';
import MarriageNode from '@/components/marriage-node';

import { getHierarchicalPosition, getNodeColor, getEdgeColor } from '@/lib/utils';

const nodeTypes = {
  person: PersonNode,
  marriage: MarriageNode,
};

export default function KnowledgeGraph() {
  
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [showGenerationLines, setShowGenerationLines] = useState(true);
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connected' | 'loading'>('disconnected');
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('Albert Einstein');
  const [relationships, setRelationships] = useState<any[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  
  // Generation tracking for hierarchical layout
  const generationData = useRef<Record<string, GenerationInfo>>({});
  const generationCounts = useRef<Record<number, number>>({});
  const nodeConnections = useRef<Record<string, number>>({});
  const marriages = useRef<Record<string, Marriage>>({});

  // Dynamic person data with fallbacks
  const getPersonData = useCallback((name: string): PersonData | undefined => {
    // First check if we have specific data for known people
    const personDataMap: Record<string, PersonData> = {
      "Albert Einstein": {
        name: "Albert Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1879,
        deathYear: 1955
      },
      "Hermann Einstein": {
        name: "Hermann Einstein", 
        image: "/placeholder-user.jpg",
        birthYear: 1847,
        deathYear: 1902
      },
      "Pauline Koch": {
        name: "Pauline Koch",
        image: "/placeholder-user.jpg", 
        birthYear: 1858,
        deathYear: 1920
      },
      "Mileva Marić": {
        name: "Mileva Marić",
        image: "/placeholder-user.jpg",
        birthYear: 1875,
        deathYear: 1948
      },
      "Elsa Einstein": {
        name: "Elsa Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1876,
        deathYear: 1936
      },
      "Hans Albert Einstein": {
        name: "Hans Albert Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1904,
        deathYear: 1973
      },
      "Eduard Einstein": {
        name: "Eduard Einstein", 
        image: "/placeholder-user.jpg",
        birthYear: 1910,
        deathYear: 1965
      },
      "Lieserl Einstein": {
        name: "Lieserl Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1902,
        deathYear: 1903
      },
      "Lieserl (Einstein)": {
        name: "Lieserl Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1902,
        deathYear: 1903
      }
    };
    
    // Return specific data if available, otherwise create fallback data
    return personDataMap[name] || {
      name: name,
      image: "/placeholder-user.jpg",
      birthYear: 1900, // Default birth year
    };
  }, []);

  // Helper function to create person node
  const createPersonNode = useCallback((id: string, generation: number, personData?: PersonData) => {
    const pos = getHierarchicalPosition(id, generation, generationCounts, generationData);
    return {
      id,
      type: 'person',
      position: pos,
      data: { 
        label: id, 
        generation,
        connections: 0,
        nodeType: 'person' as const,
        personData
      },
      style: {
        background: getNodeColor(generation, 0),
        border: '3px solid #ffffff',
        borderRadius: '15px',
        padding: '12px',
        minWidth: '140px',
        minHeight: '100px',
        fontSize: '12px',
        fontWeight: 'bold',
        color: '#ffffff',
        textShadow: '1px 1px 2px rgba(0,0,0,0.7)',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
      },
    };
  }, []);

  // Helper function to create marriage node
  const createMarriageNode = useCallback((marriageId: string, generation: number) => {
    const pos = getHierarchicalPosition(marriageId, generation, generationCounts, generationData);
    return {
      id: marriageId,
      type: 'marriage',
      position: pos,
      data: { 
        label: 'Marriage', 
        generation,
        connections: 0,
        nodeType: 'marriage'
      },
      style: {
        background: 'linear-gradient(45deg, #FFD700, #FFA500)',
        border: '2px solid #ffffff',
        borderRadius: '50%',
        padding: '4px',
        width: '10px',
        height: '10px',
        fontSize: '8px',
        fontWeight: 'bold',
        color: '#333',
        boxShadow: '0 4px 12px rgba(255,215,0,0.4)',
      },
    };
  }, []);

  // Helper function to create marriage connection edge
  const createMarriageEdge = useCallback((personId: string, marriageId: string, gender: 'father' | 'mother') => {
    const edgeId = `${personId}-to-${marriageId}`;
    
    return {
      id: edgeId,
      source: personId,
      target: marriageId,
      targetHandle: gender === 'father' ? 'left' : 'right',
      type: 'smoothstep',
      label: '',
      style: {
        stroke: '#FF69B4',
        strokeWidth: 2,
        strokeOpacity: 0.8,
        strokeDasharray: '3,3',
      },
      animated: true,
      data: { relationshipType: 'marriage', gender },
    };
  }, []);

  // Helper function to create parent-child edge
  const createParentChildEdge = useCallback((marriageId: string, childId: string, edgeCount: number) => {
    const edgeColor = getEdgeColor(edgeCount);
    const edgeId = `${marriageId}-to-${childId}`;
    
    return {
      id: edgeId,
      source: marriageId,
      target: childId,
      type: 'smoothstep',
      label: '',
      style: {
        stroke: edgeColor,
        strokeWidth: 2,
        strokeOpacity: 0.8,
        strokeDasharray: '3,3',
      },
      animated: true,
      data: { relationshipType: 'parent-child' },
    };
  }, []);

  // Function to update edges when hover state changes
  const updateEdgesForHover = useCallback(() => {
    setEdges((currentEdges) => {
      return currentEdges.map((edge) => {
        const isHovered = hoveredEdge === edge.id;
        
        if (edge.data?.relationshipType === 'parent-child') {
          // This is a parent-child edge
          return {
            ...edge,
            label: isHovered ? 'Parent-Child' : '',
            labelStyle: isHovered ? {
              fill: '#ffffff',
              fontWeight: 'bold',
              fontSize: '10px',
              background: 'rgba(0,0,0,0.7)',
              padding: '2px 6px',
              borderRadius: '4px',
            } : {},
            labelShowBg: isHovered,
            labelBgStyle: isHovered ? {
              fill: 'rgba(0,0,0,0.7)',
              fillOpacity: 0.8,
            } : {},
          };
        } else if (edge.data?.relationshipType === 'marriage') {
          // This is a marriage edge
          const gender = edge.data.gender;
          return {
            ...edge,
            label: isHovered ? `Spouse (${gender})` : '',
            labelStyle: isHovered ? {
              fill: '#ffffff',
              fontWeight: 'bold',
              fontSize: '10px',
              background: 'rgba(0,0,0,0.7)',
              padding: '2px 6px',
              borderRadius: '4px',
            } : {},
            labelShowBg: isHovered,
            labelBgStyle: isHovered ? {
              fill: 'rgba(0,0,0,0.7)',
              fillOpacity: 0.8,
            } : {},
          };
        }
        
        return edge;
      });
    });
  }, [hoveredEdge, setEdges]);

  // Update edges when hover state changes
  useEffect(() => {
    updateEdgesForHover();
  }, [updateEdgesForHover]);

  // Function to add or update nodes
  const addNodes = useCallback((parent: string, child: string, spouse: string | undefined, parentGen: number, childGen: number, marriageId: string) => {
    setNodes((nds) => {
      const updatedNodes = [...nds];
      
      // Add parent node if it doesn't exist
      if (!updatedNodes.find(n => n.id === parent)) {
        const parentData = getPersonData(parent);
        updatedNodes.push(createPersonNode(parent, parentGen, parentData));
      }
      
      // Add spouse node if specified and doesn't exist
      if (spouse && !updatedNodes.find(n => n.id === spouse)) {
        const spouseData = getPersonData(spouse);
        updatedNodes.push(createPersonNode(spouse, parentGen, spouseData));
      }
      
      // Add marriage node if it doesn't exist
      if (!updatedNodes.find(n => n.id === marriageId)) {
        const marriageGen = parentGen + 0.5;
        updatedNodes.push(createMarriageNode(marriageId, marriageGen));
      }
      
      // Add child node if it doesn't exist
      if (!updatedNodes.find(n => n.id === child)) {
        const childData = getPersonData(child);
        updatedNodes.push(createPersonNode(child, childGen, childData));
      }
      
      return updatedNodes;
    });
  }, [createPersonNode, createMarriageNode, setNodes, getPersonData]);

  // Function to manage marriage tracking
  const updateMarriageTracking = useCallback((marriageId: string, parent: string, spouse: string | undefined, child: string, parentGender: 'father' | 'mother', parentGen: number) => {
    if (!marriages.current[marriageId]) {
      marriages.current[marriageId] = {
        id: marriageId,
        father: parentGender === 'father' ? parent : (spouse || ''),
        mother: parentGender === 'mother' ? parent : spouse,
        children: [child],
        generation: parentGen + 0.5
      };
    } else {
      if (!marriages.current[marriageId].children.includes(child)) {
        marriages.current[marriageId].children.push(child);
      }
    }
  }, []);

  // Function to add or update edges
  const addEdges = useCallback((parent: string, child: string, spouse: string | undefined, marriageId: string, parentGender: 'father' | 'mother') => {
    setEdges((eds) => {
      const newEdges = [...eds];
      
      // Connect parent to marriage (father to left, mother to right)
      const parentToMarriageId = `${parent}-to-${marriageId}`;
      if (!newEdges.find(e => e.id === parentToMarriageId)) {
        newEdges.push(createMarriageEdge(parent, marriageId, parentGender));
      }
      
      // Connect spouse to marriage if exists (opposite gender)
      if (spouse) {
        const spouseGender = parentGender === 'father' ? 'mother' : 'father';
        const spouseToMarriageId = `${spouse}-to-${marriageId}`;
        if (!newEdges.find(e => e.id === spouseToMarriageId)) {
          newEdges.push(createMarriageEdge(spouse, marriageId, spouseGender));
        }
      }
      
      // Connect marriage to child
      const marriageToChildId = `${marriageId}-to-${child}`;
      if (!newEdges.find(e => e.id === marriageToChildId)) {
        newEdges.push(createParentChildEdge(marriageId, child, newEdges.length));
      }
      
      return newEdges;
    });
  }, [createMarriageEdge, createParentChildEdge, setEdges]);

  // Main function that orchestrates the family relation addition
  const addFamilyRelation = useCallback((parent: string, parentGender: 'father' | 'mother', child: string, parentGen: number, childGen: number, spouse?: string) => {
    console.log(`Adding family relation: ${parent} (${parentGender}) -> ${child}${spouse ? ` with spouse ${spouse}` : ''}`);
    
    // Create marriage ID
    const marriageId = spouse ? 
      `marriage-${[parent, spouse].sort().join('-')}` : 
      `marriage-${parent}-single`;
    
    // Add all nodes
    addNodes(parent, child, spouse, parentGen, childGen, marriageId);
    
    // Update marriage tracking
    updateMarriageTracking(marriageId, parent, spouse, child, parentGender, parentGen);
    
    // Add all edges
    addEdges(parent, child, spouse, marriageId, parentGender);
  }, [addNodes, updateMarriageTracking, addEdges]);

  // WebSocket connection setup
  useEffect(() => {
    const connectWebSocket = () => {
      setWsStatus('loading');
      const ws = new WebSocket('ws://localhost:8000/ws');
      
      ws.onopen = () => {
        setWsStatus('connected');
        wsRef.current = ws;
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'relationship') {
            setRelationships(prev => [...prev, message.data]);
          } else if (message.type === 'status') {
            if (message.data.message === 'Collection complete!') {
              setIsSearching(false);
            }
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
      
      ws.onclose = () => {
        setWsStatus('disconnected');
        wsRef.current = null;
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setWsStatus('disconnected');
      };
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Function to start fetching relationships
  const fetchRelationships = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setIsSearching(true);
      setRelationships([]);
      generationData.current = {};
      generationCounts.current = {};
      nodeConnections.current = {};
      marriages.current = {};
      setNodes([]);
      setEdges([]);
      
      const message = {
        action: 'fetch_relationships',
        page_title: searchQuery,
        depth: 2
      };
      
      wsRef.current.send(JSON.stringify(message));
    }
  };

  // Process relationships data to build family tree
  useEffect(() => {
    if (relationships.length === 0) return;
    
    const processRelationships = () => {
      // Group relationships by type
      const childParentRels: { child: string, parent: string }[] = [];
      const spouseRels: { person1: string, person2: string }[] = [];
      
      relationships.forEach((rel) => {
        const { entity1, relationship, entity2 } = rel;
        
        if (relationship === 'child of') {
          childParentRels.push({ child: entity1, parent: entity2 });
        } else if (relationship === 'spouse of') {
          spouseRels.push({ person1: entity1, person2: entity2 });
        }
      });
      
      // Create a map to track spouses for each person
      const spouseMap = new Map<string, string>();
      spouseRels.forEach(({ person1, person2 }) => {
        spouseMap.set(person1, person2);
        spouseMap.set(person2, person1);
      });
      
      // Calculate generations automatically
      const calculateGenerations = () => {
        const personGenerations = new Map<string, number>();
        const processed = new Set<string>();
        
        // Find all unique people
        const allPeople = new Set<string>();
        childParentRels.forEach(({ child, parent }) => {
          allPeople.add(child);
          allPeople.add(parent);
        });
        spouseRels.forEach(({ person1, person2 }) => {
          allPeople.add(person1);
          allPeople.add(person2);
        });
        
        // Find root generation (people who are parents but not children)
        const children = new Set(childParentRels.map(rel => rel.child));
        const parents = new Set(childParentRels.map(rel => rel.parent));
        const rootGeneration = Array.from(parents).filter(parent => !children.has(parent));
        
        // Assign generation 0 to root generation
        rootGeneration.forEach(person => {
          personGenerations.set(person, 0);
          processed.add(person);
        });
        
        // If no clear root, pick the search query person as generation 0
        if (rootGeneration.length === 0 && allPeople.has(searchQuery)) {
          personGenerations.set(searchQuery, 0);
          processed.add(searchQuery);
        }
        
        // Iteratively assign generations
        let changed = true;
        while (changed) {
          changed = false;
          
          childParentRels.forEach(({ child, parent }) => {
            if (personGenerations.has(parent) && !personGenerations.has(child)) {
              personGenerations.set(child, personGenerations.get(parent)! + 1);
              processed.add(child);
              changed = true;
            }
          });
          
          // Assign same generation to spouses
          spouseRels.forEach(({ person1, person2 }) => {
            if (personGenerations.has(person1) && !personGenerations.has(person2)) {
              personGenerations.set(person2, personGenerations.get(person1)!);
              processed.add(person2);
              changed = true;
            } else if (personGenerations.has(person2) && !personGenerations.has(person1)) {
              personGenerations.set(person1, personGenerations.get(person2)!);
              processed.add(person1);
              changed = true;
            }
          });
        }
        
        // Assign default generation to any remaining unprocessed people
        allPeople.forEach(person => {
          if (!personGenerations.has(person)) {
            personGenerations.set(person, 1); // Default generation
          }
        });
        
        return personGenerations;
      };
      
      const personGenerations = calculateGenerations();
      
      // Process parent-child relationships with calculated generations
      childParentRels.forEach((rel, index) => {
        setTimeout(() => {
          const { child, parent } = rel;
          const spouse = spouseMap.get(parent);
          
          // Use calculated generations
          const parentGen = personGenerations.get(parent) || 0;
          const childGen = personGenerations.get(child) || 1;
          
          console.log(`Processing: ${parent} (gen ${parentGen}) -> ${child} (gen ${childGen})`);
          
          // Add family relation with spouse if available
          addFamilyRelation(parent, "father", child, parentGen, childGen, spouse);
        }, index * 400);
      });
    };
    
    // Small delay to ensure UI is ready
    const timer = setTimeout(processRelationships, 500);
    return () => clearTimeout(timer);
  }, [relationships, addFamilyRelation, searchQuery]);

  // Initialize with WebSocket data loading
  useEffect(() => {
    // Auto-fetch relationships when component mounts and WebSocket is connected
    const timer = setTimeout(() => {
      if (wsStatus === 'connected') {
        fetchRelationships();
      }
    }, 1000);
    
    return () => clearTimeout(timer);
  }, [wsStatus]);

 



  // Function to render generation lines
  // development feature to visualize generations
  const renderGenerationLines = () => {
    if (!showGenerationLines) return null;
    
    const generations = Object.keys(generationCounts.current).map(Number).sort((a, b) => a - b);
    
    return generations.map((gen) => (
      <div
        key={`gen-line-${gen}`}
        className="absolute pointer-events-none"
        style={{
          top: `${gen * 250 + 50}px`,
          left: '0',
          right: '0',
          height: '2px',
          background: 'rgba(255, 255, 255, 0.3)',
          borderTop: '2px dashed rgba(255, 255, 255, 0.5)',
          zIndex: 1,
        }}
      >
        <div
          className="absolute left-4 top-[-12px] text-white text-sm font-bold bg-black/30 px-2 py-1 rounded"
          style={{ zIndex: 2 }}
        >
          Generation {gen + 1}
        </div>
      </div>
    ));
  };

  return (
  <div className="w-screen h-screen bg-gradient-to-br from-indigo-500 to-purple-700 relative">
    {/* Search Controls */}
    <div className="absolute top-4 left-4 z-10 bg-white/10 backdrop-blur-md rounded-lg p-4 min-w-[300px]">
      <div className="flex flex-col gap-2">
        <label className="text-white text-sm font-medium">Search Person:</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter person name..."
            className="flex-1 px-3 py-2 rounded bg-white/20 text-white placeholder-white/70 border border-white/30 focus:outline-none focus:border-white/60"
            disabled={isSearching}
          />
          <button
            onClick={fetchRelationships}
            disabled={wsStatus !== 'connected' || isSearching}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-500 disabled:cursor-not-allowed transition-colors"
          >
            {isSearching ? 'Searching...' : 'Search'}
          </button>
        </div>
      </div>
    </div>

    {/* WebSocket Status Indicator */}
    <div className="absolute top-4 right-4 z-10">
      <div className={`px-3 py-2 rounded-full text-sm font-medium ${
        wsStatus === 'connected' ? 'bg-green-500 text-white' :
        wsStatus === 'loading' ? 'bg-yellow-500 text-black' :
        'bg-red-500 text-white'
      }`}>
        {wsStatus === 'connected' ? '🟢 Connected' :
         wsStatus === 'loading' ? '🟡 Connecting...' :
         '🔴 Disconnected'}
      </div>
    </div>

    {/* Searching Indicator - Bottom Left Corner */}
    {isSearching && (
      <div className="absolute bottom-4 left-4 z-10 bg-blue-600/90 backdrop-blur-md rounded-lg p-3 flex items-center gap-3">
        <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent"></div>
        <span className="text-white font-medium">Fetching relationships...</span>
      </div>
    )}
  
    <ReactFlow
    nodes={nodes}
    edges={edges}
    onNodesChange={onNodesChange}
    onEdgesChange={onEdgesChange}
    onEdgeMouseEnter={(event, edge) => setHoveredEdge(edge.id)}
    onEdgeMouseLeave={() => setHoveredEdge(null)}
    nodeTypes={nodeTypes}
    fitView
    fitViewOptions={{
      padding: 0.2,
      minZoom: 0.1,
      maxZoom: 1.5,
    }}
    attributionPosition="bottom-left"
    defaultEdgeOptions={{
      type: 'smoothstep',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { 
      strokeWidth: 3,
      strokeOpacity: 0.7,
      strokeDasharray: '5,5'
      },
      animated: true,
    }}
    snapToGrid={false}
    snapGrid={[20, 20]}
    nodesDraggable={true}
    nodesConnectable={true}
    elementsSelectable={true}
    >
    <Background color="#ffffff" gap={20} size={1} variant={BackgroundVariant.Dots} />
    <Controls position="bottom-left" />
    <MiniMap 
      position="bottom-right"
      nodeColor={(node: Node) => (node.style?.background as string) || '#1976d2'}
      maskColor="rgba(255, 255, 255, 0.2)"
    />
    </ReactFlow>
  </div>
  );
}
