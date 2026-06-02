import { api } from './client';

export type Department = {
	id: string;
	name: string;
	slug: string;
	parent_id: string | null;
	parent_name: string | null;
	description: string | null;
	goals: string | null;
	policies: string[];
	status: 'Active' | 'Inactive';
	created_at: string;
	children?: Department[];
};

export type DepartmentCreate = {
	name: string;
	slug: string;
	parent_id?: string | null;
	description?: string | null;
	goals?: string | null;
	policies?: string[];
	status?: 'Active' | 'Inactive';
};
export type DepartmentUpdate = Partial<DepartmentCreate>;

export const departments = {
	list:   (company_id?: string)              => api.get<Department[]>(company_id ? `/departments?company_id=${company_id}` : '/departments'),
	get:    (id: string)                        => api.get<Department>(`/departments/${id}`),
	create: (body: DepartmentCreate, company_id?: string) => api.post<Department>(company_id ? `/departments?company_id=${company_id}` : '/departments', body),
	update: (id: string, body: DepartmentUpdate) => api.patch<Department>(`/departments/${id}`, body),
	delete: (id: string)                        => api.delete(`/departments/${id}`),
	tree:   (company_id?: string)              => api.get<Department[]>(company_id ? `/departments/tree/root?company_id=${company_id}` : '/departments/tree/root'),
};
