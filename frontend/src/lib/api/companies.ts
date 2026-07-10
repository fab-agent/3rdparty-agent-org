import { api } from './client';

export interface CompanyStats {
  departments: number;
  personnel: number;
  agents: number;
}

export interface CompanyGoal {
  id: number;
  text: string;
  done: boolean;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  sector: string | null;
  website: string | null;
  created_at: string;
  stats: CompanyStats;
  vision: string | null;
  mission: string | null;
  values: string[];
  goals: CompanyGoal[];
}

export interface CompanyCreate {
  name: string;
  slug: string;
  sector?: string;
  website?: string;
}

export interface CompanyUpdate {
  name?: string;
  slug?: string;
  sector?: string;
  website?: string;
  vision?: string;
  mission?: string;
  values?: string[];
  goals?: CompanyGoal[];
}

export const companies = {
  list: () => api.get<Company[]>('/companies'),
  get: (id: string) => api.get<Company>(`/companies/${id}`),
  create: (body: CompanyCreate) => api.post<Company>('/companies', body),
  update: (id: string, body: CompanyUpdate) => api.patch<Company>(`/companies/${id}`, body),
  delete: (id: string) => api.delete(`/companies/${id}`),
};
