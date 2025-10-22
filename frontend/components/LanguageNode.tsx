"use client";

import React, { useMemo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

// Category -> palette mapping for dark theme with blue/purple accents
const CATEGORY_STYLES: Record<string, { from: string; to: string; ring: string; glow: string; bg: string }> = {
  language: { 
    from: 'from-[#6B72FF]', 
    to: 'to-[#8B7BFF]', 
    ring: 'ring-[#6B72FF]/30', 
    glow: 'from-[#6B72FF] via-[#8B7BFF] to-[#9B8BFF]',
    bg: 'bg-[#1A1D2D]/90'
  },
  dialect: { 
    from: 'from-[#8B7BFF]', 
    to: 'to-[#9B8BFF]', 
    ring: 'ring-[#8B7BFF]/30', 
    glow: 'from-[#8B7BFF] via-[#9B8BFF] to-[#AB9BFF]',
    bg: 'bg-[#1A1D2D]/90'
  },
  language_family: { 
    from: 'from-[#5B62FF]', 
    to: 'to-[#7B72FF]', 
    ring: 'ring-[#5B62FF]/30', 
    glow: 'from-[#5B62FF] via-[#7B72FF] to-[#8B82FF]',
    bg: 'bg-[#1A1D2D]/90'
  },
  proto_language: { 
    from: 'from-[#4B52EF]', 
    to: 'to-[#6B62FF]', 
    ring: 'ring-[#4B52EF]/30', 
    glow: 'from-[#4B52EF] via-[#6B62FF] to-[#7B72FF]',
    bg: 'bg-[#1A1D2D]/90'
  },
  extinct_language: { 
    from: 'from-[#9B8BFF]', 
    to: 'to-[#AB9BFF]', 
    ring: 'ring-[#9B8BFF]/30', 
    glow: 'from-[#9B8BFF] via-[#AB9BFF] to-[#BBAEFF]',
    bg: 'bg-[#1A1D2D]/90'
  },
  dead_language: { 
    from: 'from-[#7B82FF]', 
    to: 'to-[#8B92FF]', 
    ring: 'ring-[#7B82FF]/30', 
    glow: 'from-[#7B82FF] via-[#8B92FF] to-[#9BA2FF]',
    bg: 'bg-[#1A1D2D]/90'
  },
  sign_language: {
    from: 'from-[#10B981]',
    to: 'to-[#34D399]',
    ring: 'ring-[#10B981]/30',
    glow: 'from-[#10B981] via-[#34D399] to-[#6EE7B7]',
    bg: 'bg-[#0f1b17]/90'
  },
  creole_language: {
    from: 'from-[#F59E0B]',
    to: 'to-[#FBBF24]',
    ring: 'ring-[#F59E0B]/30',
    glow: 'from-[#F59E0B] via-[#FBBF24] to-[#FCD34D]',
    bg: 'bg-[#1b160e]/90'
  },
  pidgin_language: {
    from: 'from-[#EC4899]',
    to: 'to-[#F472B6]',
    ring: 'ring-[#EC4899]/30',
    glow: 'from-[#EC4899] via-[#F472B6] to-[#FDA4AF]',
    bg: 'bg-[#1b0f16]/90'
  },
  modern_language: {
    from: 'from-[#3B82F6]',
    to: 'to-[#60A5FA]',
    ring: 'ring-[#3B82F6]/30',
    glow: 'from-[#3B82F6] via-[#60A5FA] to-[#93C5FD]',
    bg: 'bg-[#0f172a]/90'
  },
  historical_language: {
    from: 'from-[#8B5CF6]',
    to: 'to-[#A78BFA]',
    ring: 'ring-[#8B5CF6]/30',
    glow: 'from-[#8B5CF6] via-[#A78BFA] to-[#C4B5FD]',
    bg: 'bg-[#151225]/90'
  },
  ancient_language: {
    from: 'from-[#F97316]',
    to: 'to-[#FB923C]',
    ring: 'ring-[#F97316]/30',
    glow: 'from-[#F97316] via-[#FB923C] to-[#FDBA74]',
    bg: 'bg-[#1f1410]/90'
  },
  unresolved: {
    from: 'from-[#EF4444]',
    to: 'to-[#F87171]',
    ring: 'ring-[#EF4444]/40',
    glow: 'from-[#EF4444] via-[#F87171] to-[#FCA5A5]',
    bg: 'bg-[#1a1010]/90'
  },
};

type LanguageNodeData = { label: string; meta?: string; category?: string; qid?: string; types?: string[]; onExpand?: () => void };

// Modern styled language node with glassmorphism design for dark theme
const LanguageNode: React.FC<NodeProps<LanguageNodeData>> = ({ data }) => {
  const style = useMemo(() => CATEGORY_STYLES[data.category as string] || CATEGORY_STYLES.language, [data.category]);
  return (
    <div className="relative group">
      {/* Enhanced glow effect on hover */}
      <div className={`absolute -inset-1 bg-gradient-to-r ${style.glow} rounded-2xl blur-sm opacity-0 group-hover:opacity-40 transition-opacity duration-300`}></div>
      
      {/* Main node container with dark theme */}
      <div className={`relative ${style.bg} backdrop-blur-xl border border-white/10 rounded-xl shadow-lg hover:shadow-2xl transition-all duration-300 min-w-[160px] group-hover:scale-105 ring-2 ${style.ring}`}>
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