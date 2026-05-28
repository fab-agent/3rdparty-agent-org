<script>
	let organizations = [];
	let loading = true;
	let showForm = false;
	let newOrg = { name: '', slug: '', description: '' };

	async function loadOrganizations() {
		loading = true;
		try {
			const res = await fetch('http://localhost:8000/organizations');
			organizations = await res.json();
		} catch (e) {
			console.error(e);
		}
		loading = false;
	}

	async function createOrganization() {
		if (!newOrg.name || !newOrg.slug) return;

		try {
			const res = await fetch('http://localhost:8000/organizations', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newOrg)
			});
			if (res.ok) {
				await loadOrganizations();
				showForm = false;
				newOrg = { name: '', slug: '', description: '' };
			}
		} catch (e) {
			alert('Hata oluştu: ' + e);
		}
	}

	loadOrganizations();
</script>

<svelte:head>
	<title>Organizasyonlar • 3rdParty Agent</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-semibold tracking-tight">Organizasyonlar</h1>
			<p class="text-slate-600 mt-1">Tüm organizasyonları görüntüle ve yönet</p>
		</div>
		<button 
			on:click={() => showForm = true}
			class="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-black transition-colors">
			+ Yeni Organizasyon
		</button>
	</div>

	{#if loading}
		<div class="text-slate-500">Yükleniyor...</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each organizations as org}
				<div class="bg-white border rounded-2xl p-5 hover:shadow-sm transition-all">
					<div class="font-semibold text-lg">{org.name}</div>
					<div class="text-sm text-slate-500 mt-0.5">/{org.slug}</div>
					{#if org.description}
						<div class="text-sm text-slate-600 mt-3 line-clamp-2">{org.description}</div>
					{/if}
					<div class="mt-4 text-xs text-emerald-600">Detayları gör →</div>
				</div>
			{:else}
				<div class="col-span-full text-center py-12 text-slate-500">
					Henüz organizasyon yok.
				</div>
			{/each}
		</div>
	{/if}
</div>

{#if showForm}
	<div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" on:click={() => showForm = false}>
		<div class="bg-white w-full max-w-md rounded-3xl p-6" on:click|stopPropagation>
			<div class="font-semibold text-xl mb-5">Yeni Organizasyon Oluştur</div>
			
			<div class="space-y-4">
				<div>
					<label class="text-xs text-slate-500 block mb-1">Organizasyon Adı</label>
					<input bind:value={newOrg.name} type="text" class="w-full border rounded-xl px-4 h-11" placeholder="Acme Corp">
				</div>
				<div>
					<label class="text-xs text-slate-500 block mb-1">Slug (URL için)</label>
					<input bind:value={newOrg.slug} type="text" class="w-full border rounded-xl px-4 h-11" placeholder="acme-corp">
				</div>
				<div>
					<label class="text-xs text-slate-500 block mb-1">Açıklama (opsiyonel)</label>
					<textarea bind:value={newOrg.description} class="w-full border rounded-xl px-4 py-3 h-20 resize-none" placeholder="Kısa açıklama..."></textarea>
				</div>
			</div>

			<div class="mt-6 flex gap-3">
				<button on:click={() => showForm = false} class="flex-1 h-11 rounded-xl border text-sm">İptal</button>
				<button on:click={createOrganization} class="flex-1 h-11 rounded-xl bg-slate-900 text-white text-sm font-medium">Oluştur</button>
			</div>
		</div>
	</div>
{/if}