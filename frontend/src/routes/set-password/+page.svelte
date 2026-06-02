<script lang="ts">
	import { goto } from '$app/navigation';
	import { Layers, Lock, Eye, EyeOff, Loader } from '@lucide/svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { companyStore } from '$lib/stores/company.svelte';

	let password = $state('');
	let confirm = $state('');
	let showPass = $state(false);
	let error = $state('');
	let loading = $state(false);
	let done = $state(false);

	const strength = $derived(() => {
		if (password.length === 0) return 0;
		let s = 0;
		if (password.length >= 8) s++;
		if (/[A-Z]/.test(password)) s++;
		if (/[0-9]/.test(password)) s++;
		if (/[^A-Za-z0-9]/.test(password)) s++;
		return s;
	});

	const strengthLabel = $derived(
		strength() === 0 ? '' :
		strength() === 1 ? 'Zayıf' :
		strength() === 2 ? 'Orta' :
		strength() === 3 ? 'İyi' : 'Güçlü'
	);

	const strengthColor = $derived(
		strength() <= 1 ? 'bg-destructive' :
		strength() === 2 ? 'bg-amber-500' :
		strength() === 3 ? 'bg-yellow-500' : 'bg-emerald-500'
	);

	async function submit(e: Event) {
		e.preventDefault();
		if (password !== confirm) { error = 'Şifreler eşleşmiyor'; return; }
		if (password.length < 8) { error = 'En az 8 karakter gerekli'; return; }

		loading = true;
		error = '';
		try {
			await authStore.changePassword(password);
			await companyStore.load();
			done = true;
			setTimeout(() => goto('/'), 1500);
		} catch (e: any) {
			error = e?.message ?? 'Bir hata oluştu';
		} finally {
			loading = false;
		}
	}
</script>

<svelte:head>
	<title>Şifre Belirle • fab.engineering</title>
</svelte:head>

<div class="min-h-screen bg-background flex items-center justify-center p-4">
	<div class="w-full max-w-sm">
		<div class="flex items-center justify-center gap-2.5 mb-8">
			<div class="w-12 h-12 bg-primary rounded-xl flex items-center justify-center">
				<Layers class="w-6 h-6 text-primary-foreground" />
			</div>
			<div class="flex items-baseline">
				<span class="font-bold text-2xl tracking-tighter">fab</span>
				<span class="font-semibold text-2xl tracking-tighter text-muted-foreground">.engineering</span>
			</div>
		</div>

		<div class="rounded-2xl border bg-card p-8 shadow-sm">
			{#if done}
				<div class="text-center py-4">
					<div class="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-3">
						<div class="w-6 h-6 rounded-full bg-emerald-500"></div>
					</div>
					<h1 class="font-display text-lg tracking-tight mb-1">Şifreniz belirlendi!</h1>
					<p class="text-sm text-muted-foreground">Yönlendiriliyorsunuz...</p>
				</div>
			{:else}
				<h1 class="font-display text-xl tracking-tight text-center mb-1">Şifrenizi Belirleyin</h1>
				<p class="text-sm text-muted-foreground text-center mb-6">
					İlk girişinizde kalıcı şifrenizi oluşturun.
				</p>

				<form onsubmit={submit} class="space-y-4">
					<div class="space-y-1.5">
						<label class="text-sm font-medium" for="pw">Yeni Şifre</label>
						<div class="relative">
							<Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
							<Input
								id="pw"
								type={showPass ? 'text' : 'password'}
								bind:value={password}
								placeholder="En az 8 karakter"
								class="pl-9 pr-10"
								autocomplete="new-password"
							/>
							<button
								type="button"
								class="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
								onclick={() => (showPass = !showPass)}
							>
								{#if showPass}<EyeOff class="w-4 h-4" />{:else}<Eye class="w-4 h-4" />{/if}
							</button>
						</div>
						{#if password.length > 0}
							<div class="flex items-center gap-2 mt-1.5">
								<div class="flex gap-0.5 flex-1">
									{#each [1,2,3,4] as i}
										<div class="h-1 flex-1 rounded-full {i <= strength() ? strengthColor : 'bg-muted'}"></div>
									{/each}
								</div>
								<span class="text-xs text-muted-foreground">{strengthLabel}</span>
							</div>
						{/if}
					</div>

					<div class="space-y-1.5">
						<label class="text-sm font-medium" for="confirm">Şifre Tekrar</label>
						<div class="relative">
							<Lock class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
							<Input
								id="confirm"
								type={showPass ? 'text' : 'password'}
								bind:value={confirm}
								placeholder="Tekrar girin"
								class="pl-9"
								autocomplete="new-password"
							/>
						</div>
						{#if confirm && confirm !== password}
							<p class="text-xs text-destructive">Şifreler eşleşmiyor</p>
						{/if}
					</div>

					{#if error}
						<div class="rounded-lg bg-destructive/10 border border-destructive/20 px-3 py-2.5 text-sm text-destructive">
							{error}
						</div>
					{/if}

					<Button
						type="submit"
						class="w-full"
						disabled={loading || !password || password !== confirm || password.length < 8}
					>
						{#if loading}
							<Loader class="w-4 h-4 animate-spin" />
							Kaydediliyor...
						{:else}
							Şifremi Kaydet
						{/if}
					</Button>
				</form>
			{/if}
		</div>
	</div>
</div>
