import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  BackgroundVariant,
} from 'reactflow';
import 'reactflow/dist/style.css';

// Simple Language Node Component
const LanguageNode = ({ data }: { data: any }) => {
  return (
    <div className="bg-white border-2 border-blue-500 rounded-lg p-3 min-w-[200px] shadow-lg">
      <div className="font-bold text-blue-800 text-sm mb-1">{data.entity}</div>
      {data.language_family && (
        <div className="text-xs text-gray-600 mb-1">Family: {data.language_family}</div>
      )}
      {data.speakers && (
        <div className="text-xs text-gray-600 mb-1">Speakers: {data.speakers}</div>
      )}
      {data.region && (
        <div className="text-xs text-gray-600 mb-1">Region: {data.region}</div>
      )}
      {data.iso_code && (
        <div className="text-xs text-blue-600 font-mono">ISO: {data.iso_code}</div>
      )}
    </div>
  );
};

const nodeTypes = {
  language: LanguageNode,
};

interface WebSocketMessage {
  type: 'status' | 'language_details' | 'relationship';
  data: any;
}

interface LanguageDetails {
  entity: string;
  qid: string;
  name?: string;
  language_family?: string;
  speakers?: string;
  writing_system?: string;
  iso_code?: string;
  region?: string;
  status?: string;
  image_url?: string;
}

interface Relationship {
  entity1: string;
  relationship: string;
  entity2: string;
}

interface LanguageTreeProps {
  websocketData?: WebSocketMessage[];
}

export default function LanguageTree({ websocketData = [] }: LanguageTreeProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [languageDetails, setLanguageDetails] = useState<Map<string, LanguageDetails>>(new Map());
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('');

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  // Process WebSocket messages
  useEffect(() => {
    if (websocketData.length === 0) return;

    const newLanguageDetails = new Map<string, LanguageDetails>();
    const newRelationships: Relationship[] = [];
    let latestStatus = '';
    let latestProgress = 0;

    websocketData.forEach((message) => {
      switch (message.type) {
        case 'status':
          latestStatus = message.data.message;
          latestProgress = message.data.progress;
          break;
        case 'language_details':
          newLanguageDetails.set(message.data.entity, message.data);
          break;
        case 'relationship':
          newRelationships.push(message.data);
          break;
      }
    });

    setLanguageDetails(newLanguageDetails);
    setRelationships(newRelationships);
    setStatus(latestStatus);
    setProgress(latestProgress);
  }, [websocketData]);

  // Generate graph from relationships and language details
  useEffect(() => {
    if (languageDetails.size === 0 || relationships.length === 0) return;

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    
    // Constants for layout
    const HORIZONTAL_SPACING = 350;
    const VERTICAL_SPACING = 200;
    
    // Categorize relationships
    const familyRelationships = relationships.filter(rel => 
      rel.relationship === 'member of'
    );
    const evolutionRelationships = relationships.filter(rel => 
      rel.relationship === 'evolved from'
    );
    const descendantRelationships = relationships.filter(rel => 
      rel.relationship === 'descendant of'
    );
    const dialectRelationships = relationships.filter(rel => 
      rel.relationship === 'dialect of'
    );
    const siblingRelationships = relationships.filter(rel => 
      rel.relationship === 'sibling of'
    );

    // Calculate hierarchy levels for layout
    const levels = new Map<string, number>();
    const visited = new Set<string>();
    
    // Find root language (most connected or first)
    const languageConnections = new Map<string, number>();
    relationships.forEach(rel => {
      languageConnections.set(rel.entity1, (languageConnections.get(rel.entity1) || 0) + 1);
      languageConnections.set(rel.entity2, (languageConnections.get(rel.entity2) || 0) + 1);
    });
    
    const rootLanguage = Array.from(languageConnections.entries())
      .sort((a, b) => b[1] - a[1])[0]?.[0] || Array.from(languageDetails.keys())[0];
    
    // Assign levels using BFS
    const queue: { language: string; level: number }[] = [{ language: rootLanguage, level: 0 }];
    levels.set(rootLanguage, 0);
    
    while (queue.length > 0) {
      const { language, level } = queue.shift()!;
      if (visited.has(language)) continue;
      visited.add(language);
      
      // Family relationships (upward)
      familyRelationships.forEach(rel => {
        if (rel.entity1 === language && !levels.has(rel.entity2)) {
          levels.set(rel.entity2, level - 1);
          queue.push({ language: rel.entity2, level: level - 1 });
        }
      });

      // Evolution relationships (upward)
      evolutionRelationships.forEach(rel => {
        if (rel.entity1 === language && !levels.has(rel.entity2)) {
          levels.set(rel.entity2, level - 1);
          queue.push({ language: rel.entity2, level: level - 1 });
        }
      });

      // Descendant relationships (downward)
      descendantRelationships.forEach(rel => {
        if (rel.entity2 === language && !levels.has(rel.entity1)) {
          levels.set(rel.entity1, level + 1);
          queue.push({ language: rel.entity1, level: level + 1 });
        }
      });

      // Dialect relationships (downward)
      dialectRelationships.forEach(rel => {
        if (rel.entity2 === language && !levels.has(rel.entity1)) {
          levels.set(rel.entity1, level + 1);
          queue.push({ language: rel.entity1, level: level + 1 });
        }
      });
    }

    // Assign levels to remaining languages
    Array.from(languageDetails.keys()).forEach(language => {
      if (!levels.has(language)) {
        levels.set(language, 0);
      }
    });

    // Group languages by level
    const levelGroups = new Map<number, string[]>();
    Array.from(levels.entries()).forEach(([language, level]) => {
      if (!levelGroups.has(level)) {
        levelGroups.set(level, []);
      }
      levelGroups.get(level)!.push(language);
    });

    // Create nodes with improved positioning
    Array.from(levelGroups.entries())
      .sort(([a], [b]) => a - b)
      .forEach(([level, languages]) => {
        const y = level * VERTICAL_SPACING + 300;
        const totalWidth = languages.length * HORIZONTAL_SPACING;
        let startX = -totalWidth / 2;

        languages.forEach((language, index) => {
          const details = languageDetails.get(language);
          if (!details) return;

          const x = startX + index * HORIZONTAL_SPACING;

          newNodes.push({
            id: language,
            type: 'language',
            position: { x, y },
            data: {
              label: details.entity,
              entity: details.entity,
              qid: details.qid,
              name: details.name,
              language_family: details.language_family,
              speakers: details.speakers,
              writing_system: details.writing_system,
              iso_code: details.iso_code,
              region: details.region,
              status: details.status,
              image_url: details.image_url,
            },
          });
        });
      });

    // Create edges for different relationship types
    const createEdges = (rels: Relationship[], color: string, label: string) => {
      rels.forEach((rel, index) => {
        if (languageDetails.has(rel.entity1) && languageDetails.has(rel.entity2)) {
          newEdges.push({
            id: `${rel.relationship}-${index}`,
            source: rel.entity1,
            target: rel.entity2,
            type: 'smoothstep',
            label: label,
            style: {
              stroke: color,
              strokeWidth: 2,
            },
            labelStyle: {
              fontSize: 12,
              fontWeight: 'bold',
            },
          });
        }
      });
    };

    // Create edges with different colors for different relationship types
    createEdges(familyRelationships, '#8b5cf6', 'member of');
    createEdges(evolutionRelationships, '#f59e0b', 'evolved from');
    createEdges(descendantRelationships, '#10b981', 'descendant of');
    createEdges(dialectRelationships, '#3b82f6', 'dialect of');
    createEdges(siblingRelationships, '#ec4899', 'sibling of');

    setNodes(newNodes);
    setEdges(newEdges);
  }, [languageDetails, relationships, setNodes, setEdges]);

  const getRelationshipCounts = () => {
    return {
      family: relationships.filter(r => r.relationship === 'member of').length,
      evolution: relationships.filter(r => r.relationship === 'evolved from').length,
      descendant: relationships.filter(r => r.relationship === 'descendant of').length,
      dialect: relationships.filter(r => r.relationship === 'dialect of').length,
      sibling: relationships.filter(r => r.relationship === 'sibling of').length,
    };
  };

  const counts = getRelationshipCounts();

  return (
    <div className="w-full h-screen">
      <div className="absolute top-4 left-4 z-10 bg-white p-4 rounded-lg shadow-md max-w-md">
        <h2 className="text-lg font-bold mb-2">Language Tree Generator</h2>
        {status && (
          <div className="mb-2">
            <p className="text-sm text-gray-600">{status}</p>
            <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                style={{ width: `${progress}%` }}
              ></div>
            </div>
          </div>
        )}
        <div className="text-sm text-gray-500 space-y-1">
          <p>Languages: {languageDetails.size}</p>
          <p>Total Relationships: {relationships.length}</p>
          <p>Family: {counts.family}</p>
          <p>Evolution: {counts.evolution}</p>
          <p>Descendants: {counts.descendant}</p>
          <p>Dialects: {counts.dialect}</p>
          <p>Siblings: {counts.sibling}</p>
        </div>
        <div className="mt-2 text-xs text-gray-400 space-y-1">
          <p>🟣 Purple: Family membership</p>
          <p>🟡 Orange: Evolution</p>
          <p>🟢 Green: Descendants</p>
          <p>🔵 Blue: Dialects</p>
          <p>🟣 Pink: Siblings</p>
        </div>
      </div>
      
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
      >
        <Controls />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>
    </div>
  );
}
