<script lang="ts">
	import { goto } from '$app/navigation';
	import { Layers, Mail, Lock, Loader } from '@lucide/svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { companyStore } from '$lib/stores/company.svelte';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function submit(e: Event) {
		e.preventDefault();
		if (!email.trim() || !password) return;
		loading = true;
		error = '';
		try {
			const user = await authStore.login(email.trim().toLowerCase(), password);
			// Load companies then redirect
			await companyStore.load();
			if (user.must_change_password) {
				goto('/set-password?mode=first');
				return;
			}
			// Role-based redirect
			const firstCompany = user.companies[0];
			const role = firstCompany?.role;
			if (role === 'agent_owner') goto('/agents');
			else if (role === 'user') goto('/inbox');
			else goto('/');
		} catch (e: any) {
			error = e?.message ?? 'Giriş başarısız';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Giriş • fab.engineering</title>
</svelte:head>

<div class="min-h-screen bg-background flex items-center justify-center p-4">
	<div class="w-full max-w-sm">
		<!-- Logo -->
		<div class="flex items-center justify-center gap-2.5 mb-8">
			<div class="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
				<Layers class="w-6 h-6 text-primary-foreground" />
			</div>
			<div class="flex items-baseline">
				<span class="font-bold text-2xl tracking-tighter">fab</span>
				<span class="font-semibold text-2xl tracking-tighter text-muted-foreground">.engineering</span>
			</div>
		</div>

		<!-- Card -->
		<div class="rounded-2xl border bg-card p-8 shadow-sm">
			<h1 class="font-display text-xl tracking-tight text-center mb-1">Giriş Yapın</h1>
			<p class="text-sm text-muted-foreground text-center mb-6">Devam etmek için hesabınıza giriş yapın</p>

			<form onsubmit={submit} class="space-y-4">
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="email">E-posta</label>
					<div class="relative">
						<Mail class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
						<Input
							id="email"
							type="email"
							bind:value={email}
							placeholder="ad@sirket.com"
							class="pl-9"
							autocomplete="email"
							required
						/>
					</div>
				</div>

				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="password">Şifre</label>
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
						Giriş yapılıyor...
					{:else}
						Giriş Yap
					{/if}
				</Button>
			</form>

			<div class="mt-5 pt-4 border-t text-center">
				<a href="/request-reset" class="text-xs text-muted-foreground hover:text-foreground transition-colors">
					Şifremi unuttum → yöneticiden sıfırlama talep et
				</a>
			</div>
		</div>
	</div>
</div>
