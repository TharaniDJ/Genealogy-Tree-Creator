import { Node, Edge, Position } from 'reactflow';
import { GraphNode, GraphEdge, GenerationInfo } from '@/lib/types';
import { MutableRefObject } from 'react';

export interface GenericGraphBuilder {
  buildGraphFromBackend(backendNodes: GraphNode[], backendEdges: GraphEdge[]): { nodes: Node[]; edges: Edge[] };
  addEntityNode(id: string, label: string, entityType: string, data: Record<string, any>, generation?: number, customStyle?: Record<string, any>): Node;
  addConnectionNode(id: string, connectionType: string, generation?: number, label?: string, metadata?: Record<string, any>, customStyle?: Record<string, any>): Node;
  addEdge(sourceId: string, targetId: string, edgeType?: string, label?: string, metadata?: Record<string, any>, customStyle?: Record<string, any>): Edge;
  updateGraph(currentNodes: Node[], currentEdges: Edge[], newBackendNodes: GraphNode[], newBackendEdges: GraphEdge[]): { nodes: Node[]; edges: Edge[] };
  clearGenerations(): void;
}

export function createGraphBuilder(
  generationCounts: MutableRefObject<Record<number, number>>,
  generationData: MutableRefObject<Record<string, GenerationInfo>>
): GenericGraphBuilder {
  
  const calculatePosition = (generation: number, nodeId: string): { x: number; y: number } => {
    if (!generationCounts.current[generation]) {
      generationCounts.current[generation] = 0;
    }
    
    const position = generationCounts.current[generation];
    generationCounts.current[generation]++;
    
    const x = position * 250 + 100; // Horizontal spacing
    const y = generation * 150 + 100; // Vertical spacing between generations
    
    generationData.current[nodeId] = { generation, position: { x, y }, nodeId };
    
    return { x, y };
  };

  const addEntityNode = (
    id: string,
    label: string,
    entityType: string,
    data: Record<string, any>,
    generation: number = 0,
    customStyle?: Record<string, any>
  ): Node => {
    const position = calculatePosition(generation, id);
    
    return {
      id,
      type: 'default',
      position,
      data: {
        label,
        nodeType: 'entity',
        entityData: {
          id,
          label,
          type: entityType,
          data,
          generation,
          connections: 0
        },
        ...data
      },
      style: {
        background: '#fff',
        border: '2px solid #ddd',
        borderRadius: '8px',
        padding: '10px',
        minWidth: '150px',
        ...customStyle
      },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
    };
  };

  const addConnectionNode = (
    id: string,
    connectionType: string,
    generation: number = 0,
    label?: string,
    metadata?: Record<string, any>,
    customStyle?: Record<string, any>
  ): Node => {
    const position = calculatePosition(generation, id);
    
    return {
      id,
      type: 'default',
      position,
      data: {
        label: label || connectionType,
        nodeType: 'connection',
        connectionData: {
          id,
          label,
          type: connectionType,
          metadata,
          generation
        }
      },
      style: {
        background: '#f0f8ff',
        border: '2px solid #87ceeb',
        borderRadius: '50%',
        padding: '5px',
        width: '100px',
        height: '50px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontSize: '12px',
        ...customStyle
      },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
    };
  };

  const addEdge = (
    sourceId: string,
    targetId: string,
    edgeType: string = 'default',
    label?: string,
    metadata?: Record<string, any>,
    customStyle?: Record<string, any>
  ): Edge => {
    return {
      id: `${sourceId}-${targetId}`,
      source: sourceId,
      target: targetId,
      type: edgeType,
      label,
      data: metadata,
      style: {
        stroke: '#999',
        strokeWidth: 2,
        ...customStyle
      },
      labelStyle: {
        fontSize: '12px',
        fontWeight: 'bold'
      }
    };
  };

  const buildGraphFromBackend = (
    backendNodes: GraphNode[],
    backendEdges: GraphEdge[]
  ): { nodes: Node[]; edges: Edge[] } => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Convert backend nodes to frontend nodes
    backendNodes.forEach(backendNode => {
      if (backendNode.type === 'entity') {
        const node = addEntityNode(
          backendNode.id,
          backendNode.label,
          backendNode.data.type || 'person',
          backendNode.data,
          backendNode.data.generation || 0,
          backendNode.style
        );
        nodes.push(node);
      } else if (backendNode.type === 'connection') {
        const node = addConnectionNode(
          backendNode.id,
          backendNode.data.type || 'relationship',
          backendNode.data.generation || 0,
          backendNode.label,
          backendNode.data,
          backendNode.style
        );
        nodes.push(node);
      }
    });

    // Convert backend edges to frontend edges
    backendEdges.forEach(backendEdge => {
      const edge = addEdge(
        backendEdge.source,
        backendEdge.target,
        backendEdge.type,
        backendEdge.label,
        backendEdge.data,
        backendEdge.style
      );
      edges.push(edge);
    });

    return { nodes, edges };
  };

  const updateGraph = (
    currentNodes: Node[],
    currentEdges: Edge[],
    newBackendNodes: GraphNode[],
    newBackendEdges: GraphEdge[]
  ): { nodes: Node[]; edges: Edge[] } => {
    // For now, we'll replace the entire graph
    // In a more sophisticated implementation, we could merge/update existing nodes
    return buildGraphFromBackend(newBackendNodes, newBackendEdges);
  };

  const clearGenerations = (): void => {
    generationCounts.current = {};
    generationData.current = {};
  };

  return {
    buildGraphFromBackend,
    addEntityNode,
    addConnectionNode,
    addEdge,
    updateGraph,
    clearGenerations
  };
}

export function updateEdgesForHover(edges: Edge[], hoveredEdgeId: string | null): Edge[] {
  return edges.map(edge => ({
    ...edge,
    style: {
      ...edge.style,
      stroke: hoveredEdgeId === edge.id ? '#ff6b6b' : '#999',
      strokeWidth: hoveredEdgeId === edge.id ? 3 : 2,
    }
  }));
}
