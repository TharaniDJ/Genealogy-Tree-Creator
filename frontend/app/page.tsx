'use client';
import React, { useState, useCallback, useEffect, useRef } from 'react';
import ReactFlow, {
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  Background,
  MarkerType,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { NodeData, GenerationInfo, Marriage, PersonData, GraphNode, GraphEdge } from '@/lib/types';
import EntityNode from '@/components/entity-node';
import ConnectionNode from '@/components/connection-node';

import { connectWebSocket } from './_utils/ws-con';
import { processRelationships } from './_utils/people';
import { useGenericGraph } from '@/hooks/use-generic-graph';


const nodeTypes = {
  entity: EntityNode,
  connection: ConnectionNode,
};

export default function KnowledgeGraph() {
  
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);
  const [wsStatus, setWsStatus] = useState<'disconnected' | 'connected' | 'loading'>('disconnected');
  const [isSearching, setIsSearching] = useState(false);
  const [searchQuery, setSearchQuery] = useState('Albert Einstein');
  const [relationships, setRelationships] = useState<any[]>([]);
  const [personalDetails, setPersonalDetails] = useState<Record<string, PersonData>>({});
  const wsRef = useRef<WebSocket | null>(null);
  
  // Use the new generic graph builder
  const { 
    buildGraphFromBackend, 
    addEntityNode, 
    addConnectionNode, 
    addEdge, 
    updateEdgesForHover 
  } = useGenericGraph();
  
  // Legacy tracking for backward compatibility with existing family logic
  const generationData = useRef<Record<string, GenerationInfo>>({});
  const generationCounts = useRef<Record<number, number>>({});
  const nodeConnections = useRef<Record<string, number>>({});
  const marriages = useRef<Record<string, Marriage>>({});

  // Helper function to get person data by name
  const getPersonData = useCallback((name: string): PersonData | undefined => {
    if (personalDetails[name]) {
      return personalDetails[name];
    }   
    return undefined;
  }, [personalDetails]);

  // Update edges when hover state changes
  useEffect(() => {
    const updatedEdges = updateEdgesForHover(edges, hoveredEdge);
    if (JSON.stringify(updatedEdges) !== JSON.stringify(edges)) {
      setEdges(updatedEdges);
    }
  }, [hoveredEdge, updateEdgesForHover, edges, setEdges]);

  // Function to add family members using the generic graph builder
  const addFamilyMember = useCallback((
    personId: string, 
    personData: PersonData, 
    generation: number
  ) => {
    const entityNode = addEntityNode(
      personId,
      personData.name,
      'person',
      {
        entityType: 'person',
        name: personData.name,
        birthYear: personData.birthYear,
        deathYear: personData.deathYear,
        image: personData.image,
        description: `Born: ${personData.birthYear}${personData.deathYear ? `, Died: ${personData.deathYear}` : ''}`,
        generation
      },
      generation
    );
    
    setNodes(prevNodes => {
      const exists = prevNodes.find(n => n.id === personId);
      if (!exists) {
        return [...prevNodes, entityNode];
      }
      return prevNodes;
    });
    
    return entityNode;
  }, [addEntityNode, setNodes]);

  // Function to add marriage connection
  const addMarriageConnection = useCallback((
    marriageId: string,
    parentA: string,
    parentB: string | undefined,
    generation: number
  ) => {
    const marriageNode = addConnectionNode(
      marriageId,
      'marriage',
      generation,
      'Marriage',
      { type: 'marriage' }
    );
    
    setNodes(prevNodes => {
      const exists = prevNodes.find(n => n.id === marriageId);
      if (!exists) {
        return [...prevNodes, marriageNode];
      }
      return prevNodes;
    });

    // Add edges from parents to marriage
    const newEdges: Edge[] = [];
    
    const edgeA = addEdge(parentA, marriageId, 'marriage', '', { gender: 'parent' });
    newEdges.push(edgeA);
    
    if (parentB) {
      const edgeB = addEdge(parentB, marriageId, 'marriage', '', { gender: 'parent' });
      newEdges.push(edgeB);
    }
    
    setEdges(prevEdges => {
      const existingIds = new Set(prevEdges.map(e => e.id));
      const filteredNewEdges = newEdges.filter(e => !existingIds.has(e.id));
      return [...prevEdges, ...filteredNewEdges];
    });
    
    return marriageNode;
  }, [addConnectionNode, addEdge, setNodes, setEdges]);

  // Function to add parent-child relationship
  const addParentChildRelation = useCallback((
    marriageId: string,
    childId: string
  ) => {
    const edge = addEdge(marriageId, childId, 'parent-child', 'Child');
    
    setEdges(prevEdges => {
      const exists = prevEdges.find(e => e.id === edge.id);
      if (!exists) {
        return [...prevEdges, edge];
      }
      return prevEdges;
    });
  }, [addEdge, setEdges]);

  // Wrapper function for backward compatibility with existing family logic
  const addFamilyRelationWrapper = useCallback((
    parent: string, 
    parentGender: 'father' | 'mother', 
    child: string, 
    parentGen: number, 
    childGen: number, 
    spouse?: string
  ) => {
    const marriageId = spouse ? `${parent}-${spouse}-marriage` : `${parent}-single-marriage`;
    
    // Add parent
    const parentData = getPersonData(parent);
    if (parentData) {
      addFamilyMember(parent, parentData, parentGen);
    }
    
    // Add spouse if exists
    if (spouse) {
      const spouseData = getPersonData(spouse);
      if (spouseData) {
        addFamilyMember(spouse, spouseData, parentGen);
      }
    }
    
    // Add child
    const childData = getPersonData(child);
    if (childData) {
      addFamilyMember(child, childData, childGen);
    }
    
    // Add marriage connection
    addMarriageConnection(marriageId, parent, spouse, parentGen + 0.5);
    
    // Add parent-child relationship
    addParentChildRelation(marriageId, child);
    
    // Update legacy tracking for backward compatibility
    if (!marriages.current[marriageId]) {
      marriages.current[marriageId] = {
        id: marriageId,
        father: parentGender === 'father' ? parent : (spouse || ''),
        mother: parentGender === 'mother' ? parent : (spouse || ''),
        children: [child],
        generation: parentGen
      };
    } else {
      if (!marriages.current[marriageId].children.includes(child)) {
        marriages.current[marriageId].children.push(child);
      }
    }
  }, [getPersonData, addFamilyMember, addMarriageConnection, addParentChildRelation]);

  // WebSocket connection setup
  useEffect(() => {
    const cleanup = connectWebSocket({
      setWsStatus,
      wsRef,
      setRelationships,
      setPersonalDetails,
      setIsSearching
    });

    return cleanup;
  }, []);

  // Function to start fetching relationships
  const fetchRelationships = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      setIsSearching(true);
      setRelationships([]);
      setPersonalDetails({}); // Clear previous personal details
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
    
    const handleProcessRelationships = () => {
      const result = processRelationships({
        relationships,
        personalDetails,
        searchQuery,
        addFamilyRelationWrapper,
      });
      
      // If processing was not successful (missing personal details), don't continue
      if (!result) {
        return;
      }
    };
    
    // Small delay to ensure UI is ready
    const timer = setTimeout(handleProcessRelationships, 500);
    return () => clearTimeout(timer);
  }, [relationships, personalDetails, addFamilyRelationWrapper, searchQuery]); // Added personalDetails dependency

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
  
    </ReactFlow>
  </div>
  );
}
