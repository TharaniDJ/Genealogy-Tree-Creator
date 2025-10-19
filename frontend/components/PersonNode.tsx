// /* eslint-disable @next/next/no-img-element */
// import React from 'react';
// import { Handle, Position, NodeProps } from 'reactflow';

// interface PersonNodeData {
//   label: string;
//   entity: string;
//   qid: string;
//   birth_year?: string;
//   death_year?: string;
//   image_url?: string;
//   nodeType: 'entity';
// }

// export default function PersonNode({ data, selected }: NodeProps<PersonNodeData>) {
//   const getInitials = (name: string) => {
//     return name
//       .split(' ')
//       .map(n => n[0])
//       .join('')
//       .toUpperCase()
//       .slice(0, 2);
//   };

//   const formatYears = (birth?: string, death?: string) => {
//     if (birth && death) {
//       return `${birth} - ${death}`;
//     } else if (birth) {
//       return `${birth} - present`;
//     }
//     return '';
//   };

//   return (
//     <div className="person-node">
//       <Handle type="target" position={Position.Top} className="!bg-[#6B72FF] !border-[#6B72FF]" />
      
//       <div className={`w-48 backdrop-blur-xl bg-white/10 border-2 rounded-xl shadow-2xl p-4 text-center transition-all duration-200 ${
//         selected ? 'border-[#6B72FF] shadow-[#6B72FF]/25 shadow-lg' : 'border-white/20 hover:shadow-lg hover:border-white/30'
//       }`}>
//         <div className="w-16 h-16 mx-auto mb-2 rounded-full overflow-hidden bg-white/5 border border-white/20 flex items-center justify-center">
//           {data.image_url ? (
//             <img
//               crossOrigin="anonymous"
//               src={`/api/image-proxy?url=${encodeURIComponent(data.image_url)}`}
//               alt={data.entity}
//               className="w-full h-full object-cover"
//             />
//           ) : (
//             <span className="text-white bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] w-full h-full flex items-center justify-center text-sm font-bold">
//               {getInitials(data.entity)}
//             </span>
//           )}
//         </div>
        
//         <h3 className="font-semibold text-sm mb-1 line-clamp-2 text-[#F5F7FA]">
//           {data.entity}
//         </h3>
        
//         {(data.birth_year || data.death_year) && (
//           <p className="text-xs text-[#9CA3B5]">
//             {formatYears(data.birth_year, data.death_year)}
//           </p>
//         )}
        
//         {data.qid && (
//           <p className="text-xs text-[#9CA3B5]/70 mt-1">
//             {data.qid}
//           </p>
//         )}
//       </div>
      
//       <Handle type="source" position={Position.Bottom} className="!bg-[#6B72FF] !border-[#6B72FF]" />
//     </div>
//   );
// }

/* eslint-disable @next/next/no-img-element */
import React, { useState, useEffect } from 'react';
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
  const [imageData, setImageData] = useState<string | null>(null);
  const [imageError, setImageError] = useState(false);

  useEffect(() => {
    if (data.image_url) {
      // Convert proxy image to base64 for better export compatibility
      fetch(`/api/image-proxy?url=${encodeURIComponent(data.image_url)}`)
        .then(response => response.blob())
        .then(blob => {
          const reader = new FileReader();
          reader.onloadend = () => {
            setImageData(reader.result as string);
          };
          reader.readAsDataURL(blob);
        })
        .catch(() => {
          setImageError(true);
        });
    }
  }, [data.image_url]);

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
      <Handle type="target" position={Position.Top} className="!bg-[#6B72FF] !border-[#6B72FF]" />
      
      <div className={`w-48 backdrop-blur-xl bg-white/10 border-2 rounded-xl shadow-2xl p-4 text-center transition-all duration-200 ${
        selected ? 'border-[#6B72FF] shadow-[#6B72FF]/25 shadow-lg' : 'border-white/20 hover:shadow-lg hover:border-white/30'
      }`}>
        <div className="w-16 h-16 mx-auto mb-2 rounded-full overflow-hidden bg-white/5 border border-white/20 flex items-center justify-center">
          {imageData && !imageError ? (
            <img
              src={imageData}
              alt={data.entity}
              className="w-full h-full object-cover"
              crossOrigin="anonymous"
            />
          ) : (
            <span className="text-white bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] w-full h-full flex items-center justify-center text-sm font-bold">
              {getInitials(data.entity)}
            </span>
          )}
        </div>
        
        <h3 className="font-semibold text-sm mb-1 line-clamp-2 text-[#F5F7FA]">
          {data.entity}
        </h3>
        
        {(data.birth_year || data.death_year) && (
          <p className="text-xs text-[#9CA3B5]">
            {formatYears(data.birth_year, data.death_year)}
          </p>
        )}
        
        {data.qid && (
          <p className="text-xs text-[#9CA3B5]/70 mt-1">
            {data.qid}
          </p>
        )}
      </div>
      
      <Handle type="source" position={Position.Bottom} className="!bg-[#6B72FF] !border-[#6B72FF]" />
    </div>
  );
}