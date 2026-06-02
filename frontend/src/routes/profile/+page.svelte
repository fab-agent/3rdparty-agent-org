<script lang="ts">
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import { KeyRound, ShieldCheck, Save, Eye, EyeOff, Layers, CheckCircle2, Building2 } from '@lucide/svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { companyStore } from '$lib/stores/company.svelte';

	// ── Active tab ────────────────────────────────────────────────────────────
	type Tab = 'profile' | 'security';
	let activeTab: Tab = $state('profile');

	// ── Auth-driven data ──────────────────────────────────────────────────────
	const currentUser = $derived(authStore.user);
	const initials = $derived(
		currentUser?.name?.split(' ').map(w => w[0]).slice(0, 2).join('').toUpperCase() ?? '??'
	);
	const ROLE_LABELS: Record<string, string> = {
		founder: 'Kurucu', executive: 'Yönetici', dept_head: 'Bölüm Yöneticisi',
		agent_owner: 'Ajan Sorumlusu', user: 'Kullanıcı',
	};

	// ── Password change ───────────────────────────────────────────────────────
	let passwords = $state({ next: '', confirm: '' });
	let showNext    = $state(false);
	let showConfirm = $state(false);
	let pwError: string | null = $state(null);
	let pwSaving = $state(false);
	let pwSaved  = $state(false);

	const pwStrength = $derived(() => {
		const p = passwords.next;
		if (!p) return 0;
		let s = 0;
		if (p.length >= 8) s++;
		if (/[A-Z]/.test(p)) s++;
		if (/[0-9]/.test(p)) s++;
		if (/[^A-Za-z0-9]/.test(p)) s++;
		return s;
	});
	const pwStrengthLabel = $derived((['', 'Zayıf', 'Orta', 'İyi', 'Güçlü'] as const)[pwStrength()]);
	const pwStrengthColor = $derived((['', 'bg-red-400', 'bg-orange-400', 'bg-yellow-400', 'bg-emerald-500'] as const)[pwStrength()]);

	async function savePassword() {
		pwError = null;
		if (passwords.next.length < 8) { pwError = 'Yeni şifre en az 8 karakter olmalı.'; return; }
		if (passwords.next !== passwords.confirm) { pwError = 'Şifreler eşleşmiyor.'; return; }
		pwSaving = true;
		try {
			await authStore.changePassword(passwords.next);
			passwords = { next: '', confirm: '' };
			pwSaved = true;
			setTimeout(() => (pwSaved = false), 3000);
		} catch (e: any) {
			pwError = e?.message ?? 'Şifre değiştirilemedi';
		} finally {
			pwSaving = false;
		}
	}
</script>

<svelte:head>
	<title>Profil • fab.engineering</title>
</svelte:head>

<div class="space-y-6 max-w-3xl">

	<!-- Header + Avatar -->
	<div class="flex flex-col sm:flex-row sm:items-center gap-5">
		<div class="w-20 h-20 rounded-2xl bg-primary/10 flex items-center justify-center text-2xl font-bold text-primary select-none flex-shrink-0">
			{initials}
		</div>
		<div>
			<h1 class="font-display text-3xl tracking-tight">{currentUser?.name ?? '—'}</h1>
			<p class="text-muted-foreground mt-0.5 text-sm">{currentUser?.email ?? ''}</p>
			<div class="flex flex-wrap items-center gap-2 mt-2">
				{#each currentUser?.companies ?? [] as membership}
					<Badge variant="secondary" class="gap-1.5">
						<Building2 class="w-3 h-3" />
						{membership.company_name} · {ROLE_LABELS[membership.role] ?? membership.role}
					</Badge>
				{/each}
			</div>
		</div>
	</div>

	<!-- Tabs -->
	<div class="flex gap-1 border-b">
		{#each [
			{ id: 'profile',  label: 'Hesap Bilgileri' },
			{ id: 'security', label: 'Güvenlik' },
		] as tab}
			<button
				onclick={() => (activeTab = tab.id as Tab)}
				class={[
					'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
					activeTab === tab.id
						? 'border-primary text-primary'
						: 'border-transparent text-muted-foreground hover:text-foreground'
				].join(' ')}
			>
				{tab.label}
			</button>
		{/each}
	</div>

	<!-- ── Tab: Hesap Bilgileri ───────────────────────────────────────────────── -->
	{#if activeTab === 'profile'}
		<div class="rounded-xl border bg-card p-6 space-y-5">
			<div>
				<h2 class="font-semibold">Kimlik Bilgileri</h2>
				<p class="text-sm text-muted-foreground mt-0.5">Hesabınıza ait temel bilgiler.</p>
			</div>
			<div class="grid sm:grid-cols-2 gap-4">
				<div class="space-y-1.5">
					<label class="text-sm font-medium text-muted-foreground">Ad Soyad</label>
					<div class="h-9 px-3 flex items-center text-sm rounded-md border border-input bg-muted/30">
						{currentUser?.name ?? '—'}
					</div>
				</div>
				<div class="space-y-1.5">
					<label class="text-sm font-medium text-muted-foreground">E-posta</label>
					<div class="h-9 px-3 flex items-center text-sm rounded-md border border-input bg-muted/30">
						{currentUser?.email ?? '—'}
					</div>
				</div>
			</div>

			<div class="space-y-3">
				<h3 class="text-sm font-semibold">Şirket Üyelikleri</h3>
				{#each currentUser?.companies ?? [] as m}
					<div class="flex items-center justify-between px-3 py-2.5 rounded-lg border bg-muted/20 text-sm">
						<div class="flex items-center gap-2">
							<Building2 class="w-4 h-4 text-muted-foreground" />
							<span class="font-medium">{m.company_name}</span>
						</div>
						<Badge variant={m.role === 'founder' ? 'default' : 'secondary'}>
							{ROLE_LABELS[m.role] ?? m.role}
						</Badge>
					</div>
				{/each}
			</div>

			<p class="text-xs text-muted-foreground">Ad, e-posta ve üyelik değişiklikleri için yöneticinize başvurun.</p>
		</div>

	<!-- ── Tab: Güvenlik ─────────────────────────────────────────────────────── -->
	{:else if activeTab === 'security'}
		<div class="rounded-xl border bg-card p-6 space-y-5">
			<div>
				<h2 class="font-semibold">Şifre Değiştir</h2>
				<p class="text-sm text-muted-foreground mt-0.5">Hesap güvenliğiniz için güçlü bir şifre kullanın.</p>
			</div>

			<div class="space-y-4 max-w-sm">
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="pw-new">Yeni Şifre</label>
					<div class="relative">
						<Input id="pw-new" type={showNext ? 'text' : 'password'} bind:value={passwords.next} class="pr-10" autocomplete="new-password" />
						<button type="button" onclick={() => (showNext = !showNext)}
							class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
							aria-label={showNext ? 'Gizle' : 'Göster'}>
							{#if showNext}<EyeOff class="w-4 h-4" />{:else}<Eye class="w-4 h-4" />{/if}
						</button>
					</div>
					{#if passwords.next}
						<div class="space-y-1">
							<div class="flex gap-1">
								{#each [1,2,3,4] as n}
									<div class="h-1 flex-1 rounded-full {n <= pwStrength() ? pwStrengthColor : 'bg-muted'} transition-all"></div>
								{/each}
							</div>
							<p class="text-xs text-muted-foreground">{pwStrengthLabel}</p>
						</div>
					{/if}
				</div>

				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="pw-confirm">Şifre Tekrar</label>
					<div class="relative">
						<Input id="pw-confirm" type={showConfirm ? 'text' : 'password'} bind:value={passwords.confirm} class="pr-10" autocomplete="new-password" />
						<button type="button" onclick={() => (showConfirm = !showConfirm)}
							class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
							aria-label={showConfirm ? 'Gizle' : 'Göster'}>
							{#if showConfirm}<EyeOff class="w-4 h-4" />{:else}<Eye class="w-4 h-4" />{/if}
						</button>
					</div>
					{#if passwords.confirm && passwords.next !== passwords.confirm}
						<p class="text-xs text-destructive">Şifreler eşleşmiyor</p>
					{/if}
				</div>
			</div>

			{#if pwError}
				<p class="text-sm text-destructive">{pwError}</p>
			{/if}

			<div class="flex items-center gap-3 pt-1">
				{#if pwSaved}
					<span class="text-sm text-emerald-600 flex items-center gap-1.5">
						<CheckCircle2 class="w-4 h-4" /> Şifre güncellendi
					</span>
				{/if}
				<Button
					onclick={savePassword}
					disabled={pwSaving || !passwords.next || passwords.next !== passwords.confirm || passwords.next.length < 8}
				>
					<KeyRound class="w-4 h-4" />
					{pwSaving ? 'Güncelleniyor...' : 'Şifreyi Güncelle'}
				</Button>
			</div>
		</div>
	{/if}

</div>
