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

  // Color scheme based on taxonomic rank
  const getColorForRank = (rank?: string): { bg: string; border: string; text: string } => {
    if (!rank) return { bg: 'bg-gray-100', border: 'border-gray-300', text: 'text-gray-800' };
    
    const colors: Record<string, { bg: string; border: string; text: string }> = {
      'domain': { bg: 'bg-purple-100', border: 'border-purple-400', text: 'text-purple-900' },
      'kingdom': { bg: 'bg-red-100', border: 'border-red-400', text: 'text-red-900' },
      'phylum': { bg: 'bg-orange-100', border: 'border-orange-400', text: 'text-orange-900' },
      'class': { bg: 'bg-yellow-100', border: 'border-yellow-400', text: 'text-yellow-900' },
      'order': { bg: 'bg-green-100', border: 'border-green-400', text: 'text-green-900' },
      'family': { bg: 'bg-blue-100', border: 'border-blue-400', text: 'text-blue-900' },
      'genus': { bg: 'bg-indigo-100', border: 'border-indigo-400', text: 'text-indigo-900' },
      'species': { bg: 'bg-pink-100', border: 'border-pink-400', text: 'text-pink-900' },
    };
    
    return colors[rank.toLowerCase()] || { bg: 'bg-gray-100', border: 'border-gray-300', text: 'text-gray-800' };
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
    <>
      <Handle type="target" position={Position.Top} />
      <div
        className={`
          px-3 py-2 rounded-lg border-2 min-w-[180px] cursor-pointer transition-all
          ${colors.bg} ${colors.border} ${colors.text}
          ${selected ? 'ring-2 ring-blue-400 ring-opacity-50' : ''}
          hover:shadow-md hover:scale-105
          ${onExpand ? 'hover:bg-opacity-80' : ''}
        `}
        onClick={handleClick}
        title={`${label}${rank ? ` (${rank})` : ''}${scientificName ? ` - ${scientificName}` : ''}`}
      >
        {/* Rank badge */}
        {rank && (
          <div className={`
            text-xs px-2 py-0.5 rounded-full mb-1 inline-block
            ${colors.border} border bg-white bg-opacity-70
          `}>
            {rank.charAt(0).toUpperCase() + rank.slice(1)}
          </div>
        )}
        
        {/* Main label with Wikipedia button */}
        <div className="flex items-center justify-between gap-2">
          <div className={`font-semibold text-sm ${colors.text} flex-1`}>
            {formatLabel(label)}
          </div>
          
          {/* Wikipedia button */}
          <button
            onClick={handleWikipediaClick}
            className={`
              text-xs px-1.5 py-0.5 rounded border transition-colors
              ${colors.border} ${colors.text} 
              hover:bg-white hover:bg-opacity-80 hover:shadow-sm
              focus:outline-none focus:ring-1 focus:ring-blue-300
            `}
            title={`View ${label} on Wikipedia`}
            aria-label={`View ${label} on Wikipedia`}
          >
            📖
          </button>
        </div>
        
        {/* Scientific name for species */}
        {isSpecies && scientificName && scientificName !== label && (
          <div className={`text-xs italic ${colors.text} opacity-75 mt-0.5`}>
            {formatLabel(scientificName)}
          </div>
        )}
        
        {/* Expand indicator */}
        {onExpand && (
          <div className={`text-xs ${colors.text} opacity-60 mt-0.5`}>
            Click to expand →
          </div>
        )}
      </div>
      <Handle type="source" position={Position.Bottom} />
    </>
  );
};

export default memo(TaxonomyNode);