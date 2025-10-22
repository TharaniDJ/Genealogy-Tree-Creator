"use client";

import React, { useMemo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

// Category -> palette mapping for dark theme with blue/purple accents
const CATEGORY_STYLES: Record<string, { from: string; to: string; ring: string; glow: string; bg: string }> = {
  // Core language categories – spaced across blue/purple/green for better distinction
  language: {
    from: 'from-[#3B82F6]', // blue-500
    to: 'to-[#6366F1]',     // indigo-500
    ring: 'ring-[#3B82F6]/35',
    glow: 'from-[#3B82F6] via-[#6366F1] to-[#818CF8]',
    bg: 'bg-[#0f172a]/90'
  },
  dialect: {
    from: 'from-[#06B6D4]', // cyan-500
    to: 'to-[#22D3EE]',     // cyan-400
    ring: 'ring-[#06B6D4]/35',
    glow: 'from-[#06B6D4] via-[#22D3EE] to-[#67E8F9]',
    bg: 'bg-[#0f172a]/90'
  },
  language_family: {
    from: 'from-[#8B5CF6]', // violet-500
    to: 'to-[#A78BFA]',     // violet-400
    ring: 'ring-[#8B5CF6]/35',
    glow: 'from-[#8B5CF6] via-[#A78BFA] to-[#C4B5FD]',
    bg: 'bg-[#151225]/90'
  },
  proto_language: {
    from: 'from-[#10B981]', // emerald-500
    to: 'to-[#34D399]',     // emerald-400
    ring: 'ring-[#10B981]/35',
    glow: 'from-[#10B981] via-[#34D399] to-[#6EE7B7]',
    bg: 'bg-[#0f1b17]/90'
  },
  extinct_language: {
    from: 'from-[#64748B]', // slate-500
    to: 'to-[#94A3B8]',     // slate-400
    ring: 'ring-[#64748B]/35',
    glow: 'from-[#64748B] via-[#94A3B8] to-[#CBD5E1]',
    bg: 'bg-[#13161d]/90'
  },
  dead_language: {
    from: 'from-[#14B8A6]', // teal-500
    to: 'to-[#2DD4BF]',     // teal-400
    ring: 'ring-[#14B8A6]/35',
    glow: 'from-[#14B8A6] via-[#2DD4BF] to-[#99F6E4]',
    bg: 'bg-[#0f172a]/90'
  },
  // Special categories
  sign_language: {
    from: 'from-[#84CC16]', // lime-500
    to: 'to-[#A3E635]',     // lime-400
    ring: 'ring-[#84CC16]/35',
    glow: 'from-[#84CC16] via-[#A3E635] to-[#BEF264]',
    bg: 'bg-[#0f1b17]/90'
  },
  creole_language: {
    from: 'from-[#F59E0B]', // amber-500
    to: 'to-[#FBBF24]',     // amber-400
    ring: 'ring-[#F59E0B]/35',
    glow: 'from-[#F59E0B] via-[#FBBF24] to-[#FCD34D]',
    bg: 'bg-[#1b160e]/90'
  },
  pidgin_language: {
    from: 'from-[#EC4899]', // pink-500
    to: 'to-[#F472B6]',     // pink-400
    ring: 'ring-[#EC4899]/35',
    glow: 'from-[#EC4899] via-[#F472B6] to-[#FDA4AF]',
    bg: 'bg-[#1b0f16]/90'
  },
  modern_language: {
    from: 'from-[#0EA5E9]', // sky-500
    to: 'to-[#38BDF8]',     // sky-400
    ring: 'ring-[#0EA5E9]/35',
    glow: 'from-[#0EA5E9] via-[#38BDF8] to-[#7DD3FC]',
    bg: 'bg-[#0f172a]/90'
  },
  historical_language: {
    from: 'from-[#A855F7]', // purple-500
    to: 'to-[#C084FC]',     // purple-400
    ring: 'ring-[#A855F7]/35',
    glow: 'from-[#A855F7] via-[#C084FC] to-[#E9D5FF]',
    bg: 'bg-[#151225]/90'
  },
  ancient_language: {
    from: 'from-[#F97316]', // orange-500
    to: 'to-[#FB923C]',     // orange-400
    ring: 'ring-[#F97316]/35',
    glow: 'from-[#F97316] via-[#FB923C] to-[#FDBA74]',
    bg: 'bg-[#1f1410]/90'
  },
  unresolved: {
    from: 'from-[#EF4444]', // red-500
    to: 'to-[#F87171]',     // red-400
    ring: 'ring-[#EF4444]/60',
    glow: 'from-[#EF4444] via-[#F87171] to-[#FCA5A5]',
    bg: 'bg-[#1a1010]/90'
  },
};

type LanguageNodeData = { label: string; meta?: string; category?: string; qid?: string; types?: string[]; onExpand?: () => void };

// Modern styled language node with glassmorphism design for dark theme
const LanguageNode: React.FC<NodeProps<LanguageNodeData>> = ({ data }) => {
  const style = useMemo(() => CATEGORY_STYLES[data.category as string] || CATEGORY_STYLES.language, [data.category]);
  const isUnresolved = data.category === 'unresolved';
  return (
    <div className="relative group">
      {/* Enhanced glow effect on hover */}
      <div className={`absolute -inset-1 bg-gradient-to-r ${style.glow} rounded-2xl blur-sm opacity-0 group-hover:opacity-40 transition-opacity duration-300`}></div>
      
      {/* Main node container with dark theme */}
      <div className={`relative ${style.bg} backdrop-blur-xl border border-white/10 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 min-w-[160px] group-hover:scale-105 ring-2 ${style.ring} ${isUnresolved ? 'animate-pulse' : ''}`}>
        <Handle 
          type="target" 
          position={Position.Top} 
          className={`!w-3 !h-3 !bg-gradient-to-r !${style.from} !${style.to} !border-2 !border-[#0E0F19] !shadow-lg hover:!scale-125 !transition-transform !duration-200`} 
        />
        
        {/* Content with dark theme text */}
        <div className="px-4 py-3 text-center">
          <div className="font-semibold text-[#F5F7FA] text-sm leading-tight mb-1">
            {data.label}
          </div>
          {data.meta && (
            <div className="text-xs text-[#9CA3B5] opacity-90">
              {data.meta}
            </div>
          )}
        </div>

        {/* Subtle gradient overlay for dark theme */}
        <div className={`absolute inset-0 bg-gradient-to-br ${style.glow} opacity-10 rounded-xl pointer-events-none`}></div>
        {/* Expand button (shown on hover if handler exists) */}
        {data.onExpand && (
          <button
            onClick={(e) => { 
              e.stopPropagation(); 
              if (data.onExpand) {
                data.onExpand();
              }
            }}
            title="Expand"
            className={`absolute -bottom-2 -right-2 px-2 py-1 text-[10px] font-medium rounded-lg bg-gradient-to-r ${style.from} ${style.to} text-white border border-white/20 shadow-lg hover:scale-110 transition-all opacity-0 group-hover:opacity-100`}
          >
            Expand
          </button>
        )}

        <Handle 
          type="source" 
          position={Position.Bottom} 
          className={`!w-3 !h-3 !bg-gradient-to-r !${style.from} !${style.to} !border-2 !border-[#0E0F19] !shadow-lg hover:!scale-125 !transition-transform !duration-200`} 
        />
      </div>
    </div>
  );
};

export default LanguageNode;