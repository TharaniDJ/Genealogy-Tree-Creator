import { NodeData } from "@/lib/types";
import {
  Handle,
  Position,
} from 'reactflow';

export default function PersonNode({ data }: { data: NodeData }) {
  const { personData } = data;
  
  return (
    <div className="knowledge-node person-node">
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
      />
      <div className="node-content flex items-center justify-center p-3">
        <div className="flex items-center gap-3">
          {personData?.image && (
            <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-white/30 flex-shrink-0">
              <img 
                src={personData.image} 
                alt={data.label}
                className="w-full h-full object-cover"
              />
            </div>
          )}
          <div className="flex flex-col">
            <div className="text-sm font-bold mb-1">
              {personData?.name || data.label}
            </div>
            {personData && (
              <div className="text-xs opacity-90">
                <div className="birth-death">
                  {personData.birthYear}
                  {personData.deathYear && ` - ${personData.deathYear}`}
                  {!personData.deathYear && ' - Present'}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
      />
    </div>
  );
};
