import { api } from './client.js';

export interface ProviderStatus {
  provider: string;
  display_name: string;
  status: 'active' | 'invalid' | 'unconfigured';
  has_key: boolean;
  models: Array<{ id: string; name: string }>;
  last_tested: string | null;
}

export interface ModelDef {
  id: string;
  name: string;
  provider: string;
}

export const providers = {
  status:    ()                          => api.get<ProviderStatus[]>('/providers/status'),
  models:    ()                          => api.get<ModelDef[]>('/providers/models'),
  setKey:    (provider: string, key: string) =>
    api.post<ProviderStatus>(`/providers/${provider}/key`, { key }),
  deleteKey: (provider: string)          => api.delete(`/providers/${provider}/key`),
  test:      (provider: string)          =>
    api.post<ProviderStatus>(`/providers/${provider}/test`, {}),
};
