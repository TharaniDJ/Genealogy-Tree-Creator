"use client";

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

// Modern styled language node with glassmorphism design
const LanguageNode: React.FC<NodeProps> = ({ data }) => {
  return (
    <div className="relative group">
      {/* Glow effect on hover */}
      <div className="absolute -inset-1 bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-500 rounded-2xl blur opacity-0 group-hover:opacity-20 transition-opacity duration-300"></div>
      
      {/* Main node container */}
      <div className="relative bg-white/90 backdrop-blur-xl border border-white/30 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 min-w-[160px] group-hover:scale-105">
        <Handle 
          type="target" 
          position={Position.Top} 
          className="!w-3 !h-3 !bg-gradient-to-r !from-blue-500 !to-indigo-600 !border-2 !border-white !shadow-lg hover:!scale-125 !transition-transform !duration-200" 
        />
        
        {/* Content */}
        <div className="px-4 py-3 text-center">
          <div className="font-semibold text-slate-800 text-sm leading-tight mb-1">
            {data.label}
          </div>
          {data.meta && (
            <div className="text-xs text-slate-500 opacity-80">
              {data.meta}
            </div>
          )}
        </div>

        {/* Subtle gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-50/30 via-transparent to-indigo-50/30 rounded-xl pointer-events-none"></div>
        
        <Handle 
          type="source" 
          position={Position.Bottom} 
          className="!w-3 !h-3 !bg-gradient-to-r !from-indigo-500 !to-purple-600 !border-2 !border-white !shadow-lg hover:!scale-125 !transition-transform !duration-200" 
        />
      </div>
    </div>
  );
};

export default LanguageNode;