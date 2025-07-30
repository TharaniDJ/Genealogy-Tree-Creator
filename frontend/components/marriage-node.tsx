import { NodeData } from "@/lib/types";
import {
  Handle,
  Position,
} from 'reactflow';

export default function MarriageNode({ data }: { data: NodeData }) {
  return (
    <div className="marriage-content">
      <Handle
        id="left"
        type="target"
        position={Position.Left}
        style={{
          visibility: 'hidden',
        }}
      />
      <Handle
        id="right"
        type="target"
        position={Position.Right}
        style={{
          visibility: 'hidden',
        }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{
         visibility: 'hidden',
        }}
      />
    </div>
  );
};
