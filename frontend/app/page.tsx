// 'use client';

// import React, { useState, useEffect } from 'react';
// import GenealogyTree from '@/components/GenealogyTree';
// import { useWebSocket } from '@/hooks/useWebSocket';

// export default function Home() {
//   // WebSocket connection for real-time data
//   const { 
//     messages: websocketData, 
//     connectionStatus, 
//     connect, 
//     disconnect, 
//     clearMessages,
//     sendMessage 
//   } = useWebSocket('ws://localhost:8000/ws');

//   const [searchQuery, setSearchQuery] = useState('Albert Einstein');
//   const [searchDepth, setSearchDepth] = useState(2);

//   // Function to start genealogy search
//   const startGenealogySearch = () => {
//     if (connectionStatus === 'connected' && searchQuery.trim()) {
//       // Convert search query to Wikipedia page title format (replace spaces with underscores)
//       const pageTitle = searchQuery.trim().replace(/\s+/g, '_');
      
//       // Send search request to backend in the required format
//       sendMessage({
//         action: "fetch_relationships",
//         page_title: pageTitle,
//         depth: searchDepth
//       });
//     }
//   };

//   // Auto-connect on component mount
//   useEffect(() => {
//     connect();
//     return () => {
//       disconnect();
//     };
//   }, [connect, disconnect]);

//   const getConnectionStatusColor = () => {
//     switch (connectionStatus) {
//       case 'connected': return 'text-green-600';
//       case 'connecting': return 'text-yellow-600';
//       case 'error': return 'text-red-600';
//       default: return 'text-gray-600';
//     }
//   };

//   const getConnectionStatusText = () => {
//     switch (connectionStatus) {
//       case 'connected': return 'Connected';
//       case 'connecting': return 'Connecting...';
//       case 'error': return 'Connection Error';
//       default: return 'Disconnected';
//     }
//   };

//   return (
//     <main className="min-h-screen bg-gray-50">


//       <div className="absolute top-4 right-4 z-20 bg-white p-4 rounded-lg shadow-md max-w-sm">
//         <h1 className="text-xl font-bold mb-4">Genealogy Tree Creator</h1>
        
//         {/* Connection Status */}
//         <div className="mb-4 p-2 bg-gray-50 rounded">
//           <div className="flex items-center justify-between text-sm">
//             <span>WebSocket Status:</span>
//             <span className={getConnectionStatusColor()}>
//               {getConnectionStatusText()}
//             </span>
//           </div>
//         </div>

//         {/* Search Input */}
//         <div className="mb-4">
//           <label htmlFor="search" className="block text-sm font-medium text-gray-700 mb-2">
//             Search Person
//           </label>
//           <input
//             id="search"
//             type="text"
//             value={searchQuery}
//             onChange={(e) => setSearchQuery(e.target.value)}
//             placeholder="Enter person's name (e.g., Albert Einstein)"
//             className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
//             onKeyPress={(e) => {
//               if (e.key === 'Enter') {
//                 startGenealogySearch();
//               }
//             }}
//           />
//         </div>

//         {/* Depth Control */}
//         <div className="mb-4">
//           <label htmlFor="depth" className="block text-sm font-medium text-gray-700 mb-2">
//             Search Depth: {searchDepth}
//           </label>
//           <input
//             id="depth"
//             type="range"
//             min="1"
//             max="4"
//             value={searchDepth}
//             onChange={(e) => setSearchDepth(parseInt(e.target.value))}
//             className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
//           />
//           <div className="flex justify-between text-xs text-gray-500 mt-1">
//             <span>1 (Close)</span>
//             <span>4 (Extended)</span>
//           </div>
//         </div>

//         {/* Action Buttons */}
//         <div className="space-y-2">
//           <button
//             onClick={startGenealogySearch}
//             disabled={connectionStatus !== 'connected' || !searchQuery.trim()}
//             className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Search Genealogy Tree
//           </button>

//           <button
//             onClick={() => {
//               if (connectionStatus === 'connected') {
//                 sendMessage({
//                   action: "fetch_relationships",
//                   page_title: "Albert_Einstein",
//                   depth: 2
//                 });
//               }
//             }}
//             disabled={connectionStatus !== 'connected'}
//             className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Test Albert Einstein
//           </button>
          
//           <button
//             onClick={connect}
//             disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}
//             className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Connect to Server
//           </button>
          
//           <button
//             onClick={disconnect}
//             disabled={connectionStatus === 'disconnected'}
//             className="w-full px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
//           >
//             Disconnect
//           </button>
          
//           <button
//             onClick={clearMessages}
//             className="w-full px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
//           >
//             Clear Tree Data
//           </button>
//         </div>

//         {/* Data Statistics */}
//         <div className="mt-4 text-sm text-gray-600 bg-gray-50 p-2 rounded">
//           <p>Messages received: {websocketData.length}</p>
//           <p>People: {websocketData.filter(m => m.type === 'personal_details').length}</p>
//           <p>Relationships: {websocketData.filter(m => m.type === 'relationship').length}</p>
//         </div>

//         {/* Recent Messages (Debug) */}
//         {websocketData.length > 0 && (
//           <div className="mt-4 text-xs text-gray-600 bg-gray-50 p-2 rounded max-h-32 overflow-y-auto">
//             <p className="font-semibold mb-1">Recent Messages:</p>
//             {websocketData.slice(-3).map((msg, index) => (
//               <div key={index} className="mb-1 p-1 bg-white rounded text-xs">
//                 <span className="font-medium">{msg.type}:</span> {JSON.stringify(msg.data).slice(0, 50)}...
//               </div>
//             ))}
//           </div>
//         )}
//       </div>
      
//       <GenealogyTree websocketData={websocketData} />
//     </main>
//   );
// }

'use client';

import React, { useState, useEffect } from 'react';
import GenealogyTree from '@/components/GenealogyTree';
import { useWebSocket } from '@/hooks/useWebSocket';

export default function Home() {
  // WebSocket connection for real-time data
  const { 
    messages: websocketData, 
    connectionStatus, 
    connect, 
    disconnect, 
    clearMessages,
    sendMessage 
  } = useWebSocket('ws://localhost:8000/ws');

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
    <main className="w-full h-screen overflow-hidden relative">
      {/* Control Panel - Fixed position */}
      <div className="absolute top-4 right-4 z-20 bg-white p-4 rounded-lg shadow-md max-w-sm">
        <h1 className="text-xl font-bold mb-4">Genealogy Tree Creator</h1>
        
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
            Search Person
          </label>
          <input
            id="search"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter person's name (e.g., Albert Einstein)"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => {
              if (e.key === 'Enter') {
                startGenealogySearch();
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
            onClick={startGenealogySearch}
            disabled={connectionStatus !== 'connected' || !searchQuery.trim()}
            className="w-full px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
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
            className="w-full px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Test Albert Einstein
          </button>
          
          <button
            onClick={connect}
            disabled={connectionStatus === 'connected' || connectionStatus === 'connecting'}
            className="w-full px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Connect to Server
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
          <p>People: {websocketData.filter(m => m.type === 'personal_details').length}</p>
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
      
      {/* Genealogy Tree - Takes full screen */}
      <GenealogyTree websocketData={websocketData} />
    </main>
  );
}