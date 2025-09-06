"use client";

import React, { useMemo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

// Category -> palette mapping
const CATEGORY_STYLES: Record<string, { from: string; to: string; ring: string; glow: string }> = {
  language: { from: 'from-emerald-500', to: 'to-green-600', ring: 'ring-emerald-300/40', glow: 'from-emerald-400 via-green-500 to-teal-500' },
  dialect: { from: 'from-indigo-500', to: 'to-purple-600', ring: 'ring-indigo-300/40', glow: 'from-indigo-400 via-purple-500 to-fuchsia-500' },
  language_family: { from: 'from-blue-500', to: 'to-cyan-600', ring: 'ring-blue-300/40', glow: 'from-blue-400 via-cyan-500 to-sky-500' },
  proto_language: { from: 'from-amber-500', to: 'to-orange-600', ring: 'ring-amber-300/40', glow: 'from-amber-400 via-orange-500 to-yellow-500' },
  extinct_language: { from: 'from-rose-500', to: 'to-red-600', ring: 'ring-rose-300/40', glow: 'from-rose-400 via-red-500 to-pink-500' },
  dead_language: { from: 'from-slate-500', to: 'to-neutral-600', ring: 'ring-slate-300/40', glow: 'from-slate-400 via-gray-500 to-zinc-500' },
};

// Modern styled language node with glassmorphism design
const LanguageNode: React.FC<NodeProps> = ({ data }) => {
  const style = useMemo(() => CATEGORY_STYLES[data.category as string] || CATEGORY_STYLES.language, [data.category]);
  return (
    <div className="relative group">
      {/* Glow effect on hover */}
      <div className={`absolute -inset-1 bg-gradient-to-r ${style.glow} rounded-2xl blur opacity-0 group-hover:opacity-25 transition-opacity duration-300`}></div>
      
      {/* Main node container */}
      <div className={`relative bg-white/90 backdrop-blur-xl border border-white/30 rounded-xl shadow-lg hover:shadow-xl transition-all duration-300 min-w-[160px] group-hover:scale-105 ring-2 ${style.ring}`}>
        <Handle 
          type="target" 
          position={Position.Top} 
          className={`!w-3 !h-3 !bg-gradient-to-r !${style.from} !${style.to} !border-2 !border-white !shadow-lg hover:!scale-125 !transition-transform !duration-200`} 
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
          className={`!w-3 !h-3 !bg-gradient-to-r !${style.from} !${style.to} !border-2 !border-white !shadow-lg hover:!scale-125 !transition-transform !duration-200`} 
        />
      </div>
    </div>
  );
};

export default LanguageNode;