import { useState, useCallback } from 'react';

export type InferenceTier = 'fast' | 'standard' | 'smart';

export interface InferenceResult {
  success: boolean;
  output: string;
  tier: InferenceTier;
  latencyMs: number;
  error?: string;
  parsed?: any;
  fromCache?: boolean;
}

export function useInference() {
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<InferenceResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const runInference = useCallback(async (
    prompt: string,
    tier: InferenceTier = 'standard',
    expectJson: boolean = false
  ): Promise<InferenceResult | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await window.electronAPI.inference?.run({
        systemPrompt: '',
        userPrompt: prompt,
        tier,
        expectJson
      });

      if (response) {
        setResult(response);
        return response;
      }

      const apiResponse = await fetch('http://localhost:44444/v1/chat/completions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          model: 'van_engine-brain',
          messages: [{ role: 'user', content: prompt }],
          stream: false
        })
      });

      const data = await apiResponse.json();
      const inferenceResult: InferenceResult = {
        success: true,
        output: data.choices?.[0]?.message?.content || '',
        tier,
        latencyMs: 0
      };

      setResult(inferenceResult);
      return inferenceResult;

    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearResult = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { isLoading, result, error, runInference, clearResult };
}
