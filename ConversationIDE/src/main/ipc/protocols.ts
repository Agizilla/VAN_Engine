export interface ChatSendRequest {
  message: string;
  conversationId: string;
  attachments?: string[];
}

export interface ChatSendResponse {
  response: string;
  intent: string;
  skill: string;
  confidence: number;
  auditId: string;
}

export interface FileReadRequest {
  path: string;
}

export interface FileWriteRequest {
  path: string;
  content: string;
  atomic?: boolean;
}

export interface FileTreeRequest {
  root: string;
  depth?: number;
}

export interface BuildRequest {
  projectRoot: string;
  spec: string;
  target: 'react' | 'vue' | 'python' | 'csharp';
}

export interface QuaternionRequest {
  operation: 'lookup' | 'project' | 'magnitude';
  token?: string;
  quaternion?: [number, number, number, number];
}

export interface ISOValidationRequest {
  ruleId: string;
  context: any;
}
