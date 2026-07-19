import { api, API_URL } from './client';

export interface OrgStructure {
	departments: Array<{
		name: string; slug: string; description: string; goals: string;
	}>;
	humans: Array<{
		name: string; title: string; role: string; department_slug: string | null;
	}>;
	agents: Array<{
		name: string; slug: string; title: string; department_slug: string;
		model: string; skills: string[]; system_prompt_hint: string;
	}>;
	company_skills: Array<{
		name: string; slug: string; skill_type: string; description: string; content: string;
	}>;
	policies: Array<{
		name: string; slug: string; scope: string;
		department_slug: string | null; content: string;
	}>;
}

export interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
}

export interface SavedSession {
	phase: string;
	search_context: string;
	messages: ChatMessage[];
	structure: OrgStructure | null;
	updated_at: string;
}

export const onboardingApi = {
	status: (company_id: string) =>
		api.get<{ company_id: string; ai_onboarded: boolean; session: SavedSession | null }>(
			`/onboarding/status/${company_id}`
		),

	search: (company_name: string, company_id?: string) =>
		api.post<{ context: string; provider: string; model: string }>(
			'/onboarding/search', { company_name, company_id }
		),

	generate: (company_name: string, search_context: string, messages: ChatMessage[], company_id?: string, locale = 'tr') =>
		api.post<{ structure: OrgStructure }>(
			'/onboarding/generate', { company_name, search_context, messages, company_id, locale }
		),

	create: (company_id: string, structure: OrgStructure) =>
		api.post<{ success: boolean; summary: Record<string, number> }>(
			'/onboarding/create', { company_id, structure }
		),

	/** Opens an SSE connection for streaming chat. Returns cleanup fn. */
	streamChat(
		company_name: string,
		search_context: string,
		messages: ChatMessage[],
		token: string,
		onChunk: (text: string) => void,
		onDone: (ready: boolean) => void,
		onError: (err: string) => void,
		company_id?: string,
		locale = 'tr',
	): () => void {
		const ctrl = new AbortController();

		(async () => {
			try {
				const resp = await fetch(`${API_URL}/onboarding/chat`, {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						Authorization: `Bearer ${token}`,
					},
					body: JSON.stringify({ company_name, search_context, messages, company_id, locale }),
					signal: ctrl.signal,
				});

				if (!resp.ok) {
					const err = await resp.json().catch(() => ({ detail: resp.statusText }));
					onError(err.detail ?? 'Bilinmeyen hata');
					return;
				}

				const reader = resp.body!.getReader();
				const dec = new TextDecoder();
				let buf = '';

				while (true) {
					const { done, value } = await reader.read();
					if (done) break;
					buf += dec.decode(value, { stream: true });
					const lines = buf.split('\n');
					buf = lines.pop() ?? '';
					for (const line of lines) {
						if (!line.startsWith('data: ')) continue;
						const evt = JSON.parse(line.slice(6));
						if (evt.type === 'text') onChunk(evt.content);
						else if (evt.type === 'done') onDone(evt.ready ?? false);
						else if (evt.type === 'error') onError(evt.message);
					}
				}
			} catch (e: any) {
				if (e?.name !== 'AbortError') onError(e?.message ?? 'Bağlantı hatası');
			}
		})();

		return () => ctrl.abort();
	},
};
