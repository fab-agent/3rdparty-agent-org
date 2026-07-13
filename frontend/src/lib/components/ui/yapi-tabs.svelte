<script lang="ts">
	import { page } from '$app/stores';
	import { Building2, Users, Bot, Zap, FileText } from '@lucide/svelte';
	import { t } from '$lib/i18n/index.svelte';

	const tabs = $derived([
		{ href: '/departments', label: t('nav_departments'), icon: Building2 },
		{ href: '/personnel',   label: t('nav_personnel'),  icon: Users     },
		{ href: '/agents',      label: t('nav_agents'),     icon: Bot       },
		{ href: '/skills',      label: t('nav_skills'),     icon: Zap       },
		{ href: '/policies',    label: t('nav_policies'),   icon: FileText  },
	]);

	const current = $derived($page.url.pathname);
</script>

<div class="yapi-tabs-wrap">
	<div class="flex items-center gap-x-1" style="overflow-x:auto; scrollbar-width:none; -ms-overflow-style:none;">
		{#each tabs as tab}
			{@const active = current.startsWith(tab.href)}
			<a
				href={tab.href}
				class="yapi-tab {active ? 'yapi-tab-active' : 'yapi-tab-inactive'}"
			>
				<tab.icon class="w-4 h-4 flex-shrink-0" />
				<span>{tab.label}</span>
			</a>
		{/each}
	</div>
	<div class="yapi-tab-border"></div>
</div>

<style>
.yapi-tabs-wrap {
	position: relative;
	margin-bottom: 2rem;
}
.yapi-tab-border {
	position: absolute;
	bottom: 0; left: 0; right: 0;
	height: 1px;
	background: hsl(var(--border));
	pointer-events: none;
}
.yapi-tab {
	display: inline-flex;
	align-items: center;
	gap: 0.375rem;
	padding: 0.5rem 0.875rem;
	font-size: 0.8125rem;
	font-weight: 500;
	border-bottom: 2px solid transparent;
	white-space: nowrap;
	text-decoration: none;
	transition: color 0.15s, border-color 0.15s;
	position: relative;
	z-index: 1;
}
.yapi-tab-active {
	color: hsl(var(--foreground));
	border-bottom-color: hsl(var(--primary));
}
.yapi-tab-inactive {
	color: hsl(var(--muted-foreground));
}
.yapi-tab-inactive:hover {
	color: hsl(var(--foreground));
}
</style>
