import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface PersonNodeData {
  label: string;
  entity: string;
  qid: string;
  birth_year?: string;
  death_year?: string;
  image_url?: string;
  nodeType: 'entity';
}

export default function PersonNode({ data, selected }: NodeProps<PersonNodeData>) {
  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(n => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const formatYears = (birth?: string, death?: string) => {
    if (birth && death) {
      return `${birth} - ${death}`;
    } else if (birth) {
      return `${birth} - present`;
    }
    return '';
  };

  return (
    <div className="person-node">
      <Handle type="target" position={Position.Top} />
      
      <div className={`w-48 bg-white border-2 rounded-lg shadow-md p-4 text-center transition-all duration-200 ${
        selected ? 'border-blue-500 shadow-lg' : 'border-gray-300 hover:shadow-lg'
      }`}>
        <div className="w-16 h-16 mx-auto mb-2 rounded-full overflow-hidden bg-gray-100 flex items-center justify-center">
          {data.image_url ? (
            <img 
              src={data.image_url} 
              alt={data.entity}
              className="w-full h-full object-cover"
            />
          ) : (
            <span className="text-white bg-gradient-to-r from-blue-500 to-purple-600 w-full h-full flex items-center justify-center text-sm font-bold">
              {getInitials(data.entity)}
            </span>
          )}
        </div>
        
        <h3 className="font-semibold text-sm mb-1 line-clamp-2">
          {data.entity}
        </h3>
        
        {(data.birth_year || data.death_year) && (
          <p className="text-xs text-gray-600">
            {formatYears(data.birth_year, data.death_year)}
          </p>
        )}
        
        {data.qid && (
          <p className="text-xs text-gray-400 mt-1">
            {data.qid}
          </p>
        )}
      </div>
      
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}
