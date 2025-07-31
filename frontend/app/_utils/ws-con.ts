import { PersonData } from '@/lib/types';

interface WebSocketHandlers {
  setWsStatus: (status: 'disconnected' | 'connected' | 'loading') => void;
  wsRef: React.MutableRefObject<WebSocket | null>;
  setRelationships: React.Dispatch<React.SetStateAction<any[]>>;
  setPersonalDetails: React.Dispatch<React.SetStateAction<Record<string, PersonData>>>;
  setIsSearching: (searching: boolean) => void;
}

/**
 * Creates and manages WebSocket connection for genealogy data
 */
export const connectWebSocket = (handlers: WebSocketHandlers): (() => void) => {
  const { setWsStatus, wsRef, setRelationships, setPersonalDetails, setIsSearching } = handlers;
  
  setWsStatus('loading');
  const ws = new WebSocket('ws://localhost:8000/ws-test');
  
  ws.onopen = () => {
    setWsStatus('connected');
    wsRef.current = ws;
  };
  
  ws.onmessage = (event) => {
    try {
      const message = JSON.parse(event.data);

      if (message.type === 'relationship') {
        setRelationships(prev => [...prev, message.data]);
      } else if (message.type === 'personal_details') {
        // Store personal details for each entity
        const { entity, birth_year, death_year, image_url } = message.data;
        setPersonalDetails(prev => ({
          ...prev,
          [entity]: {
            name: entity,
            birthYear: birth_year ? parseInt(birth_year) : undefined,
            deathYear: death_year ? parseInt(death_year) : undefined,
            image: image_url || "/placeholder-user.jpg"
          }
        }));
      } else if (message.type === 'status') {
        if (message.data.message === 'Collection complete!') {
          setIsSearching(false);
        }
      }
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };
  
  ws.onclose = () => {
    setWsStatus('disconnected');
    wsRef.current = null;
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    setWsStatus('disconnected');
  };

  // Return cleanup function
  return () => {
    if (wsRef.current) {
      wsRef.current.close();
    }
  };
};
