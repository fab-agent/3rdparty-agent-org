export interface ProviderDef {
  id: string
  displayName: string
  envKey: string
}

export const PROVIDERS: ProviderDef[] = [
  { id: 'anthropic', displayName: 'Anthropic (Claude)', envKey: 'ANTHROPIC_API_KEY' },
  { id: 'openai',    displayName: 'OpenAI (GPT)',        envKey: 'OPENAI_API_KEY'    },
  { id: 'google',    displayName: 'Google (Gemini)',     envKey: 'GOOGLE_API_KEY'    },
  { id: 'mistral',   displayName: 'Mistral AI',          envKey: 'MISTRAL_API_KEY'   },
]

export async function testProviderKey(provider: string, key: string): Promise<boolean> {
  const timeout = AbortSignal.timeout(10_000)
  try {
    switch (provider) {
      case 'anthropic': {
        const r = await fetch('https://api.anthropic.com/v1/messages', {
          method: 'POST',
          headers: { 'x-api-key': key, 'anthropic-version': '2023-06-01', 'content-type': 'application/json' },
          body: JSON.stringify({ model: 'claude-haiku-4-5-20251001', max_tokens: 1, messages: [{ role: 'user', content: 'hi' }] }),
          signal: timeout,
        })
        return r.status === 200
      }
      case 'openai': {
        const r = await fetch('https://api.openai.com/v1/chat/completions', {
          method: 'POST',
          headers: { Authorization: `Bearer ${key}`, 'content-type': 'application/json' },
          body: JSON.stringify({ model: 'gpt-4o-mini', max_tokens: 1, messages: [{ role: 'user', content: 'hi' }] }),
          signal: timeout,
        })
        return r.status === 200
      }
      case 'google': {
        const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models?key=${encodeURIComponent(key)}`, {
          signal: timeout,
        })
        return r.status === 200
      }
      case 'mistral': {
        const r = await fetch('https://api.mistral.ai/v1/models', {
          headers: { Authorization: `Bearer ${key}` },
          signal: timeout,
        })
        return r.status === 200
      }
      default: return false
    }
  } catch {
    return false
  }
}
