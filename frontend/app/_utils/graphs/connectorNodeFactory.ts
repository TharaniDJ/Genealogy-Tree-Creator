import { GraphEdge } from "@/lib/types";
import { Edge } from 'reactflow';

// Generic edge factory for connecting nodes
export const createGenericEdge = (
  sourceId: string,
  targetId: string,
  edgeType: string = 'default',
  label?: string,
  metadata?: Record<string, any>,
  customStyle?: Record<string, any>
): Edge => {
  const edgeId = `${sourceId}-to-${targetId}`;
  
  // Default styling based on edge type
  const defaultStyle = getEdgeStyle(edgeType);
  const mergedStyle = { ...defaultStyle, ...customStyle };
  
  return {
    id: edgeId,
    source: sourceId,
    target: targetId,
    type: 'smoothstep',
    label: label || '',
    style: mergedStyle,
    animated: shouldAnimateEdge(edgeType),
    data: { 
      edgeType,
      metadata: metadata || {}
    },
  };
};

// Edge styling based on type
export const getEdgeStyle = (edgeType: string): Record<string, any> => {
  const typeStyles: Record<string, Record<string, any>> = {
    marriage: {
      stroke: '#FF69B4',
      strokeWidth: 2,
      strokeOpacity: 0.8,
      strokeDasharray: '3,3',
    },
    'parent-child': {
      stroke: '#4CAF50',
      strokeWidth: 2,
      strokeOpacity: 0.8,
      strokeDasharray: '5,5',
    },
    employment: {
      stroke: '#2196F3',
      strokeWidth: 2,
      strokeOpacity: 0.7,
      strokeDasharray: '2,2',
    },
    partnership: {
      stroke: '#E91E63',
      strokeWidth: 2,
      strokeOpacity: 0.8,
      strokeDasharray: '4,4',
    },
    friendship: {
      stroke: '#FF9800',
      strokeWidth: 1,
      strokeOpacity: 0.6,
      strokeDasharray: '1,1',
    },
    default: {
      stroke: '#9E9E9E',
      strokeWidth: 1,
      strokeOpacity: 0.6,
    }
  };

  return typeStyles[edgeType] || typeStyles.default;
};

// Determine if edge should be animated
export const shouldAnimateEdge = (edgeType: string): boolean => {
  const animatedTypes = ['marriage', 'partnership', 'parent-child'];
  return animatedTypes.includes(edgeType);
};

// Edge color helper (legacy support)
export const getEdgeColor = (index: number) => {
  const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff'];
  return colors[index % colors.length];
};

// Function to update edges for hover effects
export const updateEdgesForHover = (currentEdges: Edge[], hoveredEdge: string | null) => {
  return currentEdges.map((edge) => {
    const isHovered = hoveredEdge === edge.id;
    const edgeType = edge.data?.edgeType || 'default';
    
    return {
      ...edge,
      label: isHovered ? getEdgeLabel(edgeType) : '',
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
  });
};

// Get edge label based on type
export const getEdgeLabel = (edgeType: string): string => {
  const labels: Record<string, string> = {
    marriage: 'Marriage',
    'parent-child': 'Parent-Child',
    employment: 'Employment',
    partnership: 'Partnership',
    friendship: 'Friendship',
    default: 'Connection'
  };

  return labels[edgeType] || labels.default;
};

// Convert backend GraphEdge to React Flow Edge
export const convertGraphEdgeToReactFlowEdge = (graphEdge: GraphEdge): Edge => {
  return createGenericEdge(
    graphEdge.source,
    graphEdge.target,
    graphEdge.type || 'default',
    graphEdge.label,
    graphEdge.data,
    graphEdge.style
  );
};
