<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { Layers, Mail, Lock, Loader, Building2, Globe, Check } from '@lucide/svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { companyStore } from '$lib/stores/company.svelte';
	import { tenantStore } from '$lib/stores/tenant.svelte';
	import { i18n, type Locale } from '$lib/i18n/index.svelte';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);
	let langMenuOpen = $state(false);

	const locales: { code: Locale; label: string; flag: string }[] = [
		{ code: 'tr', label: 'Türkçe', flag: '🇹🇷' },
		{ code: 'en', label: 'English', flag: '🇬🇧' }
	];

	onMount(async () => {
		await tenantStore.resolve();
	});

	async function submit(e: Event) {
		e.preventDefault();
		if (!email.trim() || !password) return;
		loading = true;
		error = '';
		try {
			const user = await authStore.login(email.trim().toLowerCase(), password);
			await companyStore.load();

			if (tenantStore.slug) {
				const match = companyStore.list.find((c) => c.slug === tenantStore.slug);
				if (match) companyStore.setActive(match);
			}

			if (user.must_change_password) {
				goto('/set-password?mode=first');
				return;
			}
			const firstCompany = user.companies[0];
			const role = firstCompany?.role;
			if (role === 'agent_owner') goto('/agents');
			else if (role === 'user') goto('/inbox');
			else goto('/');
		} catch (e: any) {
			error = e?.message ?? i18n.t('login_error_default');
		} finally {
			loading = false;
		}
	}

	const tenant = $derived(tenantStore.info);
	const currentLang = $derived(locales.find((l) => l.code === i18n.locale)!);
</script>

<svelte:head>
	<title>{tenant?.name ? `${tenant.name} — ${i18n.t('login_title')}` : `${i18n.t('login_title')} • fab.engineering`}</title>
</svelte:head>

<div class="min-h-screen bg-background flex items-center justify-center p-4">
	<!-- Language switcher -->
	<div class="absolute top-4 right-4">
		<div class="relative">
			<button
				class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-muted/60 transition-colors border border-border/50"
				onclick={() => (langMenuOpen = !langMenuOpen)}
			>
				<Globe class="w-3.5 h-3.5" />
				<span>{currentLang.flag} {currentLang.label}</span>
			</button>
			{#if langMenuOpen}
				<div class="absolute right-0 top-full mt-1 w-36 rounded-xl border bg-card shadow-lg overflow-hidden z-50">
					{#each locales as loc}
						<button
							class="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-muted/60 transition-colors {loc.code === i18n.locale ? 'font-semibold text-primary' : 'text-foreground'}"
							onclick={() => { i18n.locale = loc.code; langMenuOpen = false; }}
						>
							<span>{loc.flag}</span>
							<span>{loc.label}</span>
							{#if loc.code === i18n.locale}<Check class="w-3.5 h-3.5 ml-auto" />{/if}
						</button>
					{/each}
				</div>
			{/if}
		</div>
	</div>

	{#if langMenuOpen}
		<div class="fixed inset-0 z-40" onclick={() => (langMenuOpen = false)}></div>
	{/if}

	<div class="w-full max-w-sm">
		<!-- Logo / Tenant branding -->
		<div class="flex items-center justify-center gap-2.5 mb-8">
			{#if tenant?.name}
				<div class="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center">
					<Building2 class="w-6 h-6 text-primary" />
				</div>
				<div class="flex flex-col">
					<span class="font-bold text-xl tracking-tight">{tenant.name}</span>
					<span class="text-xs text-muted-foreground">agent.fab.engineering</span>
				</div>
			{:else}
				<div class="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
					<Layers class="w-6 h-6 text-primary-foreground" />
				</div>
				<div class="flex items-baseline">
					<span class="font-bold text-2xl tracking-tighter">fab</span>
					<span class="font-semibold text-2xl tracking-tighter text-muted-foreground">.engineering</span>
				</div>
			{/if}
		</div>

		<!-- Card -->
		<div class="rounded-2xl border bg-card p-8 shadow-sm">
			<h1 class="font-display text-xl tracking-tight text-center mb-1">{i18n.t('login_title')}</h1>
			<p class="text-sm text-muted-foreground text-center mb-6">
				{tenant?.name
					? `${tenant.name} ${i18n.t('login_tenant_subtitle')}`
					: i18n.t('login_subtitle')}
			</p>

			<form onsubmit={submit} class="space-y-4">
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="email">{i18n.t('login_email')}</label>
					<div class="relative">
						<Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
						<Input
							id="email"
							type="email"
							bind:value={email}
							placeholder={i18n.t('login_email_placeholder')}
							class="pl-9"
							autocomplete="email"
							required
						/>
					</div>
				</div>

				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="password">{i18n.t('login_password')}</label>
					<div class="relative">
						<Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
						<Input
							id="password"
							type="password"
							bind:value={password}
							placeholder="••••••••"
							class="pl-9"
							autocomplete="current-password"
							required
						/>
					</div>
				</div>

				{#if error}
					<div class="rounded-lg bg-destructive/10 border border-destructive/20 px-3 py-2.5 text-sm text-destructive">
						{error}
					</div>
				{/if}

				<Button type="submit" class="w-full" disabled={loading || !email || !password}>
					{#if loading}
						<Loader class="w-4 h-4 animate-spin" />
						{i18n.t('login_submitting')}
					{:else}
						{i18n.t('login_submit')}
					{/if}
				</Button>
			</form>

			<div class="mt-5 pt-4 border-t text-center">
				<a href="/request-reset" class="text-xs text-muted-foreground hover:text-foreground transition-colors">
					{i18n.t('login_forgot')}
				</a>
			</div>
		</div>

		{#if tenant?.name}
			<p class="text-center text-xs text-muted-foreground mt-4">
				{i18n.t('login_powered_by')} <a href="https://fab.engineering" class="hover:text-foreground transition-colors">fab.engineering</a>
			</p>
		{/if}
	</div>
</div>
