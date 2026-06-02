import { companies, type Company } from '$lib/api/companies';

let _list = $state<Company[]>([]);
let _active = $state<Company | null>(null);
let _loaded = $state(false);

export const companyStore = {
  get list() { return _list; },
  get active() { return _active; },
  get loaded() { return _loaded; },

  async load() {
    const data = await companies.list();
    _list = data;
    if (!_active && data.length > 0) {
      _active = data[0];
    }
    _loaded = true;
  },

  setActive(company: Company) {
    _active = company;
  },

  async create(name: string) {
    const slug = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    const company = await companies.create({ name, slug });
    _list = [..._list, company];
    _active = company;
    return company;
  },
};
