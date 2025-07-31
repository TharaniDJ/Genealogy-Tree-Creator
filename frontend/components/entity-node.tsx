import { NodeData } from "@/lib/types";
import {
  Handle,
  Position,
} from 'reactflow';

export default function EntityNode({ data }: { data: NodeData }) {
  const { entityData } = data;
  
  if (!entityData) {
    return (
      <div className="knowledge-node entity-node">
        <div className="node-content flex items-center justify-center p-3">
          <div className="text-sm font-bold">{data.label}</div>
        </div>
      </div>
    );
  }

  // Render different entity types
  const renderEntityContent = () => {
    switch (entityData.type) {
      case 'person':
        return (
          <div className="flex items-center gap-3">
            {entityData.data.image && (
              <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-white/30 flex-shrink-0">
                <img 
                  src={entityData.data.image} 
                  alt={entityData.label}
                  className="w-full h-full object-cover"
                />
              </div>
            )}
            <div className="flex flex-col">
              <div className="text-sm font-bold mb-1">
                {entityData.data.name || entityData.label}
              </div>
              {(entityData.data.birthYear || entityData.data.description) && (
                <div className="text-xs opacity-90">
                  {entityData.data.birthYear && (
                    <div className="birth-death">
                      {entityData.data.birthYear}
                      {entityData.data.deathYear && ` - ${entityData.data.deathYear}`}
                      {!entityData.data.deathYear && entityData.data.birthYear && ' - Present'}
                    </div>
                  )}
                  {entityData.data.description && (
                    <div className="description mt-1 text-xs">
                      {entityData.data.description.length > 50 
                        ? `${entityData.data.description.substring(0, 50)}...`
                        : entityData.data.description}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        );

      case 'company':
        return (
          <div className="flex items-center gap-3">
            {entityData.data.logo && (
              <div className="w-12 h-12 rounded-lg overflow-hidden border-2 border-white/30 flex-shrink-0">
                <img 
                  src={entityData.data.logo} 
                  alt={entityData.label}
                  className="w-full h-full object-cover"
                />
              </div>
            )}
            <div className="flex flex-col">
              <div className="text-sm font-bold mb-1">
                {entityData.data.name || entityData.label}
              </div>
              <div className="text-xs opacity-90">
                {entityData.data.industry && (
                  <div className="industry">{entityData.data.industry}</div>
                )}
                {entityData.data.founded && (
                  <div className="founded">Founded: {entityData.data.founded}</div>
                )}
              </div>
            </div>
          </div>
        );

      case 'event':
        return (
          <div className="flex flex-col">
            <div className="text-sm font-bold mb-1">{entityData.label}</div>
            <div className="text-xs opacity-90">
              {entityData.data.date && (
                <div className="date">{entityData.data.date}</div>
              )}
              {entityData.data.location && (
                <div className="location">{entityData.data.location}</div>
              )}
              {entityData.data.description && (
                <div className="description mt-1">
                  {entityData.data.description.length > 60 
                    ? `${entityData.data.description.substring(0, 60)}...`
                    : entityData.data.description}
                </div>
              )}
            </div>
          </div>
        );

      case 'location':
        return (
          <div className="flex flex-col">
            <div className="text-sm font-bold mb-1">{entityData.label}</div>
            <div className="text-xs opacity-90">
              {entityData.data.type && (
                <div className="location-type">{entityData.data.type}</div>
              )}
              {entityData.data.country && (
                <div className="country">{entityData.data.country}</div>
              )}
              {entityData.data.coordinates && (
                <div className="coordinates text-xs">
                  {entityData.data.coordinates.lat}, {entityData.data.coordinates.lng}
                </div>
              )}
            </div>
          </div>
        );

      default:
        return (
          <div className="flex flex-col">
            <div className="text-sm font-bold mb-1">{entityData.label}</div>
            {entityData.data.description && (
              <div className="text-xs opacity-90">
                {entityData.data.description.length > 80 
                  ? `${entityData.data.description.substring(0, 80)}...`
                  : entityData.data.description}
              </div>
            )}
            {entityData.data.value && (
              <div className="text-xs opacity-90 mt-1">
                Value: {entityData.data.value}
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="knowledge-node entity-node">
      <Handle
        type="target"
        position={Position.Top}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
      />
      <div className="node-content flex items-center justify-center p-3">
        {renderEntityContent()}
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
      />
      
      {/* Additional handles for better connectivity */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
        id="left"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-2 h-2 bg-gray-600 border-2 border-white"
        id="right"
      />
    </div>
  );
}
