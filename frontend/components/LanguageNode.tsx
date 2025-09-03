"use client";

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';

// Simple styled language node with explicit handles to avoid edge creation errors.
const LanguageNode: React.FC<NodeProps> = ({ data }) => {
  return (
    <div style={{
      padding: '6px 8px',
      border: '1px solid #ccc',
      borderRadius: 4,
      background: '#fff',
      fontSize: 12,
      minWidth: 140,
      textAlign: 'center',
      boxShadow: '0 1px 2px rgba(0,0,0,0.1)'
    }}>
      <Handle type="target" position={Position.Top} style={{ background: '#555' }} />
      <div style={{ fontWeight: 600 }}>{data.label}</div>
      {data.meta && (
        <div style={{ marginTop: 2, opacity: 0.7 }}>{data.meta}</div>
      )}
      <Handle type="source" position={Position.Bottom} style={{ background: '#007bff' }} />
    </div>
  );
};

export default LanguageNode;