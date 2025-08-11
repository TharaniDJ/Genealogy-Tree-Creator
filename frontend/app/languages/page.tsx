'use client';

import React, { useState, useEffect } from 'react';
import LanguageTree from '@/components/LanguageTree';
import { useWebSocket } from '@/hooks/useWebSocket';

// Define language-specific message types
interface LanguageWebSocketMessage {
  type: 'status' | 'language_details' | 'relationship';
  data: any;
}

export default function LanguagesPage() {
  // WebSocket connection for real-time data (connecting to language service on port 8001)
  const { 
    messages: rawWebsocketData, 
    connectionStatus, 
    connect, 
    disconnect, 
    clearMessages,
    sendMessage 
  } = useWebSocket('ws://localhost:8001/ws/relationships');

  const [searchQuery, setSearchQuery] = useState('English');
  const [searchDepth, setSearchDepth] = useState(2);

  // Transform the raw websocket data to language format
  const websocketData: LanguageWebSocketMessage[] = rawWebsocketData.map(msg => {
    // Convert 'personal_details' to 'language_details' for language context
    if (msg.type === 'personal_details') {
      return {
        type: 'language_details' as const,
        data: msg.data
      };
    }
    return msg as LanguageWebSocketMessage;
  });

  // Function to start language search
  const startLanguageSearch = () => {
    if (connectionStatus === 'connected' && searchQuery.trim()) {
        const language = searchQuery.trim();
        const depth = searchDepth;
      // Send search request to backend for language relationships
      sendMessage({

        language,
        depth
      });
    }
  };

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
    <main className="min-h-screen bg-gray-50 overflow-y-auto">
      <div className="absolute top-4 right-4 z-20 bg-white p-4 rounded-lg shadow-md max-w-sm">
        <h1 className="text-xl font-bold mb-4">Language Tree Creator</h1>
        
        {/* Navigation Links */}
        <div className="mb-4 flex space-x-2">
          <a 
            href="/" 
            className="px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm font-medium hover:bg-blue-200"
          >
            People
          </a>
          <a 
            href="/languages" 
            className="px-3 py-1 bg-purple-100 text-purple-700 rounded text-sm font-medium"
          >
            Languages
          </a>
        </div>
        
        {/* Connection Status */}
        <div className="mb-4 p-2 bg-gray-50 rounded">
          <div className="flex items-center justify-between text-sm">
            <span>WebSocket Status:</span>
            <span className={getConnectionStatusColor()}>
              {getConnectionStatusText()}
            </span>
          </div>
        </div>

        {/* Search Input */}
        <div className="mb-4">
          <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
            Search Language
          </label>
          <input
            id="search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter language name (e.g., English, Spanish)"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                startLanguageSearch();
              }
            }}
          />
        </div>

        {/* Depth Control */}
        <div className="mb-4">
          <label htmlFor="depth" className="block text-sm font-medium text-gray-700 mb-2">
            Search Depth: {searchDepth}
          </label>
          <input
            id="depth"
            type="range"
            min="1"
            max="4"
            value={searchDepth}
            onChange={(e) => setSearchDepth(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1 (Close)</span>
            <span>4 (Extended)</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2">
          <button
            onClick={startLanguageSearch}
            disabled={connectionStatus !== 'connected' || !searchQuery.trim()}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Search Language Tree
          </button>

          <button
            onClick={() => {
              if (connectionStatus === 'connected') {
                sendMessage({
                  action: "fetch_language_relationships",
                  language_name: "English",
                  depth: 2
                });
              }
            }}
            disabled={connectionStatus !== 'connected'}
            className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Test English Language
          </button>
          
          <button
            onClick={connect}
            disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}
            className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Connect to Language Service
          </button>
          
          <button
            onClick={disconnect}
            disabled={connectionStatus === 'disconnected'}
            className="w-full px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Disconnect
          </button>
          
          <button
            onClick={clearMessages}
            className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
          >
            Clear Tree Data
          </button>
        </div>

        {/* Data Statistics */}
        <div className="mt-4 text-sm text-gray-600 bg-gray-50 p-2 rounded">
          <p>Messages received: {websocketData.length}</p>
          <p>Languages: {websocketData.filter(m => m.type === 'language_details').length}</p>
          <p>Relationships: {websocketData.filter(m => m.type === 'relationship').length}</p>
        </div>

        {/* Recent Messages (Debug) */}
        {websocketData.length > 0 && (
          <div className="mt-4 text-xs text-gray-600 bg-gray-50 p-2 rounded max-h-32 overflow-y-auto">
            <p className="font-semibold mb-1">Recent Messages:</p>
            {websocketData.slice(-3).map((msg, index) => (
              <div key={index} className="mb-1 p-1 bg-white rounded text-xs">
                <span className="font-medium">{msg.type}:</span> {JSON.stringify(msg.data).slice(0, 50)}...
              </div>
            ))}
          </div>
        )}
      </div>
      
      <LanguageTree websocketData={websocketData} />
    </main>
  );
}