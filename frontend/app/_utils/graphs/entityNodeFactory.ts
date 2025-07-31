import { EntityNodeData, ConnectionNodeData, GenerationInfo } from "@/lib/types";
import { Node } from 'reactflow';

// Generic entity node factory
export const createEntityNode = (
  entityData: EntityNodeData,
  generation: number,
  generationCounts: React.MutableRefObject<Record<number, number>>,
  generationData: React.MutableRefObject<Record<string, GenerationInfo>>,
  customStyle?: Record<string, any>
): Node => {
  const pos = getHierarchicalPosition(entityData.id, generation, generationCounts, generationData);
  
  // Default styling based on entity type
  const defaultStyle = getEntityNodeStyle(entityData.type, generation);
  const mergedStyle = { ...defaultStyle, ...customStyle };
  
  return {
    id: entityData.id,
    type: 'entity',
    position: pos,
    data: {
      label: entityData.label,
      generation,
      connections: entityData.connections || 0,
      nodeType: 'entity' as const,
      entityData
    },
    style: mergedStyle,
  };
};

// Generic connection node factory
export const createConnectionNode = (
  connectionData: ConnectionNodeData,
  generation: number,
  generationCounts: React.MutableRefObject<Record<number, number>>,
  generationData: React.MutableRefObject<Record<string, GenerationInfo>>,
  customStyle?: Record<string, any>
): Node => {
  const pos = getHierarchicalPosition(connectionData.id, generation, generationCounts, generationData);
  
  // Default styling based on connection type
  const defaultStyle = getConnectionNodeStyle(connectionData.type);
  const mergedStyle = { ...defaultStyle, ...customStyle };
  
  return {
    id: connectionData.id,
    type: 'connection',
    position: pos,
    data: {
      label: connectionData.label || '',
      generation,
      connections: 0,
      nodeType: 'connection' as const,
      connectionData
    },
    style: mergedStyle,
  };
};

// Positioning function for hierarchical layout
export const getHierarchicalPosition = (
  nodeId: string,
  generation: number,
  generationCounts: React.MutableRefObject<Record<number, number>>,
  generationData: React.MutableRefObject<Record<string, GenerationInfo>>
) => {
  if (!generationCounts.current[generation]) {
    generationCounts.current[generation] = 0;
  }
  
  if (!generationData.current[nodeId]) {
    generationData.current[nodeId] = {
      generation,
      position: generationCounts.current[generation]++
    };
  }
  
  const data = generationData.current[nodeId];
  const nodesInGeneration = generationCounts.current[generation];
  const x = (data.position - (nodesInGeneration - 1) / 2) * 350;
  const y = generation * 250;
  
  return { x, y };
};

// Styling for entity nodes based on type
export const getEntityNodeStyle = (entityType: string, generation: number = 0): Record<string, any> => {
  const baseStyles = {
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
  };

  // Different styles based on entity type
  const typeStyles: Record<string, Record<string, any>> = {
    person: {
      background: getNodeColor(generation, 0),
    },
    company: {
      background: 'linear-gradient(45deg, #4CAF50, #2E7D32)',
    },
    event: {
      background: 'linear-gradient(45deg, #FF9800, #F57C00)',
    },
    location: {
      background: 'linear-gradient(45deg, #9C27B0, #7B1FA2)',
    },
    default: {
      background: 'linear-gradient(45deg, #607D8B, #455A64)',
    }
  };

  return {
    ...baseStyles,
    ...(typeStyles[entityType] || typeStyles.default)
  };
};

// Styling for connection nodes based on type
export const getConnectionNodeStyle = (connectionType: string): Record<string, any> => {
  const baseStyles = {
    border: '2px solid #ffffff',
    borderRadius: '50%',
    padding: '4px',
    width: '10px',
    height: '10px',
    fontSize: '8px',
    fontWeight: 'bold',
    color: '#333',
    boxShadow: '0 4px 12px rgba(255,215,0,0.4)',
  };

  // Different styles based on connection type
  const typeStyles: Record<string, Record<string, any>> = {
    marriage: {
      background: 'linear-gradient(45deg, #FFD700, #FFA500)',
    },
    employment: {
      background: 'linear-gradient(45deg, #2196F3, #1976D2)',
    },
    partnership: {
      background: 'linear-gradient(45deg, #E91E63, #C2185B)',
    },
    family: {
      background: 'linear-gradient(45deg, #4CAF50, #388E3C)',
    },
    default: {
      background: 'linear-gradient(45deg, #9E9E9E, #616161)',
    }
  };

  return {
    ...baseStyles,
    ...(typeStyles[connectionType] || typeStyles.default)
  };
};

// Helper function to get node colors (legacy support)
export const getNodeColor = (generation: number, connections: number = 0) => {
  const baseColors = [
    '#e3f2fd', '#bbdefb', '#90caf9', '#64b5f6', '#42a5f5', '#2196f3', '#1976d2'
  ];
  const color = baseColors[Math.min(generation, baseColors.length - 1)];
  
  const opacity = Math.min(0.7 + (connections * 0.1), 1);
  return color + Math.floor(opacity * 255).toString(16).padStart(2, '0');
};
