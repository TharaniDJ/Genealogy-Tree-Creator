// Shared WebSocket message types for the application

export interface WebSocketMessage {
  type: 'status' | 'personal_details' | 'relationship' | 'classified_relationships' | 'complete' | 'error' | string;
  data: any;
}

export interface PersonDetails {
  entity: string;
  qid: string;
  birth_year?: string;
  death_year?: string;
  image_url?: string;
}

export interface Relationship {
  entity1: string;
  relationship: string;
  entity2: string;
  classification?: string;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'error';
