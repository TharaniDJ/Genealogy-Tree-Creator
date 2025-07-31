import { GraphNode, GraphEdge, EntityNodeData, ConnectionNodeData, GenerationInfo } from "@/lib/types";
import { Node, Edge } from 'reactflow';
import { createEntityNode, createConnectionNode, getHierarchicalPosition } from './entityNodeFactory';
import { createGenericEdge, convertGraphEdgeToReactFlowEdge, updateEdgesForHover } from './connectorNodeFactory';

// Main graph builder class
export class GenericGraphBuilder {
  private generationCounts: React.MutableRefObject<Record<number, number>>;
  private generationData: React.MutableRefObject<Record<string, GenerationInfo>>;
  
  constructor(
    generationCounts: React.MutableRefObject<Record<number, number>>,
    generationData: React.MutableRefObject<Record<string, GenerationInfo>>
  ) {
    this.generationCounts = generationCounts;
    this.generationData = generationData;
  }

  // Build graph from backend data
  buildGraphFromBackend(
    backendNodes: GraphNode[], 
    backendEdges: GraphEdge[]
  ): { nodes: Node[]; edges: Edge[] } {
    const nodes = this.buildNodes(backendNodes);
    const edges = this.buildEdges(backendEdges);
    
    return { nodes, edges };
  }

  // Build nodes from backend data
  private buildNodes(backendNodes: GraphNode[]): Node[] {
    return backendNodes.map(graphNode => {
      const generation = this.calculateGeneration(graphNode);
      
      if (graphNode.type === 'entity') {
        const entityData: EntityNodeData = {
          id: graphNode.id,
          label: graphNode.label,
          type: graphNode.data.entityType || 'default',
          data: graphNode.data,
          generation
        };
        
        return createEntityNode(
          entityData,
          generation,
          this.generationCounts,
          this.generationData,
          graphNode.style
        );
      } else {
        const connectionData: ConnectionNodeData = {
          id: graphNode.id,
          label: graphNode.label,
          type: graphNode.data.connectionType || 'default',
          metadata: graphNode.data,
          generation
        };
        
        return createConnectionNode(
          connectionData,
          generation,
          this.generationCounts,
          this.generationData,
          graphNode.style
        );
      }
    });
  }

  // Build edges from backend data
  private buildEdges(backendEdges: GraphEdge[]): Edge[] {
    return backendEdges.map(graphEdge => convertGraphEdgeToReactFlowEdge(graphEdge));
  }

  // Calculate generation for a node (can be overridden by backend)
  private calculateGeneration(graphNode: GraphNode): number {
    if (graphNode.data.generation !== undefined) {
      return graphNode.data.generation;
    }
    
    // Default generation calculation logic
    return 0;
  }

  // Add a single entity node
  addEntityNode(
    id: string,
    label: string,
    entityType: string,
    data: Record<string, any>,
    generation: number = 0,
    customStyle?: Record<string, any>
  ): Node {
    const entityData: EntityNodeData = {
      id,
      label,
      type: entityType,
      data,
      generation
    };

    return createEntityNode(
      entityData,
      generation,
      this.generationCounts,
      this.generationData,
      customStyle
    );
  }

  // Add a single connection node
  addConnectionNode(
    id: string,
    connectionType: string,
    generation: number = 0,
    label?: string,
    metadata?: Record<string, any>,
    customStyle?: Record<string, any>
  ): Node {
    const connectionData: ConnectionNodeData = {
      id,
      label,
      type: connectionType,
      metadata,
      generation
    };

    return createConnectionNode(
      connectionData,
      generation,
      this.generationCounts,
      this.generationData,
      customStyle
    );
  }

  // Add a generic edge
  addEdge(
    sourceId: string,
    targetId: string,
    edgeType: string = 'default',
    label?: string,
    metadata?: Record<string, any>,
    customStyle?: Record<string, any>
  ): Edge {
    return createGenericEdge(sourceId, targetId, edgeType, label, metadata, customStyle);
  }

  // Update existing nodes and edges with new data
  updateGraph(
    currentNodes: Node[],
    currentEdges: Edge[],
    newBackendNodes: GraphNode[],
    newBackendEdges: GraphEdge[]
  ): { nodes: Node[]; edges: Edge[] } {
    // Merge existing nodes with new ones
    const existingNodeIds = new Set(currentNodes.map(n => n.id));
    const newNodes = newBackendNodes
      .filter(n => !existingNodeIds.has(n.id))
      .map(n => this.buildNodes([n])[0]);

    // Merge existing edges with new ones  
    const existingEdgeIds = new Set(currentEdges.map(e => e.id));
    const newEdges = newBackendEdges
      .filter(e => !existingEdgeIds.has(`${e.source}-to-${e.target}`))
      .map(e => convertGraphEdgeToReactFlowEdge(e));

    return {
      nodes: [...currentNodes, ...newNodes],
      edges: [...currentEdges, ...newEdges]
    };
  }

  // Clear generation data
  clearGenerations() {
    this.generationCounts.current = {};
    this.generationData.current = {};
  }
}

// Utility functions for backward compatibility and convenience
export const createGraphBuilder = (
  generationCounts: React.MutableRefObject<Record<number, number>>,
  generationData: React.MutableRefObject<Record<string, GenerationInfo>>
) => {
  return new GenericGraphBuilder(generationCounts, generationData);
};

// Export hover functionality
export { updateEdgesForHover } from './connectorNodeFactory';

// Export individual factories for direct use
export { createEntityNode, createConnectionNode } from './entityNodeFactory';
export { createGenericEdge } from './connectorNodeFactory';
