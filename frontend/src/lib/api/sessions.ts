import { api } from './client';
import { API_URL } from './client';

export type SessionMessage = {
	id: string;
	session_id: string;
	role: 'user' | 'assistant';
	content: string;
	tool_calls: Array<{ name: string; args: Record<string, unknown> }>;
	tool_results: Array<{ name: string; result: string }>;
	tokens_used: number | null;
	created_at: string;
};

export type Session = {
	id: string;
	personnel_id: string;
	title: string | null;
	status: 'active' | 'closed';
	created_at: string;
	updated_at: string;
	messages?: SessionMessage[];
	last_message?: SessionMessage | null;
};

export type StreamEvent =
	| { type: 'text'; content: string }
	| { type: 'tool_call'; name: string; args: Record<string, unknown> }
	| { type: 'tool_result'; name: string; result: string }
	| { type: 'done'; message_id: string }
	| { type: 'error'; message: string }
	| { type: 'stream_end' };

export type AgentMemory = {
	id: string;
	personnel_id: string;
	session_id: string | null;
	summary: string;
	created_at: string;
};

export const sessionsApi = {
	list: (params?: { personnel_id?: string; status?: string }) => {
		const qs = new URLSearchParams();
		if (params?.personnel_id) qs.set('personnel_id', params.personnel_id);
		if (params?.status)       qs.set('status', params.status);
		const query = qs.toString() ? `?${qs}` : '';
		return api.get<Session[]>(`/sessions${query}`);
	},

	create: (personnel_id: string, title?: string) =>
		api.post<Session>('/sessions', { personnel_id, title }),

	get: (id: string) => api.get<Session>(`/sessions/${id}`),

	close: (id: string) => api.delete(`/sessions/${id}`),

	memories: (personnel_id?: string) => {
		const qs = personnel_id ? `?personnel_id=${personnel_id}` : '';
		return api.get<AgentMemory[]>(`/sessions/memories${qs}`);
	},
};

export async function* streamMessage(
	sessionId: string,
	content: string,
	signal?: AbortSignal
): AsyncGenerator<StreamEvent> {
	const response = await fetch(`${API_URL}/sessions/${sessionId}/messages`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ content }),
		signal,
	});

	if (!response.ok) {
		const err = await response.text();
		yield { type: 'error', message: err };
		return;
	}

	if (!response.body) {
		yield { type: 'error', message: 'No response body' };
		return;
	}

	const reader = response.body.getReader();
	const decoder = new TextDecoder();
	let buffer = '';

	while (true) {
		const { done, value } = await reader.read();
		if (done) break;

		buffer += decoder.decode(value, { stream: true });
		const lines = buffer.split('\n');
		buffer = lines.pop() ?? '';

		for (const line of lines) {
			if (!line.startsWith('data: ')) continue;
			const raw = line.slice(6).trim();
			if (!raw) continue;
			try {
				const event = JSON.parse(raw) as StreamEvent;
				yield event;
				if (event.type === 'stream_end') return;
			} catch {
				// malformed chunk, skip
			}
		}
	}
}
