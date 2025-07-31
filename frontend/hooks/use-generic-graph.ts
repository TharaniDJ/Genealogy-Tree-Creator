import { useRef, useCallback } from 'react';
import { Node, Edge } from 'reactflow';
import { GenericGraphBuilder, createGraphBuilder, updateEdgesForHover } from '@/app/_utils/graphs';
import { GraphNode, GraphEdge, GenerationInfo } from '@/lib/types';

export function useGenericGraph() {
  // Create refs for generation tracking
  const generationCounts = useRef<Record<number, number>>({});
  const generationData = useRef<Record<string, GenerationInfo>>({});
  
  // Create the graph builder instance
  const graphBuilder = useRef<GenericGraphBuilder | null>(null);
  
  // Initialize graph builder if not already created
  const getGraphBuilder = useCallback(() => {
    if (!graphBuilder.current) {
      graphBuilder.current = createGraphBuilder(generationCounts, generationData);
    }
    return graphBuilder.current;
  }, []);

  // Build graph from backend data
  const buildGraphFromBackend = useCallback((
    backendNodes: GraphNode[], 
    backendEdges: GraphEdge[]
  ): { nodes: Node[]; edges: Edge[] } => {
    const builder = getGraphBuilder();
    return builder.buildGraphFromBackend(backendNodes, backendEdges);
  }, [getGraphBuilder]);

  // Add a single entity node
  const addEntityNode = useCallback((
    id: string,
    label: string,
    entityType: string,
    data: Record<string, any>,
    generation: number = 0,
    customStyle?: Record<string, any>
  ): Node => {
    const builder = getGraphBuilder();
    return builder.addEntityNode(id, label, entityType, data, generation, customStyle);
  }, [getGraphBuilder]);

  // Add a single connection node
  const addConnectionNode = useCallback((
    id: string,
    connectionType: string,
    generation: number = 0,
    label?: string,
    metadata?: Record<string, any>,
    customStyle?: Record<string, any>
  ): Node => {
    const builder = getGraphBuilder();
    return builder.addConnectionNode(id, connectionType, generation, label, metadata, customStyle);
  }, [getGraphBuilder]);

  // Add a generic edge
  const addEdge = useCallback((
    sourceId: string,
    targetId: string,
    edgeType: string = 'default',
    label?: string,
    metadata?: Record<string, any>,
    customStyle?: Record<string, any>
  ): Edge => {
    const builder = getGraphBuilder();
    return builder.addEdge(sourceId, targetId, edgeType, label, metadata, customStyle);
  }, [getGraphBuilder]);

  // Update existing graph with new data
  const updateGraph = useCallback((
    currentNodes: Node[],
    currentEdges: Edge[],
    newBackendNodes: GraphNode[],
    newBackendEdges: GraphEdge[]
  ): { nodes: Node[]; edges: Edge[] } => {
    const builder = getGraphBuilder();
    return builder.updateGraph(currentNodes, currentEdges, newBackendNodes, newBackendEdges);
  }, [getGraphBuilder]);

  // Clear generation data
  const clearGenerations = useCallback(() => {
    const builder = getGraphBuilder();
    builder.clearGenerations();
  }, [getGraphBuilder]);

  // Export the updateEdgesForHover function
  const updateEdgesForHoverCallback = useCallback((
    edges: Edge[],
    hoveredEdgeId: string | null
  ): Edge[] => {
    return updateEdgesForHover(edges, hoveredEdgeId);
  }, []);

  return {
    buildGraphFromBackend,
    addEntityNode,
    addConnectionNode,
    addEdge,
    updateGraph,
    clearGenerations,
    updateEdgesForHover: updateEdgesForHoverCallback,
    // Expose generation tracking for backward compatibility
    generationCounts,
    generationData
  };
}
