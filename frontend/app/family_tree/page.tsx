'use client';
import React, { useState, useEffect, useCallback } from 'react';
import GenealogyTree from '@/components/GenealogyTree';
import { useWebSocket } from '@/hooks/useWebSocket';
import useAuth from '@/hooks/useAuth';
import AuthGuard from '@/components/AuthGuard';

function FamilyTreePage() {
  const { getToken } = useAuth();
  
  // WebSocket connection for real-time data through API Gateway
  const wsBase = process.env.NEXT_PUBLIC_FAMILY_API_URL || 'http://localhost:8080/api/family';
  const wsUrl = wsBase.replace(/^http/, 'ws') + '/ws';
  
  const { 
    messages: websocketData, 
    connectionStatus, 
    connect, 
    disconnect, 
    clearMessages,
    sendMessage 
  } = useWebSocket(wsUrl, { token: getToken() });

  const [searchQuery, setSearchQuery] = useState('Albert Einstein');
  const [searchDepth, setSearchDepth] = useState(2);

  // Function to start genealogy search
  const startGenealogySearch = () => {
    if (connectionStatus === 'connected' && searchQuery.trim()) {
      // Convert search query to Wikipedia page title format (replace spaces with underscores)
      const pageTitle = searchQuery.trim().replace(/\s+/g, '_');
      
      // Send search request to backend in the required format
      sendMessage({
        action: "fetch_relationships",
        page_title: pageTitle,
        depth: searchDepth
      });
    }
  };

  // Handle expand node functionality (for initial name-based searches)
  const handleExpandNode = useCallback((personName: string, depth: number) => {
    if (connectionStatus === 'connected') {
      sendMessage({
        action: "fetch_relationships",
        page_title: personName,
        depth: depth
      });
    }
  }, [connectionStatus, sendMessage]);

  // NEW: Handle QID-based expansion (for node expansion)
  const handleExpandNodeByQid = useCallback((qid: string, depth: number, entityName?: string) => {
    if (connectionStatus !== 'connected') {
      console.error('WebSocket not connected');
      return;
    }

    try {
      console.log(`Sending QID expansion request: ${qid}, depth: ${depth}, entity: ${entityName}`);
      
      // Send QID expansion request to backend
      sendMessage({
        action: "expand_by_qid",
        qid: qid,
        depth: depth,
        entity_name: entityName
      });
      
    } catch (error) {
      console.error('Error sending QID expansion request:', error);
    }
  }, [connectionStatus, sendMessage]);

  // Add this handler in page.tsx, after handleExpandNodeByQid
const handleClassifyRelationships = useCallback((relationships: any[]) => {
  if (connectionStatus !== 'connected') {
    console.error('WebSocket not connected');
    return;
  }

  try {
    console.log(`Sending classification request for ${relationships.length} relationships`);
    
    sendMessage({
      action: "classify_relationships",
      relationships: relationships
    });
    
  } catch (error) {
    console.error('Error sending classification request:', error);
  }
}, [connectionStatus, sendMessage]);
  // Auto-connect on component mount
  useEffect(() => {
    connect();
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-600';
      case 'connecting': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'connecting': return 'Connecting...';
      case 'error': return 'Connection Error';
      default: return 'Disconnected';
    }
  };

  return (
    <main className="w-full h-screen overflow-hidden relative bg-[#0E0F19]">
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 -left-48 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob"></div>
        <div className="absolute top-1/3 -right-48 w-96 h-96 bg-[#8B7BFF] rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-32 left-1/3 w-96 h-96 bg-[#6B72FF] rounded-full mix-blend-multiply filter blur-3xl opacity-10 animate-blob animation-delay-4000"></div>
      </div>

      {/* Control Panel - Fixed position */}
      <div className="absolute top-4 right-4 z-20 backdrop-blur-xl bg-white/5 border border-white/10 p-6 rounded-2xl shadow-2xl max-w-sm">
        <h1 className="text-xl font-bold mb-4 text-[#F5F7FA]">Family Tree Explorer</h1>
        
        {/* Connection Status */}
        <div className="mb-4 p-3 backdrop-blur-md bg-white/5 border border-white/10 rounded-lg">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[#9CA3B5]">WebSocket Status:</span>
            <span className={getConnectionStatusColor()}>
              {getConnectionStatusText()}
            </span>
          </div>
        </div>

        {/* Search Input */}
        <div className="mb-4">
          <label htmlFor="search" className="block text-sm font-medium text-[#9CA3B5] mb-2">
            Search Person
          </label>
          <input
            id="search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter person's name (e.g., Albert Einstein)"
            className="w-full px-4 py-2.5 backdrop-blur-md bg-white/5 border border-white/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#6B72FF] focus:border-transparent text-[#F5F7FA] placeholder-[#9CA3B5]/50"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                startGenealogySearch();
              }
            }}
          />
        </div>

        {/* Depth Control */}
        <div className="mb-4">
          <label htmlFor="depth" className="block text-sm font-medium text-[#9CA3B5] mb-2">
            Search Depth: {searchDepth}
          </label>
          <input
            id="depth"
            type="range"
            min="1"
            max="4"
            value={searchDepth}
            onChange={(e) => setSearchDepth(parseInt(e.target.value))}
            className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-[#6B72FF]"
          />
          <div className="flex justify-between text-xs text-[#9CA3B5] mt-1">
            <span>1 (Close)</span>
            <span>4 (Extended)</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2">
          <button
            onClick={startGenealogySearch}
            disabled={connectionStatus !== 'connected' || !searchQuery.trim()}
            className="w-full px-4 py-2.5 bg-gradient-to-r from-[#6B72FF] to-[#8B7BFF] text-white rounded-lg hover:shadow-lg hover:shadow-[#6B72FF]/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            Search Genealogy Tree
          </button>

          <button
            onClick={() => {
              if (connectionStatus === 'connected') {
                sendMessage({
                  action: "fetch_relationships",
                  page_title: "Albert_Einstein",
                  depth: 2
                });
              }
            }}
            disabled={connectionStatus !== 'connected'}
            className="w-full px-4 py-2.5 backdrop-blur-md bg-[#8B7BFF]/20 border border-[#8B7BFF]/30 text-[#F5F7FA] rounded-lg hover:bg-[#8B7BFF]/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Test Albert Einstein
          </button>
          
          <button
            onClick={connect}
            disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}
            className="w-full px-4 py-2.5 backdrop-blur-md bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 rounded-lg hover:bg-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Connect to Server
          </button>
          
          <button
            onClick={disconnect}
            disabled={connectionStatus === 'disconnected'}
            className="w-full px-4 py-2.5 backdrop-blur-md bg-orange-500/20 border border-orange-500/30 text-orange-400 rounded-lg hover:bg-orange-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Disconnect
          </button>
          
          <button
            onClick={clearMessages}
            className="w-full px-4 py-2.5 backdrop-blur-md bg-red-500/20 border border-red-500/30 text-red-400 rounded-lg hover:bg-red-500/30 transition-all"
          >
            Clear Tree Data
          </button>
        </div>

        {/* Data Statistics */}
        <div className="mt-4 text-sm text-[#9CA3B5] backdrop-blur-md bg-white/5 border border-white/10 p-3 rounded-lg">
          <p>Messages received: {websocketData.length}</p>
          <p>People: {websocketData.filter(m => m.type === 'personal_details').length}</p>
          <p>Relationships: {websocketData.filter(m => m.type === 'relationship').length}</p>
          <p className="text-[#8B7BFF] font-medium">QID-based expansion enabled</p>
        </div>

        {/* Recent Messages (Debug) */}
        {websocketData.length > 0 && (
          <div className="mt-4 text-xs text-[#9CA3B5] backdrop-blur-md bg-white/5 border border-white/10 p-3 rounded-lg max-h-32 overflow-y-auto">
            <p className="font-semibold mb-2 text-[#F5F7FA]">Recent Messages:</p>
            {websocketData.slice(-3).map((msg, index) => (
              <div key={index} className="mb-2 p-2 backdrop-blur-sm bg-white/5 border border-white/10 rounded text-xs">
                <span className="font-medium text-[#6B72FF]">{msg.type}:</span> <span className="text-[#9CA3B5]">{JSON.stringify(msg.data).slice(0, 50)}...</span>
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Genealogy Tree - Takes full screen with BOTH expansion handlers */}
      <GenealogyTree 
        websocketData={websocketData} 
        onExpandNode={handleExpandNode}          // For initial name-based searches
        onExpandNodeByQid={handleExpandNodeByQid} // For QID-based node expansion
        onClassifyRelationships={handleClassifyRelationships}  // ADD THIS LINE
        expandDepth={2}                          // Default expansion depth for nodes
      />
    </main>
  );
}

// Wrap with AuthGuard for authentication
export default function ProtectedFamilyTree() {
  return (
    <AuthGuard>
      <FamilyTreePage />
    </AuthGuard>
  );
}