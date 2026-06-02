import { api } from './client';
import type { OrgNode } from '$lib/types/org';

export const orgTree = {
	get: (company_id?: string) => api.get<OrgNode[]>(company_id ? `/org-tree?company_id=${company_id}` : '/org-tree'),
};
