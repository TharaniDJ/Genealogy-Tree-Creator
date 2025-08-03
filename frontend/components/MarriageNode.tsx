import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

interface MarriageNodeData {
  label: string;
  spouse1: string;
  spouse2: string;
  nodeType: 'marriage';
}

export default function MarriageNode({ data, selected }: NodeProps<MarriageNodeData>) {
  return (
    <div className="marriage-node flex items-center justify-center">
      <Handle type="target" position={Position.Top} id="top" />
      
      <div className={`w-10 h-10 bg-pink-200 border-2 rounded-full flex items-center justify-center transition-all duration-200 ${
        selected ? 'border-pink-500 shadow-lg scale-110' : 'border-pink-400 hover:shadow-md hover:scale-105'
      }`}>
        <div className="text-sm text-pink-700 font-bold">♥</div>
      </div>
      
      <Handle type="source" position={Position.Bottom} id="bottom" />
    </div>
  );
}
