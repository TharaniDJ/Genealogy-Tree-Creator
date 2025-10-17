import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

type TaxonomyNodeData = {
  label: string;
  rank?: string;
  scientificName?: string;
  onExpand?: () => void;
};

const TaxonomyNode: React.FC<NodeProps<TaxonomyNodeData>> = ({ data, selected }) => {
  const { label, rank, scientificName, onExpand } = data;

  // Dark glassmorphic color scheme based on taxonomic rank with vivid colored accents
  const getColorForRank = (rank?: string): { bg: string; border: string; text: string; glow: string; shadow: string } => {
    if (!rank) return { 
      bg: 'bg-white/5', 
      border: 'border-gray-400', 
      text: 'text-gray-300', 
      glow: 'from-gray-400 to-gray-500',
      shadow: 'shadow-gray-500/20'
    };
    
    const colors: Record<string, { bg: string; border: string; text: string; glow: string; shadow: string }> = {
      'domain': { bg: 'bg-white/5', border: 'border-purple-500', text: 'text-purple-200', glow: 'from-purple-500 to-purple-600', shadow: 'shadow-purple-500/30' },
      'kingdom': { bg: 'bg-white/5', border: 'border-red-500', text: 'text-red-200', glow: 'from-red-500 to-red-600', shadow: 'shadow-red-500/30' },
      'phylum': { bg: 'bg-white/5', border: 'border-orange-500', text: 'text-orange-200', glow: 'from-orange-500 to-orange-600', shadow: 'shadow-orange-500/30' },
      'class': { bg: 'bg-white/5', border: 'border-yellow-500', text: 'text-yellow-200', glow: 'from-yellow-500 to-yellow-600', shadow: 'shadow-yellow-500/30' },
      'order': { bg: 'bg-white/5', border: 'border-green-500', text: 'text-green-200', glow: 'from-green-500 to-green-600', shadow: 'shadow-green-500/30' },
      'family': { bg: 'bg-white/5', border: 'border-blue-500', text: 'text-blue-200', glow: 'from-blue-500 to-blue-600', shadow: 'shadow-blue-500/30' },
      'genus': { bg: 'bg-white/5', border: 'border-indigo-500', text: 'text-indigo-200', glow: 'from-indigo-500 to-indigo-600', shadow: 'shadow-indigo-500/30' },
      'species': { bg: 'bg-white/5', border: 'border-pink-500', text: 'text-pink-200', glow: 'from-pink-500 to-pink-600', shadow: 'shadow-pink-500/30' },
    };
    
    return colors[rank.toLowerCase()] || { 
      bg: 'bg-white/5', 
      border: 'border-gray-400', 
      text: 'text-gray-300', 
      glow: 'from-gray-400 to-gray-500',
      shadow: 'shadow-gray-500/20'
    };
  };

  const colors = getColorForRank(rank);
  
  const handleClick = () => {
    if (onExpand) {
      onExpand();
    }
  };

  const handleWikipediaClick = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent triggering the expand action
    const wikipediaUrl = `https://en.wikipedia.org/wiki/${encodeURIComponent(label)}`;
    window.open(wikipediaUrl, '_blank', 'noopener,noreferrer');
  };

  const formatLabel = (label: string) => {
    // Truncate long names
    if (label.length > 20) {
      return label.substring(0, 17) + '...';
    }
    return label;
  };

  const isSpecies = rank?.toLowerCase() === 'species' || scientificName;

  return (
    <div className="relative group">
      {/* Enhanced glow effect on hover */}
      <div className={`absolute -inset-1 bg-gradient-to-r ${colors.glow} rounded-2xl blur-md opacity-0 group-hover:opacity-70 transition-opacity duration-300`}></div>
      
      <Handle type="target" position={Position.Left} className="!w-3 !h-3 !bg-gradient-to-r !from-[#6B72FF] !to-[#8B7BFF] !border-2 !border-white/20 !shadow-lg hover:!scale-125 !transition-transform !duration-200" />
      
      <div
        className={`
          relative px-4 py-2.5 rounded-xl border-2 min-w-[180px] cursor-pointer transition-all backdrop-blur-xl
          ${colors.bg} ${colors.border} ${colors.text}
          ${selected ? 'ring-4 ring-[#6B72FF] ring-opacity-50 shadow-xl ' + colors.shadow : 'shadow-lg ' + colors.shadow}
          hover:shadow-2xl hover:scale-105 hover:border-opacity-100
          ${onExpand ? 'hover:bg-white/10' : ''}
        `}
        onClick={handleClick}
        title={`${label}${rank ? ` (${rank})` : ''}${scientificName ? ` - ${scientificName}` : ''}`}
      >
        {/* Rank badge with dark glassmorphic style */}
        {rank && (
          <div className={`
            text-xs px-2.5 py-1 rounded-full mb-2 inline-block font-bold
            ${colors.border} border-2 backdrop-blur-xl bg-black/20 shadow-lg
            ${colors.text}
          `}>
            {rank.charAt(0).toUpperCase() + rank.slice(1)}
          </div>
        )}
        
        {/* Main label with Wikipedia button */}
        <div className="flex items-center justify-between gap-2">
          <div className={`font-bold text-sm ${colors.text} flex-1 drop-shadow-md`}>
            {formatLabel(label)}
          </div>
          
          {/* Wikipedia button with dark theme */}
          <button
            onClick={handleWikipediaClick}
            className={`
              text-sm px-2.5 py-1.5 rounded-lg border-2 transition-all backdrop-blur-xl
              ${colors.border} ${colors.text} bg-black/20
              hover:bg-gradient-to-r hover:${colors.glow} hover:text-white hover:shadow-lg hover:scale-110
              focus:outline-none focus:ring-2 focus:ring-[#6B72FF]
            `}
            title={`View ${label} on Wikipedia`}
            aria-label={`View ${label} on Wikipedia`}
          >
            📖
          </button>
        </div>
        
        {/* Scientific name for species */}
        {isSpecies && scientificName && scientificName !== label && (
          <div className={`text-xs italic ${colors.text} opacity-80 mt-1.5 font-medium drop-shadow-sm`}>
            {formatLabel(scientificName)}
          </div>
        )}
        
        {/* Expand indicator */}
        {onExpand && (
          <div className={`text-xs ${colors.text} opacity-70 mt-1.5 font-medium drop-shadow-sm flex items-center gap-1`}>
            <span>Click to expand</span>
            <span className="inline-block animate-pulse">→</span>
          </div>
        )}
      </div>
      
      <Handle type="source" position={Position.Right} className="!w-3 !h-3 !bg-gradient-to-r !from-[#6B72FF] !to-[#8B7BFF] !border-2 !border-white/20 !shadow-lg hover:!scale-125 !transition-transform !duration-200" />
    </div>
  );
};

export default memo(TaxonomyNode);