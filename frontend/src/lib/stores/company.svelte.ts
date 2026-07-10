import { companies, type Company } from '$lib/api/companies';

let _list = $state<Company[]>([]);
let _active = $state<Company | null>(null);
let _loaded = $state(false);

export const companyStore = {
  get list() { return _list; },
  get active() { return _active; },
  get loaded() { return _loaded; },

  // preferredIds: set active to first company user is a member of, not data[0]
  async load(preferredIds?: string[]) {
    const data = await companies.list();
    _list = data;
    if (!_active && data.length > 0) {
      if (preferredIds?.length) {
        _active = data.find(c => preferredIds.includes(c.id)) ?? null;
      } else {
        _active = data[0];
      }
    }
    _loaded = true;
  },

  setActive(company: Company) {
    _active = company;
    _list = _list.map(c => c.id === company.id ? company : c);
  },

  async create(name: string) {
    const slug = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    const company = await companies.create({ name, slug });
    _list = [..._list, company];
    _active = company;
    return company;
  },
};
