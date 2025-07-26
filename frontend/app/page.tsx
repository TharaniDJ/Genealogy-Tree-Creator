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
  
  // Generation tracking for hierarchical layout
  const generationData = useRef<Record<string, GenerationInfo>>({});
  const generationCounts = useRef<Record<number, number>>({});
  const nodeConnections = useRef<Record<string, number>>({});
  const marriages = useRef<Record<string, Marriage>>({});

  // Einstein family personal data
  const getPersonData = useCallback((name: string): PersonData | undefined => {
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
      "Abraham Einstein": {
        name: "Abraham Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1808,
        deathYear: 1868
      },
      "Julius Koch": {
        name: "Julius Koch",
        image: "/placeholder-user.jpg",
        birthYear: 1816,
        deathYear: 1895
      },
      "Jette Bernheimer": {
        name: "Jette Bernheimer",
        image: "/placeholder-user.jpg",
        birthYear: 1825,
        deathYear: 1886
      },
      "Rupert Einstein": {
        name: "Rupert Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1759,
        deathYear: 1834
      },
      "Rebecca Einstein": {
        name: "Rebecca Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1770,
        deathYear: 1853
      },
      "Frieda Knecht": {
        name: "Frieda Knecht",
        image: "/placeholder-user.jpg",
        birthYear: 1895,
        deathYear: 1958
      },
      "Elizabeth Roboz": {
        name: "Elizabeth Roboz",
        image: "/placeholder-user.jpg",
        birthYear: 1904,
        deathYear: 1995
      },
      "Bernhard Caesar Einstein": {
        name: "Bernhard Caesar Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1930,
        deathYear: 2008
      },
      "Klaus Martin Einstein": {
        name: "Klaus Martin Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1932,
        deathYear: 1938
      },
      "David Einstein": {
        name: "David Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1939
      },
      "Evelyn Einstein": {
        name: "Evelyn Einstein",
        image: "/placeholder-user.jpg",
        birthYear: 1941,
        deathYear: 2011
      }
    };
    
    return personDataMap[name];
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

  // Build Einstein family tree
  useEffect(() => {
  const buildFamilyTree = async () => {
    generationData.current = {};
    generationCounts.current = {};
    nodeConnections.current = {};
    marriages.current = {};
    setNodes([]);
    setEdges([]);

    // Einstein family relationships with marriage handling
    const familyRelations = [
    
    () => addFamilyRelation("Abraham Einstein", "father", "Hermann Einstein", 1, 2),
    () => addFamilyRelation("Julius Koch", "father", "Pauline Koch", 1, 2, "Jette Bernheimer"),
    () => addFamilyRelation("Albert Einstein", "father", "Hans Albert Einstein", 3, 4, "Mileva Marić"),
    () => addFamilyRelation("Albert Einstein", "father", "Eduard Einstein", 3, 4, "Mileva Marić"),
    () => addFamilyRelation("Albert Einstein", "father", "Lieserl Einstein", 3, 4, "Mileva Marić"),
    () => addFamilyRelation("Rupert Einstein", "father", "Abraham Einstein", 0, 1, "Rebecca Einstein"),
    () => addFamilyRelation("Hans Albert Einstein", "father", "Bernhard Caesar Einstein", 4, 5, "Frieda Knecht"),
    () => addFamilyRelation("Hans Albert Einstein", "father", "Klaus Martin Einstein", 4, 5, "Frieda Knecht"),
    () => addFamilyRelation("Hermann Einstein", "father", "Albert Einstein", 2, 3, "Pauline Koch"),
    () => addFamilyRelation("Hans Albert Einstein", "father", "David Einstein", 4, 5, "Elizabeth Roboz"),
    () => addFamilyRelation("Hans Albert Einstein", "father", "Evelyn Einstein", 4, 5, "Elizabeth Roboz"),
    ];


    for (let i = 0; i < familyRelations.length; i++) {
    setTimeout(familyRelations[i], i * 500);
    }
  };

  const timer = setTimeout(buildFamilyTree, 1000);
  return () => clearTimeout(timer);
  }, [addFamilyRelation]);

 



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
