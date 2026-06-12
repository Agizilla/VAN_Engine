import { IpcMain, BrowserWindow } from 'electron';
import * as http from 'http';
import * as https from 'https';

// ============================================================================
// Configuration
// ============================================================================

const LLM_GATEWAY_URL =  'http://127.0.0.1:44444';
const LLM_GATEWAY_HOST = '127.0.0.1';
const LLM_GATEWAY_PORT = 11434;

// ============================================================================
// HTTP Helpers
// ============================================================================

function httpRequest(url: string, body: string): Promise<string | null> {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 11434,
      path: urlObj.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body)
      },
      timeout: 30000
    };
    
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        if (res.statusCode !== 200) {
          resolve(null);
          return;
        }
        try {
          const parsed = JSON.parse(data);
          resolve(parsed?.choices?.[0]?.message?.content || null);
        } catch {
          resolve(null);
        }
      });
    });
    
    req.on('error', () => resolve(null));
    req.on('timeout', () => { req.destroy(); resolve(null); });
    req.write(body);
    req.end();
  });
}

function httpGet(url: string): Promise<{ ok: boolean; data?: any }> {
  return new Promise((resolve) => {
    const urlObj = new URL(url);
    const options = {
      hostname: urlObj.hostname,
      port: urlObj.port || 11434,
      path: urlObj.pathname,
      method: 'GET',
      timeout: 10000
    };
    
    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        if (res.statusCode !== 200) {
          resolve({ ok: false });
          return;
        }
        try {
          const parsed = JSON.parse(data);
          resolve({ ok: true, data: parsed });
        } catch {
          resolve({ ok: false });
        }
      });
    });
    
    req.on('error', () => resolve({ ok: false }));
    req.on('timeout', () => { req.destroy(); resolve({ ok: false }); });
    req.end();
  });
}

// ============================================================================
// Handler Setup
// ============================================================================

export async function setupVANEngineHandlers(ipcMain: IpcMain, window: BrowserWindow) {
  
  // Status endpoint - check if LLM Gateway is running
  ipcMain.handle('van-engine:status', async () => {
    try {
      const result = await httpGet(`${LLM_GATEWAY_URL}/health`);
      if (result.ok && result.data?.status === 'ok') {
        return {
          available: true,
          path: 'LLM Gateway',
          tokenCount: 0,
          isoCount: 20,
          uptime: 0,
          bridgeMode: 'http'
        };
      }
    } catch (e) {
      // Fall through
    }
    
    return {
      available: false,
      path: 'LLM Gateway (not reachable)',
      tokenCount: 0,
      isoCount: 20,
      uptime: 0,
      bridgeMode: 'offline'
    };
  });
  
  // Query endpoint - send message to LLM Gateway
  ipcMain.handle('van-engine:query', async (event, query: string, context: any) => {
    if (!query || query.trim() === '') {
      return {
        success: false,
        action: 'HALT_AND_CLARIFY',
        message: 'Please provide a query.',
        clarificationQuestions: ['What would you like to know?']
      };
    }
    
    try {
      const body = JSON.stringify({
        model: 'van_engine-brain',
        messages: [{ role: 'user', content: query }],
        stream: false
      });
      
      const response = await httpRequest(`${LLM_GATEWAY_URL}/v1/chat/completions`, body);
      
      if (response) {
        return {
          success: true,
          action: 'EXECUTE',
          message: response,
          clarificationQuestions: []
        };
      } else {
        return {
          success: false,
          action: 'HALT_AND_CLARIFY',
          message: 'LLM Gateway returned empty response. Make sure VAN_Engine is running.',
          clarificationQuestions: ['Is the VAN_Engine brain running?', 'Try: dotnet run in VAN_Engine folder']
        };
      }
    } catch (error: any) {
      return {
        success: false,
        action: 'HALT_AND_CLARIFY',
        message: `Cannot reach LLM Gateway at ${LLM_GATEWAY_URL}\n\nStart the brain with:\ncd ../VAN_Engine && dotnet run\n\nError: ${error.message}`,
        clarificationQuestions: ['Is the VAN_Engine brain running?']
      };
    }
  });
  
  // Quaternion lookup (passthrough - not implemented in HTTP mode)
  ipcMain.handle('van-engine:quaternion:lookup', async (event, token: string) => {
    return null;
  });
  
  // Quaternion store (passthrough - not implemented in HTTP mode)
  ipcMain.handle('van-engine:quaternion:store', async (event, token: string, w: number, x: number, y: number, z: number, applies_to: string) => {
    return { stored: false };
  });
  
  // ISO rule check
  ipcMain.handle('van-engine:iso:check', async (event, ruleId: string) => {
    return {
      ruleId,
      status: 'active',
      name: ruleId,
      timestamp: Date.now()
    };
  });
  
  // Get all ISO rules
  ipcMain.handle('van-engine:iso:all', async () => {
    const rules = [];
    for (let i = 1; i <= 20; i++) {
      rules.push({
        id: `ISO_${i.toString().padStart(3, '0')}`,
        name: `ISO Rule ${i}`,
        status: 'active'
      });
    }
    return { rules };
  });
  
  // Drift gate check
  ipcMain.handle('van-engine:drift:check', async (event, quaternion: [number, number, number, number]) => {
    // Simple check - if all values are within reasonable bounds
    const allValid = quaternion.every(v => Math.abs(v) <= 1.5);
    if (allValid) {
      return { violated: false, action: 'EXECUTE' };
    }
    return { violated: true, action: 'HALT_AND_CLARIFY' };
  });
  
  console.log('[VAN_Engine] HTTP mode handlers initialized');
  console.log(`[VAN_Engine] LLM Gateway URL: ${LLM_GATEWAY_URL}`);
}