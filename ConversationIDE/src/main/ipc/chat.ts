import { IpcMain, BrowserWindow } from 'electron';
import { ChatSendRequest, ChatSendResponse } from './protocols';

const API_BASE = 'http://127.0.0.1:44444';
const MODEL = 'van_engine-brain';

// Direct HTTP request using Electron's net module
async function callVANApiDirect(messages: { role: string; content: string }[]): Promise<{ content: string | null; error?: string }> {
  const body = JSON.stringify({ model: MODEL, messages, stream: false });
  
  return new Promise((resolve) => {
    const { net } = require('electron');
    const request = net.request({
      method: 'POST',
      url: `${API_BASE}/v1/chat/completions`,
      headers: { 'Content-Type': 'application/json' }
    });
    
    let data = '';
    request.on('response', (response: any) => {
      response.on('data', (chunk: Buffer) => { data += chunk.toString(); });
      response.on('end', () => {
        if (response.statusCode === 200) {
          try {
            const parsed = JSON.parse(data);
            const content = parsed?.choices?.[0]?.message?.content;
            resolve({ content: content || null });
          } catch (e) {
            resolve({ content: null, error: 'Parse error' });
          }
        } else {
          resolve({ content: null, error: `HTTP ${response.statusCode}` });
        }
      });
    });
    request.on('error', (error: Error) => {
      resolve({ content: null, error: error.message });
    });
    request.write(body);
    request.end();
  });
}

function getFallbackResponse(message: string, error?: string): ChatSendResponse {
  return {
    response: `⚠️ Cannot reach VAN_Engine API at ${API_BASE}\n\nMake sure the brain is running:\ncd ../VanEngine.LLMGateway && dotnet run\n\nError: ${error || 'Connection refused'}\n\nYour message: "${message}"`,
    intent: 'system',
    skill: 'general',
    confidence: 0.1,
    auditId: `audit_${Date.now()}`
  };
}

export function setupChatHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  ipcMain.handle('chat:send', async (event, request: ChatSendRequest): Promise<ChatSendResponse> => {
    const { message, conversationId } = request;

    const history = [{ role: 'user' as const, content: message }];
    const { content, error } = await callVANApiDirect(history);

    let result: ChatSendResponse;
    if (content === null) {
      result = getFallbackResponse(message, error);
    } else {
      result = {
        response: content,
        intent: 'conversation',
        skill: 'general',
        confidence: 0.95,
        auditId: `audit_${Date.now()}`
      };
    }

    window.webContents.send('chat:response', {
      conversationId,
      ...result
    });

    return result;
  });

  ipcMain.handle('chat:history', async () => {
    return { messages: [] };
  });

  ipcMain.handle('chat:conversations', async () => {
    return { conversations: [] };
  });

  ipcMain.handle('brain:status', async () => {
    try {
      const { net } = require('electron');
      return new Promise((resolve) => {
        const request = net.request({ method: 'GET', url: `${API_BASE}/health` });
        let data = '';
        request.on('response', (response: any) => {
          response.on('data', (chunk: Buffer) => { data += chunk.toString(); });
          response.on('end', () => {
            if (response.statusCode === 200) {
              resolve({ available: true, uptime: 0, tokenCount: 0, activeISO: [] });
            } else {
              resolve({ available: false, error: `HTTP ${response.statusCode}` });
            }
          });
        });
        request.on('error', () => resolve({ available: false, error: 'Connection refused' }));
        request.end();
      });
    } catch (e: any) {
      return { available: false, error: e.message };
    }
  });
}