import { NodeData } from "@/lib/types";
import {
  Handle,
  Position,
} from 'reactflow';

export default function ConnectionNode({ data }: { data: NodeData }) {
  const { connectionData } = data;
  
  if (!connectionData) {
    return (
      <div className="connection-content">
        <Handle
          type="target"
          position={Position.Left}
          className="w-2 h-2 bg-gray-600 border-2 border-white"
          id="left"
        />
        <Handle
          type="target"
          position={Position.Right}
          className="w-2 h-2 bg-gray-600 border-2 border-white"
          id="right"
        />
        <Handle
          type="source"
          position={Position.Bottom}
          className="w-2 h-2 bg-gray-600 border-2 border-white"
        />
        <Handle
          type="target"
          position={Position.Top}
          className="w-2 h-2 bg-gray-600 border-2 border-white"
        />
      </div>
    );
  }

  // Different connection node styles based on type
  const getConnectionIcon = () => {
    switch (connectionData.type) {
      case 'marriage':
        return '💍';
      case 'employment':
        return '💼';
      case 'partnership':
        return '🤝';
      case 'family':
        return '👨‍👩‍👧‍👦';
      case 'friendship':
        return '👫';
      default:
        return '🔗';
    }
  };

  const shouldShowLabel = connectionData.label && connectionData.type !== 'marriage';

  return (
    <div className="connection-content relative">
      {/* Input handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
        id="left"
        style={{ visibility: 'hidden' }}
      />
      <Handle
        type="target"
        position={Position.Right}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
        id="right"
        style={{ visibility: 'hidden' }}
      />
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
        id="top"
        style={{ visibility: 'hidden' }}
      />
      
      {/* Output handle */}
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
        id="bottom"
        style={{ visibility: 'hidden' }}
      />
      
      {/* Connection node visual */}
      <div className="flex items-center justify-center text-xs">
        <span role="img" aria-label={connectionData.type}>
          {getConnectionIcon()}
        </span>
        {shouldShowLabel && (
          <span className="ml-1 text-xs font-medium">
            {connectionData.label}
          </span>
        )}
      </div>
      
      {/* Additional metadata tooltip */}
      {connectionData.metadata && Object.keys(connectionData.metadata).length > 0 && (
        <div 
          className="absolute top-full left-1/2 transform -translate-x-1/2 mt-1 bg-black/80 text-white text-xs px-2 py-1 rounded opacity-0 hover:opacity-100 transition-opacity z-10 whitespace-nowrap"
          title={JSON.stringify(connectionData.metadata, null, 2)}
        >
          {connectionData.metadata.date && `Date: ${connectionData.metadata.date}`}
          {connectionData.metadata.location && ` | Location: ${connectionData.metadata.location}`}
        </div>
      )}
    </div>
  );
}
