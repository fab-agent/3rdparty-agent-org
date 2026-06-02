import { api } from './client';

export interface CompanyStats {
  departments: number;
  personnel: number;
  agents: number;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  sector: string | null;
  website: string | null;
  created_at: string;
  stats: CompanyStats;
}

export interface CompanyCreate {
  name: string;
  slug: string;
  sector?: string;
  website?: string;
}

export const companies = {
  list: () => api.get<Company[]>('/companies'),
  get: (id: string) => api.get<Company>(`/companies/${id}`),
  create: (body: CompanyCreate) => api.post<Company>('/companies', body),
  update: (id: string, body: Partial<CompanyCreate>) => api.patch<Company>(`/companies/${id}`, body),
  delete: (id: string) => api.delete(`/companies/${id}`),
};
