/**
 * Tenant store — reads the subdomain from the current hostname and resolves
 * the matching company from the backend.
 *
 * fabrikayazilim.agent.fab.engineering  →  slug = "fabrikayazilim"
 * agent.fab.engineering                 →  slug = null  (no tenant pre-selected)
 * localhost:5173                        →  slug = null  (dev mode)
 */

import { API_URL } from '$lib/api/client';

const AGENT_DOMAIN = 'agent.fab.engineering';

export type TenantInfo = {
	id: string;
	name: string;
	slug: string;
} | null;

let _tenant = $state<TenantInfo>(null);
let _resolved = $state(false);

function extractSlug(): string | null {
	if (typeof window === 'undefined') return null;
	const host = window.location.hostname;
	if (host.endsWith(`.${AGENT_DOMAIN}`)) {
		const slug = host.slice(0, -`.${AGENT_DOMAIN}`.length);
		if (slug && !slug.includes('.')) return slug;
	}
	// Dev override: ?tenant=slug in URL
	const params = new URLSearchParams(window.location.search);
	return params.get('tenant');
}

export const tenantStore = {
	get info() {
		return _tenant;
	},
	get resolved() {
		return _resolved;
	},
	get slug() {
		return _tenant?.slug ?? null;
	},

	async resolve() {
		if (_resolved) return;
		const slug = extractSlug();
		if (!slug) {
			_resolved = true;
			return;
		}
		try {
			const res = await fetch(`${API_URL}/tenant/resolve?slug=${encodeURIComponent(slug)}`);
			if (res.ok) {
				_tenant = await res.json();
			}
		} catch {
			// network error — proceed without tenant
		}
		_resolved = true;
	},

	/** Force-set tenant (used after login to confirm the company matches) */
	set(info: TenantInfo) {
		_tenant = info;
	},

	clear() {
		_tenant = null;
		_resolved = false;
	},
};
