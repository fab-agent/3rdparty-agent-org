import { api } from './client';

export interface Policy {
	id: string;
	company_id: string;
	department_id: string | null;
	agent_config_id: string | null;
	name: string;
	slug: string;
	content: string;
	scope: 'company' | 'department' | 'agent';
	is_active: boolean;
	created_at: string;
	updated_at: string;
}

export interface PolicyCreate {
	company_id: string;
	name: string;
	slug: string;
	content?: string;
	scope?: string;
	department_id?: string;
	agent_config_id?: string;
}

export interface PolicyUpdate {
	name?: string;
	slug?: string;
	content?: string;
	scope?: string;
	department_id?: string;
	agent_config_id?: string;
	is_active?: boolean;
}

export const policiesApi = {
	list: (params?: { company_id?: string; scope?: string; department_id?: string }) => {
		const qs = new URLSearchParams();
		if (params?.company_id) qs.set('company_id', params.company_id);
		if (params?.scope) qs.set('scope', params.scope);
		if (params?.department_id) qs.set('department_id', params.department_id);
		const q = qs.toString() ? `?${qs}` : '';
		return api.get<Policy[]>(`/policies${q}`);
	},
	get: (id: string) => api.get<Policy>(`/policies/${id}`),
	create: (body: PolicyCreate) => api.post<Policy>('/policies', body),
	update: (id: string, body: PolicyUpdate, propose = false, personnel_id?: string) => {
		const qs = new URLSearchParams();
		if (propose) qs.set('propose', 'true');
		if (personnel_id) qs.set('personnel_id', personnel_id);
		const q = qs.toString() ? `?${qs}` : '';
		return api.put<Policy | { change_request_id: string; status: string }>(
			`/policies/${id}${q}`, body
		);
	},
	delete: (id: string) => api.delete(`/policies/${id}`),
};
