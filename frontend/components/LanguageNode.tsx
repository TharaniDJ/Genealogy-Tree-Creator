"use client";

import React, { useMemo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

// Category -> palette mapping for dark theme
const CATEGORY_STYLES: Record<string, { from: string; to: string; ring: string; glow: string; bg: string }> = {
  language: { 
    from: 'from-emerald-400', 
    to: 'to-green-500', 
    ring: 'ring-emerald-400/30', 
    glow: 'from-emerald-400 via-green-500 to-teal-500',
    bg: 'bg-gray-800/90'
  },
  dialect: { 
    from: 'from-indigo-400', 
    to: 'to-purple-500', 
    ring: 'ring-indigo-400/30', 
    glow: 'from-indigo-400 via-purple-500 to-fuchsia-500',
    bg: 'bg-gray-800/90'
  },
  language_family: { 
    from: 'from-blue-400', 
    to: 'to-cyan-500', 
    ring: 'ring-blue-400/30', 
    glow: 'from-blue-400 via-cyan-500 to-sky-500',
    bg: 'bg-gray-800/90'
  },
  proto_language: { 
    from: 'from-amber-400', 
    to: 'to-orange-500', 
    ring: 'ring-amber-400/30', 
    glow: 'from-amber-400 via-orange-500 to-yellow-500',
    bg: 'bg-gray-800/90'
  },
  extinct_language: { 
    from: 'from-rose-400', 
    to: 'to-red-500', 
    ring: 'ring-rose-400/30', 
    glow: 'from-rose-400 via-red-500 to-pink-500',
    bg: 'bg-gray-800/90'
  },
  dead_language: { 
    from: 'from-slate-400', 
    to: 'to-neutral-500', 
    ring: 'ring-slate-400/30', 
    glow: 'from-slate-400 via-gray-500 to-zinc-500',
    bg: 'bg-gray-800/90'
  },
};

type LanguageNodeData = { label: string; meta?: string; category?: string; qid?: string; onExpand?: () => void };

// Modern styled language node with glassmorphism design for dark theme
const LanguageNode: React.FC<NodeProps<LanguageNodeData>> = ({ data }) => {
  const style = useMemo(() => CATEGORY_STYLES[data.category as string] || CATEGORY_STYLES.language, [data.category]);
  return (
    <div className="relative group">
      {/* Enhanced glow effect on hover */}
      <div className={`absolute -inset-1 bg-gradient-to-r ${style.glow} rounded-2xl blur-sm opacity-0 group-hover:opacity-40 transition-opacity duration-300`}></div>
      
      {/* Main node container with dark theme */}
      <div className={`relative ${style.bg} backdrop-blur-xl border border-gray-600/40 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 min-w-[160px] group-hover:scale-105 ring-2 ${style.ring}`}>
        <Handle 
          type="target" 
          position={Position.Top} 
          className={`!w-3 !h-3 !bg-gradient-to-r !${style.from} !${style.to} !border-2 !border-gray-700 !shadow-lg hover:!scale-125 !transition-transform !duration-200`} 
        />
        
        {/* Content with dark theme text */}
        <div className="px-4 py-3 text-center">
          <div className="font-semibold text-gray-100 text-sm leading-tight mb-1">
            {data.label}
          </div>
          {data.meta && (
            <div className="text-xs text-gray-400 opacity-90">
              {data.meta}
            </div>
          )}
        </div>

        {/* Subtle gradient overlay for dark theme */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/20 via-transparent to-cyan-900/20 rounded-xl pointer-events-none"></div>
        {/* Expand button (shown on hover if handler exists) */}
        {data.onExpand && (
          <button
            onClick={(e) => { e.stopPropagation(); data.onExpand && data.onExpand(); }}
            title="Expand"
            className="absolute -bottom-2 -right-2 px-2 py-1 text-[10px] font-medium rounded-lg bg-purple-600/80 text-white border border-purple-400/40 shadow hover:bg-purple-600 transition-colors opacity-0 group-hover:opacity-100"
          >
            Expand
          </button>
        )}

        <Handle 
          type="source" 
          position={Position.Bottom} 
          className={`!w-3 !h-3 !bg-gradient-to-r !${style.from} !${style.to} !border-2 !border-gray-700 !shadow-lg hover:!scale-125 !transition-transform !duration-200`} 
        />
      </div>
    </div>
  );
};

export default LanguageNode;