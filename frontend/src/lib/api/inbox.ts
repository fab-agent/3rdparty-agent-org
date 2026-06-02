import { api } from './client';

export type InboxMessage = {
	id: string;
	company_id: string;
	recipient_user_id: string;
	source_type: 'flow' | 'task_request' | 'task_result' | 'system';
	source_id: string | null;
	title: string;
	body: string;
	read: boolean;
	created_at: string;
};

export type TaskRequest = {
	id: string;
	company_id: string;
	requester_user_id: string;
	department_id: string | null;
	skill_filter: string | null;
	assigned_agent_id: string | null;
	responsible_user_id: string | null;
	title: string;
	body: string;
	human_note: string | null;
	status: 'pending' | 'assigned' | 'running' | 'completed' | 'rejected';
	result: string | null;
	created_at: string;
	updated_at: string;
};

function qs(p: Record<string, string | boolean | undefined>) {
	const u = new URLSearchParams();
	for (const [k, v] of Object.entries(p)) {
		if (v !== undefined && v !== '') u.set(k, String(v));
	}
	return u.toString() ? `?${u}` : '';
}

export const inbox = {
	list:        (params?: { company_id?: string; unread_only?: boolean; period?: string }) =>
		api.get<InboxMessage[]>(`/inbox${qs(params ?? {})}`),
	unreadCount: (company_id?: string) =>
		api.get<{ count: number }>(`/inbox/unread-count${company_id ? `?company_id=${company_id}` : ''}`),
	markRead:    (id: string)         => api.post<InboxMessage>(`/inbox/${id}/read`, {}),
	markAllRead: (company_id?: string) => api.post<{ marked: number }>(`/inbox/read-all${company_id ? `?company_id=${company_id}` : ''}`, {}),
	delete:      (id: string)         => api.delete(`/inbox/${id}`),
};

export const taskRequests = {
	list:   (params?: { company_id?: string; status?: string }) =>
		api.get<TaskRequest[]>(`/task-requests${qs(params ?? {})}`),
	create: (body: { company_id: string; department_id?: string; skill_filter?: string; title: string; body: string }) =>
		api.post<TaskRequest>('/task-requests', body),
	run:    (id: string, human_note?: string) =>
		api.post<TaskRequest>(`/task-requests/${id}/run`, { human_note }),
	reject: (id: string, human_note?: string) =>
		api.post<TaskRequest>(`/task-requests/${id}/reject`, { human_note }),
};
