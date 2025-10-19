import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
  ReactFlowProvider,
  MarkerType,
  useReactFlow,
  getNodesBounds,
  getViewportForBounds,
} from 'reactflow';
import 'reactflow/dist/style.css';
import PersonNode from './PersonNode';
import MarriageNode from './MarriageNode';
import { toPng, toJpeg } from 'html-to-image';
import jsPDF from 'jspdf';

const nodeTypes = {
  person: PersonNode,
  marriage: MarriageNode,
};

// Family line colors for visual distinction
const FAMILY_COLORS = [
  '#3b82f6', '#ef4444', '#10b981', '#f59e0b',
  '#8b5cf6', '#06b6d4', '#f97316', '#84cc16',
];

// Edge styles for different relationship types
const RELATIONSHIP_STYLES = {
  'child of': {
    stroke: '#1f2937', 
    strokeWidth: 3, 
    strokeDasharray: undefined,
    label: '' 
  },
  'adopted by': {
    stroke: '#7c3aed', 
    strokeWidth: 3, 
    strokeDasharray: '8,4',
    label: 'adopted' 
  },
  'spouse of': { 
    stroke: '#ec4899', 
    strokeWidth: 2, 
    strokeDasharray: undefined,
    label: '' 
  },
};

import { WebSocketMessage, PersonDetails, Relationship } from '@/types/websocket';

interface ContextMenu {
  show: boolean;
  x: number;
  y: number;
  nodeId: string;
  nodeType: 'person' | 'marriage';
}

interface GenealogyTreeProps {
  websocketData?: WebSocketMessage[];
  onExpandNode?: (personName: string, depth: number) => void;
  onExpandNodeByQid?: (qid: string, depth: number, entityName?: string) => void;
  onClassifyRelationships?: (relationships: { entity1: string; entity2: string; relationship: string }[]) => void;
  expandDepth?: number;
  triggerFitView?: number;
  onSaveGraph?: () => void;
  onLoadGraph?: () => void;
  onClearGraph?: () => void;
  graphDataLength?: number;
}

function GenealogyTreeInternal({ 
  websocketData = [], 
  onExpandNodeByQid,
  onClassifyRelationships,
  expandDepth = 2,
  triggerFitView = 0,
  onSaveGraph,
  onLoadGraph,
  onClearGraph,
  graphDataLength = 0
}: GenealogyTreeProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [personDetails, setPersonDetails] = useState<Map<string, PersonDetails>>(new Map());
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');
  // WebSocket handling is managed by parent; no local socket state required here
  const [contextMenu, setContextMenu] = useState<ContextMenu>({
    show: false,
    x: 0,
    y: 0,
    nodeId: '',
    nodeType: 'person'
  });
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [expandingNode, setExpandingNode] = useState<string | null>(null);
  const [isClassifying, setIsClassifying] = useState(false);
  const [showClassificationButton, setShowClassificationButton] = useState(false);
  const [classifiedRelationships, setClassifiedRelationships] = useState<Map<string, string>>(new Map());
  // Collapsible UI state for status panel and toolbar
  const [isStatusCollapsed, setIsStatusCollapsed] = useState(true);
  const [isToolbarCollapsed, setIsToolbarCollapsed] = useState(true);
  // When user explicitly expands, keep it open even if idle until they collapse
  const [statusPinnedOpen, setStatusPinnedOpen] = useState(false);
  const [toolbarPinnedOpen, setToolbarPinnedOpen] = useState(false);
  
  // Get ReactFlow instance for fitView
  const { fitView, getNodes } = useReactFlow();
  const reactFlowRef = useRef<HTMLDivElement>(null);

  // Trigger fitView when triggerFitView changes (e.g., after loading a graph)
  useEffect(() => {
    if (triggerFitView > 0 && nodes.length > 0) {
      setTimeout(() => {
        fitView({ padding: 0.2, duration: 800 });
      }, 100);
    }
  }, [triggerFitView, nodes.length, fitView]);

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onNodeContextMenu = useCallback((event: React.MouseEvent, node: Node) => {
    event.preventDefault();
    setContextMenu({
      show: true,
      x: event.clientX,
      y: event.clientY,
      nodeId: node.id,
      nodeType: node.type as 'person' | 'marriage'
    });
  }, []);

  useEffect(() => {
    const handleClick = () => setContextMenu(prev => ({ ...prev, show: false }));
    document.addEventListener('click', handleClick);
    return () => document.removeEventListener('click', handleClick);
  }, []);

useEffect(() => {
  if (websocketData.length === 0) return;
  
  const latestMessage = websocketData[websocketData.length - 1];
  
  if (latestMessage.type === 'classified_relationships') {
    console.log('Received classified relationships:', latestMessage.data);
    
    const classified: { entity1: string; entity2: string; classification?: string }[] = latestMessage.data.relationships;
    const classificationMap = new Map<string, string>();
    
    // Build classification map using entity names
    classified.forEach((rel) => {
      if (rel.classification) {
        const key1 = `${rel.entity1}-${rel.entity2}`;
        const key2 = `${rel.entity2}-${rel.entity1}`;
        classificationMap.set(key1, rel.classification);
        classificationMap.set(key2, rel.classification);
        
        console.log(`Classified: ${key1} = ${rel.classification}`);
      }
    });
    
    // Capture current nodes snapshot
    const currentNodes = nodes;
    
    // Build node ID map - map entity names to node IDs
    const nodeIdMap = new Map<string, string>();
    currentNodes.forEach(node => {
      if (node.data.entity) {
        nodeIdMap.set(node.data.entity, node.id);
      }
    });
    
    console.log('Classification map size:', classificationMap.size);
    console.log('Node ID map size:', nodeIdMap.size);
    setClassifiedRelationships(classificationMap);
    setIsClassifying(false);
    setStatus('Classification complete! Relationships updated.');
    
    // Update edges with new classifications
    setEdges(currentEdges => {
      console.log('Updating edges, current count:', currentEdges.length);
      
      return currentEdges.map(edge => {
        // Only process parent-child edges
        if (edge.id.includes('parent-child')) {
          console.log(`\nChecking edge: ${edge.id}`);
          console.log(`  Source ID: ${edge.source}, Target ID: ${edge.target}`);
          
          // Get entity names from node IDs using captured snapshot
          const sourceNode = currentNodes.find(n => n.id === edge.source);
          const targetNode = currentNodes.find(n => n.id === edge.target);
          
          if (sourceNode && targetNode) {
            const parentEntity = sourceNode.data.entity;
            const childEntity = targetNode.data.entity;
            
            console.log(`  Parent: ${parentEntity}, Child: ${childEntity}`);
            
            // Check classification
            const key1 = `${childEntity}-${parentEntity}`;
            const key2 = `${parentEntity}-${childEntity}`;
            
            const classification = classificationMap.get(key1) || classificationMap.get(key2);
            
            console.log(`  Classification: ${classification || 'none'}`);
            
            if (classification === 'ADOPTIVE') {
              console.log(`  ✓✓✓ UPDATING to ADOPTIVE style!`);
              return {
                ...edge,
                style: {
                  stroke: '#7c3aed',
                  strokeWidth: 3,
                  strokeDasharray: '8,4',
                },
                label: 'adopted',
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                  color: '#7c3aed',
                },
              };
            }
          } else {
            console.log(`  ⚠️ Could not find nodes for edge`);
          }
        }
        return edge;
      });
    });
    
    setTimeout(() => setStatus(''), 3000);
  }
// eslint-disable-next-line react-hooks/exhaustive-deps
}, [websocketData, setEdges]); // Intentionally excluding 'nodes' to prevent infinite loop; using snapshot inside
  useEffect(() => {
    if (relationships.length > 0 && personDetails.size > 0) {
      setShowClassificationButton(true);
    }
  }, [relationships, personDetails]);

  // Update handleClassifyRelationships:
const handleClassifyRelationships = useCallback(() => {
  if (isClassifying || !onClassifyRelationships) {
    console.log('Cannot classify:', { isClassifying, hasCallback: !!onClassifyRelationships });
    return;
  }

  setIsClassifying(true);
  setStatus('Classifying relationships...');

  const relationshipsToClassify = relationships
    .filter(rel => 
      rel.relationship.includes('child of') || 
      rel.relationship.includes('parent of')
    )
    .map(rel => ({
      entity1: rel.entity1,
      entity2: rel.entity2,
      relationship: rel.relationship
    }));

  console.log('Sending classification request:', {
    count: relationshipsToClassify.length,
    sample: relationshipsToClassify.slice(0, 2)
  });

  // Use the callback passed from parent
  onClassifyRelationships(relationshipsToClassify);
}, [relationships, isClassifying, onClassifyRelationships]);

  
  const getNodeById = useCallback((nodeId: string) => {
    return nodes.find(node => node.id === nodeId);
  }, [nodes]);

  type MarriageRecord = { spouse1: string; spouse2: string; children: string[] };
  const assignFamilyColors = useCallback((marriages: Map<string, MarriageRecord>, parentChildRels: Relationship[]) => {
    const familyColors = new Map<string, string>();
    
    const getAncestors = (person: string, visited: Set<string> = new Set()): string[] => {
      if (visited.has(person)) return [];
      visited.add(person);
      
      const ancestors: string[] = [];
      parentChildRels.forEach(rel => {
        if ((rel.relationship === 'biological child of' || 
             rel.relationship === 'adopted child of' || 
             rel.relationship === 'child of') && 
            rel.entity1 === person) {
          ancestors.push(rel.entity2);
          ancestors.push(...getAncestors(rel.entity2, visited));
        }
      });
      return [...new Set(ancestors)];
    };

    const assignLineageColor = (person: string, color: string) => {
      if (familyColors.has(person)) return;
      
      familyColors.set(person, color);
      const ancestors = getAncestors(person);
      ancestors.forEach(ancestor => {
        if (!familyColors.has(ancestor)) {
          familyColors.set(ancestor, color);
        }
      });
    };

    const findAvailableColor = (conflictingFamilies: string[]): string => {
      const conflictingColors = new Set(
        conflictingFamilies.map(person => familyColors.get(person)).filter(Boolean)
      );
      
      for (const color of FAMILY_COLORS) {
        if (!conflictingColors.has(color)) {
          return color;
        }
      }
      
      return FAMILY_COLORS[Math.floor(Math.random() * FAMILY_COLORS.length)];
    };

    Array.from(marriages.values()).forEach(marriage => {
      const spouse1 = marriage.spouse1;
      const spouse2 = marriage.spouse2;
      
      const spouse1Ancestors = getAncestors(spouse1);
      const spouse2Ancestors = getAncestors(spouse2);
      
      if (!familyColors.has(spouse1)) {
        const conflictingFamilies = [spouse2, ...spouse2Ancestors];
        const spouse1Color = findAvailableColor(conflictingFamilies);
        assignLineageColor(spouse1, spouse1Color);
      }
      
      if (!familyColors.has(spouse2)) {
        const conflictingFamilies = [spouse1, ...spouse1Ancestors, ...Array.from(familyColors.keys())];
        const spouse2Color = findAvailableColor(conflictingFamilies);
        assignLineageColor(spouse2, spouse2Color);
      }
    });

    Array.from(parentChildRels).forEach(rel => {
      [rel.entity1, rel.entity2].forEach(person => {
        if (!familyColors.has(person)) {
          const availableColor = findAvailableColor(Array.from(familyColors.keys()));
          assignLineageColor(person, availableColor);
        }
      });
    });

    return familyColors;
  }, []);

  useEffect(() => {
    if (websocketData.length === 0) return;

    const latestMessage = websocketData[websocketData.length - 1];
    
    if (latestMessage.type === 'status') {
      const message = latestMessage.data.message;
      
      if (message.includes('Error') || message.includes('not found') || message.includes('Connection error')) {
        if (expandingNode) {
          setExpandingNode(null);
        }
        
        setTimeout(() => {
          setStatus('');
          setProgress(0);
        }, 5000);
      }
    }
  }, [websocketData, expandingNode]);

  // Auto manage collapse/expand based on activity
  useEffect(() => {
    // Determine if there's an active event worth surfacing
    const hasActiveProgress = progress > 0 && progress < 100;
    const hasActiveStatus = Boolean(status && !/complete/i.test(status));
    const eventActive = isClassifying || Boolean(expandingNode) || hasActiveProgress || hasActiveStatus;

    if (eventActive) {
      // Auto expand during activity (unless user explicitly collapsed and pinned closed; we don't pin close here, so expand)
      setIsStatusCollapsed(false);
      setIsToolbarCollapsed(false);
    } else {
      // Idle -> collapse after a short delay unless pinned open by user
      const t = setTimeout(() => {
        if (!statusPinnedOpen) setIsStatusCollapsed(true);
        if (!toolbarPinnedOpen) setIsToolbarCollapsed(true);
      }, 1200);
      return () => clearTimeout(t);
    }
  }, [isClassifying, expandingNode, progress, status, statusPinnedOpen, toolbarPinnedOpen]);

  const handleExpandNode = useCallback((nodeId: string) => {
    const node = getNodeById(nodeId);
    if (node && node.data.qid && onExpandNodeByQid) {
      const qid = node.data.qid;
      const entityName = node.data.entity;

      if (qid === 'temp' || qid === 'unknown' || !qid.startsWith('Q')) {
        setStatus(`Cannot expand ${entityName}: No valid Wikipedia/Wikidata entry available`);
        setTimeout(() => setStatus(''), 3000);
        return;
      }

      if (expandingNode === nodeId) {
        return;
      }

      setExpandingNode(nodeId);

      setTimeout(() => {
        if (expandingNode === nodeId) {
          setExpandingNode(null);
          setStatus(`Expansion timeout for ${entityName}`);
          setProgress(0);
        }
      }, 30000);

      onExpandNodeByQid(qid, expandDepth, entityName);
      setExpandedNodes(prev => new Set([...prev, nodeId]));
    }
    setContextMenu(prev => ({ ...prev, show: false }));
  }, [getNodeById, onExpandNodeByQid, expandDepth, expandingNode]);

  const handleDeleteNode = useCallback((nodeId: string) => {
    const nodeToDelete = nodes.find(node => node.id === nodeId);
    if (!nodeToDelete) return;

    let finalNodes = [...nodes];
    let finalEdges = [...edges];

    if (nodeToDelete.type === 'person') {
      finalNodes = finalNodes.filter(node => node.id !== nodeId);
      finalEdges = finalEdges.filter(edge => 
        edge.source !== nodeId && edge.target !== nodeId
      );

      const marriageNodes = nodes.filter(node => 
        node.type === 'marriage' && 
        (node.data.spouse1 === nodeId || node.data.spouse2 === nodeId)
      );

      marriageNodes.forEach(marriageNode => {
        finalNodes = finalNodes.filter(node => node.id !== marriageNode.id);
        finalEdges = finalEdges.filter(edge => 
          edge.source !== marriageNode.id && edge.target !== marriageNode.id
        );

        const remainingSpouseId = marriageNode.data.spouse1 === nodeId ? 
          marriageNode.data.spouse2 : marriageNode.data.spouse1;
        
        const remainingSpouseExists = finalNodes.some(node => node.id === remainingSpouseId);
        
        if (remainingSpouseExists) {
          const childEdges = edges.filter(edge => edge.source === marriageNode.id);
          
          childEdges.forEach(childEdge => {
            const childExists = finalNodes.some(node => node.id === childEdge.target);
            
            if (childExists) {
              const newEdge = {
                id: `single-parent-${remainingSpouseId}-${childEdge.target}`,
                source: remainingSpouseId,
                target: childEdge.target,
                type: 'smoothstep',
                style: {
                  stroke: '#6b7280',
                  strokeWidth: 2,
                  strokeDasharray: '5,5',
                },
                markerEnd: {
                  type: MarkerType.ArrowClosed,
                  color: '#6b7280',
                },
              };
              finalEdges.push(newEdge);
            }
          });
        }
      });
    } 
    else if (nodeToDelete.type === 'marriage') {
      finalNodes = finalNodes.filter(node => node.id !== nodeId);
      finalEdges = finalEdges.filter(edge => 
        edge.source !== nodeId && edge.target !== nodeId
      );
    }

    setNodes(finalNodes);
    setEdges(finalEdges);

    setExpandedNodes(prev => {
      const newSet = new Set(prev);
      newSet.delete(nodeId);
      return newSet;
    });

    setContextMenu(prev => ({ ...prev, show: false }));
  }, [nodes, edges, setNodes, setEdges]);

  const handleAddSpouse = useCallback((nodeId: string) => {
    const node = getNodeById(nodeId);
    if (!node || node.type !== 'person') return;

    const spouseName = prompt('Enter spouse name:', 'New Spouse');
    if (!spouseName || spouseName.trim() === '') {
      setContextMenu(prev => ({ ...prev, show: false }));
      return;
    }

    const spouseId = `${nodeId}-spouse-${Date.now()}`;
    const marriageId = `${nodeId}-${spouseId}-marriage`;

    const spouseX = node.position.x + 350;
    const spouseY = node.position.y;
    const marriageX = node.position.x + 175;
    const marriageY = node.position.y + 200;

    const newSpouseNode: Node = {
      id: spouseId,
      type: 'person',
      position: { x: spouseX, y: spouseY },
      data: {
        label: spouseName.trim(),
        entity: spouseName.trim(),
        qid: 'temp',
        nodeType: 'entity' as const,
        isUserAdded: true,
      },
    };

    const newMarriageNode: Node = {
      id: marriageId,
      type: 'marriage',
      position: { x: marriageX, y: marriageY },
      data: {
        label: '♥',
        spouse1: nodeId,
        spouse2: spouseId,
        nodeType: 'marriage' as const,
        isUserAdded: true,
      },
    };

    const newEdges: Edge[] = [
      {
        id: `${nodeId}-${marriageId}`,
        source: nodeId,
        target: marriageId,
        type: 'straight',
        style: { stroke: '#ec4899', strokeWidth: 2 },
      },
      {
        id: `${spouseId}-${marriageId}`,
        source: spouseId,
        target: marriageId,
        type: 'straight',
        style: { stroke: '#ec4899', strokeWidth: 2 },
      }
    ];

    setNodes([...nodes, newSpouseNode, newMarriageNode]);
    setEdges([...edges, ...newEdges]);
    setContextMenu(prev => ({ ...prev, show: false }));
  }, [getNodeById, nodes, edges, setNodes, setEdges]);

  const handleAddChild = useCallback((nodeId: string) => {
    const node = getNodeById(nodeId);
    if (!node) return;

    const childName = prompt('Enter child name:', 'New Child');
    if (!childName || childName.trim() === '') {
      setContextMenu(prev => ({ ...prev, show: false }));
      return;
    }

    const relationshipType = prompt(
      'Enter relationship type:\n' +
      '1. biological (default)\n' +
      '2. adopted\n' +
      '3. other',
      '1'
    );

    let relType = 'child of';
    if (relationshipType === '2') relType = 'adopted by';
    else if (relationshipType === '3') relType = 'child of';

    const childId = `${nodeId}-child-${Date.now()}`;
    let childX = node.position.x;
    let childY = node.position.y + 350;
    let sourceId = nodeId;

    const styleConfig = RELATIONSHIP_STYLES[relType as keyof typeof RELATIONSHIP_STYLES] || RELATIONSHIP_STYLES['child of'];

    const edgeStyle = {
      stroke: styleConfig?.stroke || '#1f2937',
      strokeWidth: styleConfig?.strokeWidth || 3,
      strokeDasharray: styleConfig?.strokeDasharray,
    };

    if (node.type === 'marriage') {
      childX = node.position.x - 25;
      childY = node.position.y + 150;
      sourceId = nodeId;
      edgeStyle.strokeDasharray = undefined;
    } 
    else if (node.type === 'person') {
      const marriageNode = nodes.find(n => 
        n.type === 'marriage' && 
        (n.data.spouse1 === nodeId || n.data.spouse2 === nodeId)
      );

      if (marriageNode) {
        const fromMarriage = confirm(
          `Add child from marriage with ${marriageNode.data.spouse1 === nodeId ? 
            marriageNode.data.spouse2 : marriageNode.data.spouse1}?\n\n` +
          'Click OK for child from marriage, Cancel for single parent child.'
        );

        if (fromMarriage) {
          sourceId = marriageNode.id;
          childX = marriageNode.position.x - 25;
          childY = marriageNode.position.y + 150;
          edgeStyle.strokeDasharray = undefined;
        } else {
          sourceId = nodeId;
          childX = node.position.x - 25;
          childY = node.position.y + 350;
        }
      } else {
        sourceId = nodeId;
        childX = node.position.x - 25;
        childY = node.position.y + 350;
      }
    }

    const newChildNode: Node = {
      id: childId,
      type: 'person',
      position: { x: childX, y: childY },
      data: {
        label: childName.trim(),
        entity: childName.trim(),
        qid: 'temp',
        nodeType: 'entity' as const,
        isUserAdded: true,
        relationshipType: relType,
      },
    };

    const newEdge: Edge = {
      id: `parent-child-${sourceId}-${childId}`,
      source: sourceId,
      target: childId,
      type: 'smoothstep',
      style: edgeStyle,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: edgeStyle.stroke,
      },
      label: styleConfig?.label || (relType === 'adopted by' ? 'adopted' : ''),
    };

    setNodes([...nodes, newChildNode]);
    setEdges([...edges, newEdge]);
    setContextMenu(prev => ({ ...prev, show: false }));
  }, [getNodeById, nodes, edges, setNodes, setEdges]);

  useEffect(() => {
    if (expandingNode && websocketData.length > 0) {
      const hasNewData = websocketData.some(msg => 
        msg.type === 'status' && msg.data.message.includes('Complete')
      );
      if (hasNewData) {
        setExpandingNode(null);
      }
    }
  }, [websocketData, expandingNode]);

  const ContextMenuComponent = () => {
    if (!contextMenu.show) return null;

    const isExpanded = expandedNodes.has(contextMenu.nodeId);
    const isExpanding = expandingNode === contextMenu.nodeId;
    const node = getNodeById(contextMenu.nodeId);
    const hasWikipediaEntry = node?.data.qid && node.data.qid !== 'temp' && node.data.qid !== 'unknown';
    const isUserAdded = node?.data.isUserAdded;

    const userAddedCount = nodes.filter(n => n.data.isUserAdded).length;

    return (
      <div
        className="fixed backdrop-blur-xl bg-white/10 border border-white/20 rounded-xl shadow-2xl py-2 z-50"
        style={{
          left: contextMenu.x,
          top: contextMenu.y,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {contextMenu.nodeType === 'person' && (
          <>
            {!isUserAdded && (
              <button
                className={`w-full px-4 py-2 text-left hover:bg-white/10 flex items-center text-[#F5F7FA] ${
                  isExpanding ? 'opacity-50 cursor-not-allowed' : 
                  !hasWikipediaEntry ? 'opacity-75 text-[#9CA3B5]' : ''
                }`}
                onClick={() => handleExpandNode(contextMenu.nodeId)}
                disabled={isExpanding}
                title={
                  !hasWikipediaEntry ? 
                  'This person may not have a Wikipedia entry' : 
                  isExpanding ? 'Expansion in progress...' : 
                  'Expand family tree (includes adoptions)'
                }
              >
                <span className="mr-2">
                  {isExpanding ? '⏳' : hasWikipediaEntry ? '🔍' : '❓'}
                </span>
                {isExpanding ? 'Expanding...' : 
                 !hasWikipediaEntry ? 'Try Expand (Limited Info)' :
                 isExpanded ? 'Expand More' : 'Expand Family Tree'}
              </button>
            )}
            
            <button
              className="w-full px-4 py-2 text-left hover:bg-white/10 flex items-center text-[#F5F7FA]"
              onClick={() => handleAddSpouse(contextMenu.nodeId)}
            >
              <span className="mr-2">💑</span>
              Add Spouse
            </button>
          </>
        )}

        <button
          className="w-full px-4 py-2 text-left hover:bg-white/10 flex items-center text-[#F5F7FA]"
          onClick={() => handleAddChild(contextMenu.nodeId)}
        >
          <span className="mr-2">👶</span>
          {contextMenu.nodeType === 'marriage' ? 'Add Child (Both Parents)' : 'Add Child (Biological/Adopted)'}
        </button>

        {isUserAdded && userAddedCount > 0 && (
          <>
            <div className="border-t border-white/10 my-1"></div>
            
            <button
              className="w-full px-4 py-2 text-left hover:bg-red-500/20 text-red-400 flex items-center"
              onClick={() => handleDeleteNode(contextMenu.nodeId)}
              title="This will remove all manually added people and marriages from the tree"
            >
              <span className="mr-2">🗑️</span>
              <div className="text-left">
                <div className="font-medium">Clear All Added Nodes</div>
                <div className="text-xs text-red-400">
                  ({userAddedCount} item{userAddedCount !== 1 ? 's' : ''})
                </div>
              </div>
            </button>
          </>
        )}
      </div>
    );
  };

  // Clear graph when requested
  useEffect(() => {
    if (onClearGraph && graphDataLength === 0 && personDetails.size > 0) {
      // Clear all state
      setPersonDetails(new Map());
      setRelationships([]);
      setNodes([]);
      setEdges([]);
      setExpandedNodes(new Set());
      setClassifiedRelationships(new Map());
      setStatus('Graph cleared');
      setProgress(0);
      setTimeout(() => setStatus(''), 2000);
    }
  }, [graphDataLength, onClearGraph, personDetails.size, setNodes, setEdges]);
  useEffect(() => {
    if (websocketData.length === 0) return;

    const newPersonDetails = new Map<string, PersonDetails>();
    const newRelationships: Relationship[] = [];
    let latestStatus = '';
    let latestProgress = 0;

    websocketData.forEach((message) => {
      switch (message.type) {
        case 'status':
          const statusMessage = message.data.message;
          if (!statusMessage.toLowerCase().includes('disconnected') && 
              !statusMessage.toLowerCase().includes('client has disconnected')) {
            latestStatus = statusMessage;
            latestProgress = message.data.progress;
              }
          break;
        case 'personal_details':
          newPersonDetails.set(message.data.entity, message.data);
          break;
        case 'relationship':
          newRelationships.push(message.data);
          break;
      }
    });

    setPersonDetails(newPersonDetails);
    setRelationships(newRelationships);
    setStatus(latestStatus);
    setProgress(latestProgress);
  }, [websocketData]);

  useEffect(() => {
    if (personDetails.size === 0) return;

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    
    const PERSON_WIDTH = 200;
    const HORIZONTAL_SPACING = 300;
    const VERTICAL_SPACING = 350;
    const MARRIAGE_WIDTH = 60;
    const MARRIAGE_OFFSET_Y = 220;
    
    const marriageRelationships = relationships.filter(rel => 
      rel.relationship === 'spouse of' || 
      rel.relationship === 'married to' ||
      rel.relationship === 'spouse' ||
      rel.relationship === 'husband of' ||
      rel.relationship === 'wife of'
    );
    
    const parentChildRelationships = relationships.filter(rel => 
      rel.relationship === 'biological child of' ||
      rel.relationship === 'adopted child of' ||
      rel.relationship === 'child of' ||
      rel.relationship === 'parent of' ||
      rel.relationship === 'father of' ||
      rel.relationship === 'mother of'
    );

    const marriages = new Map<string, { spouse1: string; spouse2: string; children: string[] }>();
    const personToMarriages = new Map<string, string[]>();

    marriageRelationships.forEach(rel => {
      const [person1, person2] = [rel.entity1, rel.entity2].sort();
      const marriageId = `${person1}-${person2}-marriage`;
      
      if (!marriages.has(marriageId)) {
        marriages.set(marriageId, {
          spouse1: person1,
          spouse2: person2,
          children: []
        });
        
        if (!personToMarriages.has(person1)) personToMarriages.set(person1, []);
        if (!personToMarriages.has(person2)) personToMarriages.set(person2, []);
        personToMarriages.get(person1)!.push(marriageId);
        personToMarriages.get(person2)!.push(marriageId);
      }
    });

    const marriageChildren = new Map<string, string[]>();

    parentChildRelationships.forEach(rel => {
      let parent, child;
      
      if (rel.relationship === 'biological child of' || 
          rel.relationship === 'adopted child of' || 
          rel.relationship === 'child of') {
        parent = rel.entity2;
        child = rel.entity1;
      } else if (rel.relationship === 'parent of' || 
                 rel.relationship === 'father of' || 
                 rel.relationship === 'mother of') {
        parent = rel.entity1;
        child = rel.entity2;
      } else {
        return;
      }
      
      const parentMarriages = personToMarriages.get(parent) || [];
      let childAssigned = false;
      
      parentMarriages.forEach(marriageId => {
        const marriage = marriages.get(marriageId);
        if (marriage) {
          const otherSpouse = marriage.spouse1 === parent ? marriage.spouse2 : marriage.spouse1;
          
          const hasRelationshipWithOtherSpouse = parentChildRelationships.some(otherRel => {
            if (otherRel.relationship === 'biological child of' || 
                otherRel.relationship === 'adopted child of' || 
                otherRel.relationship === 'child of') {
              return otherRel.entity1 === child && otherRel.entity2 === otherSpouse;
            } else if (otherRel.relationship === 'parent of' || 
                       otherRel.relationship === 'father of' || 
                       otherRel.relationship === 'mother of') {
              return otherRel.entity1 === otherSpouse && otherRel.entity2 === child;
            }
            return false;
          });
          
          if (hasRelationshipWithOtherSpouse && !marriage.children.includes(child)) {
            marriage.children.push(child);
            childAssigned = true;
          }
        }
      });
      
      if (!childAssigned) {
        const singleParentKey = `single-parent-${parent}`;
        if (!marriageChildren.has(singleParentKey)) {
          marriageChildren.set(singleParentKey, []);
        }
        if (!marriageChildren.get(singleParentKey)!.includes(child)) {
          marriageChildren.get(singleParentKey)!.push(child);
        }
      }
    });

    const familyColors = assignFamilyColors(marriages, parentChildRelationships);

    const generations = new Map<string, number>();
    const visited = new Set<string>();
    
    const peopleWithParents = new Set<string>();
    parentChildRelationships.forEach(rel => {
      if (rel.relationship === 'biological child of' || 
          rel.relationship === 'adopted child of' || 
          rel.relationship === 'child of') {
        peopleWithParents.add(rel.entity1);
      } else if (rel.relationship === 'parent of') {
        peopleWithParents.add(rel.entity2);
      }
    });
    
    const rootCandidates = Array.from(personDetails.keys()).filter(person => 
      !peopleWithParents.has(person)
    );
    
        
    const rootPerson = rootCandidates.length > 0 ? rootCandidates[0] : Array.from(personDetails.keys())[0];
    
    const queue: { person: string; generation: number }[] = [{ person: rootPerson, generation: 0 }];
    generations.set(rootPerson, 0);
    
    while (queue.length > 0) {
      const { person, generation } = queue.shift()!;
      if (visited.has(person)) continue;
      visited.add(person);
      
      parentChildRelationships.forEach(rel => {
        if ((rel.relationship === 'biological child of' || 
             rel.relationship === 'adopted child of' || 
             rel.relationship === 'child of') && 
            rel.entity2 === person && !generations.has(rel.entity1)) {
          generations.set(rel.entity1, generation + 1);
          queue.push({ person: rel.entity1, generation: generation + 1 });
        } else if ((rel.relationship === 'biological child of' || 
                    rel.relationship === 'adopted child of' || 
                    rel.relationship === 'child of') && 
                   rel.entity1 === person && !generations.has(rel.entity2)) {
          generations.set(rel.entity2, Math.max(generation - 1, 0));
          queue.push({ person: rel.entity2, generation: Math.max(generation - 1, 0) });
        } else if (rel.relationship === 'parent of' && 
                   rel.entity1 === person && !generations.has(rel.entity2)) {
          generations.set(rel.entity2, generation + 1);
          queue.push({ person: rel.entity2, generation: generation + 1 });
        } else if (rel.relationship === 'parent of' && 
                   rel.entity2 === person && !generations.has(rel.entity1)) {
          generations.set(rel.entity1, Math.max(generation - 1, 0));
          queue.push({ person: rel.entity1, generation: Math.max(generation - 1, 0) });
        }
      });
    }

    marriageRelationships.forEach(rel => {
      const gen1 = generations.get(rel.entity1);
      const gen2 = generations.get(rel.entity2);
      
      if (gen1 !== undefined && gen2 === undefined) {
        generations.set(rel.entity2, gen1);
      } else if (gen2 !== undefined && gen1 === undefined) {
        generations.set(rel.entity1, gen2);
      } else if (gen1 !== undefined && gen2 !== undefined && gen1 !== gen2) {
        const targetGen = Math.min(gen1, gen2);
        generations.set(rel.entity1, targetGen);
        generations.set(rel.entity2, targetGen);
      }
    });

    Array.from(personDetails.keys()).forEach(person => {
      if (!generations.has(person)) {
        generations.set(person, 0);
      }
    });

    // Positioning algorithm
    const generationGroups = new Map<number, { 
      marriages: Array<{id: string, data: MarriageRecord}>, 
      singles: string[] 
    }>();

    const allGenerations = new Set(Array.from(generations.values()));
    const minGen = Math.min(...Array.from(allGenerations));
    const maxGen = Math.max(...Array.from(allGenerations));
    
    for (let gen = minGen; gen <= maxGen; gen++) {
      generationGroups.set(gen, { marriages: [], singles: [] });
    }

    Array.from(marriages.entries())
      .forEach(([marriageId, marriage]) => {
        const gen1 = generations.get(marriage.spouse1) || 0;
        const gen2 = generations.get(marriage.spouse2) || 0;
        const generation = Math.min(gen1, gen2);
        
        const group = generationGroups.get(generation);
        if (group && personDetails.has(marriage.spouse1) && personDetails.has(marriage.spouse2)) {
          group.marriages.push({
            id: marriageId,
            data: marriage
          });
        }
      });

    // Sort marriages within each generation by family color to group related families
    Array.from(generationGroups.values()).forEach(group => {
      group.marriages.sort((a, b) => {
        const colorA = familyColors.get(a.data.spouse1) || '';
        const colorB = familyColors.get(b.data.spouse1) || '';
        return colorA.localeCompare(colorB);
      });
    });

    // Group single people by generation
    const marriedPeople = new Set<string>();
    Array.from(marriages.values()).forEach(marriage => {
      marriedPeople.add(marriage.spouse1);
      marriedPeople.add(marriage.spouse2);
    });

    Array.from(personDetails.keys()).forEach(person => {
      if (!marriedPeople.has(person)) {
        const generation = generations.get(person) || 0;
        const group = generationGroups.get(generation);
        if (group) {
          group.singles.push(person);
        }
      }
    });

    // Create nodes with positioning
    const nodePositions = new Map<string, { x: number; y: number }>();
    
    Array.from(generationGroups.entries())
      .sort(([a], [b]) => a - b)
      .forEach(([generation, group]) => {
        const y = generation * VERTICAL_SPACING + 300;
        
        const marriageWidth = group.marriages.length * (HORIZONTAL_SPACING * 2 + MARRIAGE_WIDTH);
        const singleWidth = group.singles.length * HORIZONTAL_SPACING;
        const totalWidth = Math.max(marriageWidth + singleWidth, 400);
        
        let currentX = -totalWidth / 2;
        
        // Position marriages
        group.marriages.forEach(({ id: marriageId, data: marriage }) => {
          const spouse1Details = personDetails.get(marriage.spouse1);
          const spouse2Details = personDetails.get(marriage.spouse2);
          
          if (!spouse1Details && !spouse2Details) return;
          
          const marriageGroupWidth = HORIZONTAL_SPACING * 2 + MARRIAGE_WIDTH;
          const groupCenterX = currentX + marriageGroupWidth / 2;
          
          const spouse1X = groupCenterX - HORIZONTAL_SPACING / 2 - PERSON_WIDTH / 2;
          const spouse2X = groupCenterX + HORIZONTAL_SPACING / 2 - PERSON_WIDTH / 2;
          const marriageX = groupCenterX - MARRIAGE_WIDTH / 2;
          const marriageY = y + MARRIAGE_OFFSET_Y;
          
          nodePositions.set(marriage.spouse1, { x: spouse1X, y });
          nodePositions.set(marriage.spouse2, { x: spouse2X, y });
          nodePositions.set(marriageId, { x: marriageX, y: marriageY });
          
          // Create spouse nodes with family color information
          [marriage.spouse1, marriage.spouse2].forEach((person, index) => {
            const details = index === 0 ? spouse1Details : spouse2Details;
            const x = index === 0 ? spouse1X : spouse2X;
            
            newNodes.push({
              id: person,
              type: 'person',
              position: { x, y },
              data: {
                label: details?.entity || person,
                entity: details?.entity || person,
                qid: details?.qid || 'unknown',
                birth_year: details?.birth_year,
                death_year: details?.death_year,
                image_url: details?.image_url,
                nodeType: 'entity' as const,
                isExpanded: expandedNodes.has(person),
                familyColor: familyColors.get(person),
              },
            });
          });

          // Create marriage node
          newNodes.push({
            id: marriageId,
            type: 'marriage',
            position: { x: marriageX, y: marriageY },
            data: {
              label: '♥',
              spouse1: marriage.spouse1,
              spouse2: marriage.spouse2,
              nodeType: 'marriage' as const,
            },
          });

          // Connect spouses to marriage node
          newEdges.push({
            id: `${marriage.spouse1}-${marriageId}`,
            source: marriage.spouse1,
            target: marriageId,
            type: 'straight',
            style: { stroke: '#ec4899', strokeWidth: 2 },
          });

          newEdges.push({
            id: `${marriage.spouse2}-${marriageId}`,
            source: marriage.spouse2,
            target: marriageId,
            type: 'straight',
            style: { stroke: '#ec4899', strokeWidth: 2 },
          });

          currentX += marriageGroupWidth;
        });

        // Position single people
        group.singles.forEach(person => {
          const details = personDetails.get(person);
          if (!details) return;
          
          const x = currentX;
          nodePositions.set(person, { x, y });
          
          newNodes.push({
            id: person,
            type: 'person',
            position: { x, y },
            data: {
              label: details.entity,
              entity: details.entity,
              qid: details.qid,
              birth_year: details.birth_year,
              death_year: details.death_year,
              image_url: details.image_url,
              nodeType: 'entity' as const,
              isExpanded: expandedNodes.has(person),
              familyColor: familyColors.get(person),
            },
          });

          currentX += HORIZONTAL_SPACING;
        });
      });

    // Create parent-child relationships with enhanced adoption support
    // Create parent-child relationships with enhanced adoption support
parentChildRelationships.forEach((rel, index) => {
  let parent, child;
  
  if (rel.relationship === 'biological child of' || 
      rel.relationship === 'adopted child of' || 
      rel.relationship === 'child of') {
    parent = rel.entity2;
    child = rel.entity1;
  } else if (rel.relationship === 'parent of' || 
             rel.relationship === 'father of' || 
             rel.relationship === 'mother of') {
    parent = rel.entity1;
    child = rel.entity2;
  } else {
    return;
  }
  
  const hasParentNode = newNodes.some(n => n.id === parent);
  const hasChildNode = newNodes.some(n => n.id === child);
  
  if (!hasParentNode || !hasChildNode) return;
  
  // Check if parent is in a marriage with children
  let sourceId = parent;
  let isFromMarriage = false;
  const parentMarriages = personToMarriages.get(parent) || [];
  
  for (const marriageId of parentMarriages) {
    const marriage = marriages.get(marriageId);
    if (marriage && marriage.children.includes(child)) {
      sourceId = marriageId;
      isFromMarriage = true;
      break;
    }
  }
  
  // Check if this relationship has been classified as adoptive
  const classificationKey1 = `${parent}-${child}`;
  const classificationKey2 = `${child}-${parent}`;
  const isAdoptive = classifiedRelationships.get(classificationKey1) === 'ADOPTIVE' || 
                     classifiedRelationships.get(classificationKey2) === 'ADOPTIVE';
  
  // Get relationship style based on relationship type OR classification
  let styleConfig;
  if (isAdoptive) {
    styleConfig = RELATIONSHIP_STYLES['adopted by'];
  } else {
    styleConfig = RELATIONSHIP_STYLES[rel.relationship as keyof typeof RELATIONSHIP_STYLES] || 
                  RELATIONSHIP_STYLES['child of'];
  }
  
  const parentColor = isAdoptive ? '#7c3aed' : (familyColors.get(parent) || styleConfig.stroke);
  
  // Only create edge if we haven't already created one for this parent-child pair
  const existingEdge = newEdges.find(edge => 
    edge.source === sourceId && edge.target === child && edge.id.includes('parent-child')
  );
  
  if (!existingEdge) {
    newEdges.push({
      id: `parent-child-${parent}-${child}-${index}`,
      source: sourceId,
      target: child,
      type: 'smoothstep',
      style: {
        stroke: parentColor,
        strokeWidth: styleConfig.strokeWidth,
        strokeDasharray: styleConfig.strokeDasharray,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: parentColor,
      },
      label: isFromMarriage ? undefined : 
             (isAdoptive || rel.relationship === 'adopted child of' ? 'adopted' : 
              !isFromMarriage ? `${parent.split(' ')[0]}'s child` : undefined),
    });
  }
});
    
    console.log(`Generated tree with adoption support: ${newNodes.length} nodes, ${newEdges.length} edges`);
    console.log(`Marriages found: ${marriages.size}`);
    console.log('Family colors assigned:', Array.from(familyColors.entries()).slice(0, 5));

    setNodes(newNodes);
    setEdges(newEdges);
  }, [personDetails, relationships, setNodes, setEdges, expandedNodes, assignFamilyColors,classifiedRelationships]);

  return (
    <div ref={reactFlowRef} className="absolute inset-0 w-full h-full bg-[#0E0F19]">
      {/* Status toggle (collapsed) */}
      {isStatusCollapsed && (
        <button
          onClick={() => { setIsStatusCollapsed(false); setStatusPinnedOpen(true); }}
          className="absolute top-4 left-4 z-20 px-2 py-1 text-xs rounded-md bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10 shadow"
          title="Show status"
        >
          Status
        </button>
      )}

      {/* Horizontal Status Bar (collapsible) */}
      {!isStatusCollapsed && (
        <div className="absolute w-8/12 top-4 left-4 z-10 backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl shadow-lg">
          <div className="px-6 py-3 relative">
            {/* Collapse control */}
            <button
              onClick={() => { setIsStatusCollapsed(true); setStatusPinnedOpen(false); }}
              className="absolute top-2 right-2 text-xs px-2 py-1 rounded bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10"
              title="Hide status"
            >
              Hide
            </button>

            <div className="space-y-2">
              {/* First Row: Status Message - Full Width */}
              <div className="flex items-start space-x-2">
                {isClassifying && (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-[#8B7BFF]"></div>
                )}
                <span className="text-sm font-medium text-[#F5F7FA] flex-1 min-w-0 whitespace-pre-wrap break-words">
                  {isClassifying ? 'Classifying relationships...' :
                   expandingNode ? 'Expanding Family Tree...' :
                   status || 'Idle'}
                </span>
              </div>

              {/* Second Row: Statistics and Progress Bar */}
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 text-xs text-[#9CA3B5]">
                  <span>People: {personDetails.size}</span>
                  <span>Relationships: {relationships.length}</span>
                  <span>Expanded: {expandedNodes.size}</span>
                  <span>Depth: {expandDepth}</span>
                </div>

                {progress > 0 && (
                  <div className="flex items-center space-x-3">
                    <span className="text-sm font-medium text-[#9CA3B5]">{progress}%</span>
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
          className="absolute top-4 right-4 z-20 px-2 py-1 text-xs rounded-md bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10 shadow"
          title="Show tools"
        >
          Tools
        </button>
      )}

      {/* Floating Toolbar for Actions (collapsible) */}
      {!isToolbarCollapsed && (
      <div className="absolute top-4 right-4 z-10 flex items-center gap-2 backdrop-blur-xl bg-white/5 border border-white/10 rounded-xl p-2 shadow-lg shadow-[#6B72FF]/10">
        <button
          onClick={() => { setIsToolbarCollapsed(true); setToolbarPinnedOpen(false); }}
          className="px-2 py-1 text-xs rounded-md bg-white/10 hover:bg-white/20 text-[#F5F7FA] border border-white/10"
          title="Hide tools"
        >
          Hide
        </button>
        {showClassificationButton && !isClassifying && nodes.length > 0 && (
          <button
            onClick={handleClassifyRelationships}
            disabled={isClassifying}
            className="px-3 py-2 text-sm rounded-lg bg-gradient-to-r from-[#8B7BFF] to-[#6B72FF] text-white hover:from-[#9B8BFF] hover:to-[#7B82FF] transition-all shadow-lg shadow-[#8B7BFF]/30 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Classify biological vs adoptive relationships"
          >
            Classify Relations
          </button>
        )}
        
        <button
          onClick={onSaveGraph}
          disabled={!onSaveGraph || graphDataLength === 0}
          title="Save Graph"
          className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-green-600/80 text-[#9CA3B5] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg border border-white/10 hover:scale-105"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
          </svg>
        </button>
        
        <button
          onClick={onLoadGraph}
          disabled={!onLoadGraph}
          title="Load Saved Graph"
          className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-amber-600/80 text-[#9CA3B5] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg border border-white/10 hover:scale-105"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z" />
          </svg>
        </button>
        
        <button
          onClick={onClearGraph}
          disabled={!onClearGraph}
          title="Clear Tree Data"
          className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-red-600/80 text-[#9CA3B5] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-md hover:shadow-lg border border-white/10 hover:scale-105"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
        
        <div className="w-px h-6 bg-white/10 mx-1" />
        
        <button
          onClick={async () => {
            const domViewport = reactFlowRef.current?.querySelector('.react-flow__viewport') as HTMLElement;
            if (!domViewport) {
              console.error('Viewport not found');
              return;
            }

            setStatus('Preparing PNG export...');
            
            // Wait for all images to load
            const images = domViewport.querySelectorAll('img');
            await Promise.all(
              Array.from(images).map((img) => {
                if (img.complete) return Promise.resolve();
                return new Promise((resolve) => {
                  img.onload = resolve;
                  img.onerror = resolve;
                });
              })
            );

            const nodesBounds = getNodesBounds(getNodes());
            const rfViewport = getViewportForBounds(
              nodesBounds,
              nodesBounds.width,
              nodesBounds.height,
              0.5,
              2,
              0.2
            );

            try {
              const dataUrl = await toPng(domViewport, {
                backgroundColor: '#0E0F19',
                width: nodesBounds.width,
                height: nodesBounds.height,
                pixelRatio: 2,
                cacheBust: true,
                skipFonts: false,
                filter: (node) => {
                  // Exclude controls and background
                  if (node.classList?.contains('react-flow__controls')) return false;
                  if (node.classList?.contains('react-flow__background')) return false;
                  return true;
                },
                style: {
                  width: `${nodesBounds.width}px`,
                  height: `${nodesBounds.height}px`,
                  transform: `translate(${rfViewport.x}px, ${rfViewport.y}px) scale(${rfViewport.zoom})`,
                },
              });
              
              const link = document.createElement('a');
              link.download = `family-tree-graph.png`;
              link.href = dataUrl;
              link.click();
              setStatus('PNG exported successfully!');
              setTimeout(() => setStatus(''), 2000);
            } catch (err) {
              console.error('Failed to export PNG:', err);
              setStatus('PNG export failed');
              setTimeout(() => setStatus(''), 3000);
            }
          }}
          title="Export as PNG"
          disabled={nodes.length === 0}
          className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-white/10 text-[#9CA3B5] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all border border-white/10 hover:scale-105"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </button>
        
        <button
          onClick={async () => {
            const domViewport = reactFlowRef.current?.querySelector('.react-flow__viewport') as HTMLElement;
            if (!domViewport) {
              console.error('Viewport not found');
              return;
            }

            setStatus('Preparing PDF export...');
    
            // Wait for all images to load
            const images = domViewport.querySelectorAll('img');
            await Promise.all(
              Array.from(images).map((img) => {
                if (img.complete) return Promise.resolve();
                return new Promise((resolve) => {
                  img.onload = resolve;
                  img.onerror = resolve;
                });
              })
            );

            const nodesBounds = getNodesBounds(getNodes());
            const rfViewport = getViewportForBounds(
              nodesBounds,
              nodesBounds.width,
              nodesBounds.height,
              0.5,
              2,
              0.2
            );

            try {
              const dataUrl = await toJpeg(domViewport, {
                backgroundColor: '#0E0F19',
                width: nodesBounds.width,
                height: nodesBounds.height,
                quality: 0.95,
                cacheBust: true,
                skipFonts: false,
                filter: (node) => {
                  // Exclude controls and background
                  if (node.classList?.contains('react-flow__controls')) return false;
                  if (node.classList?.contains('react-flow__background')) return false;
                  return true;
                },
                style: {
                  width: `${nodesBounds.width}px`,
                  height: `${nodesBounds.height}px`,
                  transform: `translate(${rfViewport.x}px, ${rfViewport.y}px) scale(${rfViewport.zoom})`,
                },
              });
      
              const pdf = new jsPDF({
                orientation: nodesBounds.width > nodesBounds.height ? 'landscape' : 'portrait',
                unit: 'px',
                format: [nodesBounds.width, nodesBounds.height],
              });

              pdf.addImage(dataUrl, 'JPEG', 0, 0, nodesBounds.width, nodesBounds.height);
              pdf.save(`family-tree-graph.pdf`);
              setStatus('PDF exported successfully!');
              setTimeout(() => setStatus(''), 2000);
            } catch (err) {
              console.error('Failed to export PDF:', err);
              setStatus('PDF export failed');
              setTimeout(() => setStatus(''), 3000);
            }
          }}
          title="Export as PDF"
          disabled={nodes.length === 0}
          className="p-2 rounded-lg backdrop-blur-lg bg-white/5 hover:bg-white/10 text-[#9CA3B5] hover:text-white disabled:opacity-40 disabled:cursor-not-allowed transition-all border border-white/10 hover:scale-105"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        </button>
      </div>
      )}
      

      

      <ContextMenuComponent />
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeContextMenu={onNodeContextMenu}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        panOnScroll
        selectionOnDrag
        panOnDrag
        zoomOnScroll
        zoomOnPinch
        zoomOnDoubleClick
        preventScrolling={false}
        className="w-full h-full bg-[#0E0F19]"
      >
        <Controls position="bottom-left" className="!bg-white/50 !border-white/10 backdrop-blur-xl [&_button]:!bg-white/5 [&_button]:!border-white/10 [&_button]:!text-[#F5F7FA] [&_button:hover]:!bg-white/10" />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} className="!bg-[#0E0F19] opacity-30" color="#6B72FF" />
      </ReactFlow>
    </div>
  );
}

// Main component wrapped with ReactFlowProvider
export default function GenealogyTree(props: GenealogyTreeProps) {
  return (
    <ReactFlowProvider>
      <GenealogyTreeInternal {...props} />
    </ReactFlowProvider>
  );
}

