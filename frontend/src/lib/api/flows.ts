import { api } from './client';

export type Flow = {
	id: string;
	company_id: string;
	personnel_id: string;
	name: string;
	description: string | null;
	schedule: string;
	prompt: string;
	enabled: boolean;
	last_run_at: string | null;
	last_run_status: 'success' | 'error' | null;
	last_run_output: string | null;
	created_at: string;
	updated_at: string;
};

export type FlowCreate = {
	personnel_id: string;
	name: string;
	description?: string;
	schedule: string;
	prompt: string;
	enabled?: boolean;
};

export const flows = {
	list:   (company_id?: string) => api.get<Flow[]>(company_id ? `/flows?company_id=${company_id}` : '/flows'),
	get:    (id: string)          => api.get<Flow>(`/flows/${id}`),
	create: (body: FlowCreate, company_id: string) => api.post<Flow>(`/flows?company_id=${company_id}`, body),
	update: (id: string, body: Partial<FlowCreate>) => api.patch<Flow>(`/flows/${id}`, body),
	delete: (id: string) => api.delete(`/flows/${id}`),
	run:    (id: string) => api.post<Flow>(`/flows/${id}/run`, {}),
};
