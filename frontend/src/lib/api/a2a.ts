import { api } from './client';

export type A2AStatus =
	| 'pending_approval'
	| 'approved'
	| 'running'
	| 'pending_result_approval'
	| 'completed'
	| 'rejected';

export type A2ARequest = {
	id: string;
	from_session_id: string;
	from_agent_id: string;
	from_agent_name: string | null;
	to_agent_id: string;
	to_agent_name: string | null;
	task: string;
	context: string | null;
	status: A2AStatus;
	result: string | null;
	approver_id: string | null;
	approver_name: string | null;
	approved_at: string | null;
	result_approved_at: string | null;
	rejection_reason: string | null;
	created_at: string;
	updated_at: string;
};

export const a2aApi = {
	list: (params?: { company_id?: string; approver_id?: string; status?: string }) => {
		const qs = new URLSearchParams();
		if (params?.company_id) qs.set('company_id', params.company_id);
		if (params?.approver_id) qs.set('approver_id', params.approver_id);
		if (params?.status) qs.set('status', params.status);
		const q = qs.toString() ? `?${qs}` : '';
		return api.get<A2ARequest[]>(`/a2a/requests${q}`);
	},

	pendingCount: (company_id?: string) => {
		const q = company_id ? `?company_id=${company_id}` : '';
		return api.get<{ count: number }>(`/a2a/requests/pending-count${q}`);
	},

	get: (id: string) => api.get<A2ARequest>(`/a2a/requests/${id}`),

	create: (body: {
		from_session_id: string;
		from_agent_id: string;
		to_agent_id: string;
		task: string;
		context?: string;
	}) => api.post<A2ARequest>('/a2a/requests', body),

	approve: (id: string, approver_id: string) =>
		api.post<{ status: string }>(`/a2a/requests/${id}/approve`, { approver_id }),

	approveResult: (id: string, approver_id: string) =>
		api.post<A2ARequest>(`/a2a/requests/${id}/approve-result`, { approver_id }),

	reject: (id: string, approver_id: string, reason?: string) =>
		api.post<A2ARequest>(`/a2a/requests/${id}/reject`, { approver_id, reason }),

	delegationStatus: (session_id: string) =>
		api.get<{
			total: number;
			pending: number;
			completed: number;
			rejected: number;
			all_done: boolean;
		}>(`/a2a/sessions/${session_id}/delegation-status`),
};

export function statusLabel(s: A2AStatus): string {
	const map: Record<A2AStatus, string> = {
		pending_approval: 'Onay Bekliyor',
		approved: 'Onaylandı',
		running: 'Çalışıyor',
		pending_result_approval: 'Sonuç Onayı Bekliyor',
		completed: 'Tamamlandı',
		rejected: 'Reddedildi',
	};
	return map[s] ?? s;
}

export function statusColor(s: A2AStatus): string {
	if (s === 'completed') return 'text-green-600 bg-green-50 border-green-200';
	if (s === 'rejected') return 'text-red-600 bg-red-50 border-red-200';
	if (s === 'running') return 'text-blue-600 bg-blue-50 border-blue-200';
	if (s === 'pending_approval' || s === 'pending_result_approval')
		return 'text-amber-600 bg-amber-50 border-amber-200';
	return 'text-muted-foreground bg-muted/40 border-border';
}
