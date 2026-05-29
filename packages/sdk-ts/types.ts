// src/types.ts
export interface GenerateRequest {
    provider: string;
    model: string;
    session_id?: string;
    prompt: string;
}

export interface SessionIdRequest {
    session_id: string;
}

export interface Message {
    role: string;
    content: string;
    [key: string]: any;
}