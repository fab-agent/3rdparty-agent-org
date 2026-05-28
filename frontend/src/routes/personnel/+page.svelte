<script>
	let personnel = [];
	let organizations = [];
	let loading = true;
	let showForm = false;
	let newPerson = { organization_id: '', name: '', slug: '', role: '' };

	async function loadData() {
		loading = true;
		try {
			const [orgRes, perRes] = await Promise.all([
				fetch('http://localhost:8000/organizations'),
				fetch('http://localhost:8000/personnel')
			]);
			organizations = await orgRes.json();
			personnel = await perRes.json();
		} catch (e) {
			console.error(e);
		}
		loading = false;
	}

	async function createPersonnel() {
		if (!newPerson.name || !newPerson.slug || !newPerson.organization_id) return;

		try {
			const res = await fetch('http://localhost:8000/personnel', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(newPerson)
			});
			if (res.ok) {
				await loadData();
				showForm = false;
				newPerson = { organization_id: '', name: '', slug: '', role: '' };
			}
		} catch (e) {
			alert('Hata: ' + e);
		}
	}

	loadData();
</script>

<svelte:head>
	<title>Personel • 3rdParty Agent</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-3xl font-semibold tracking-tight">Personel</h1>
			<p class="text-slate-600 mt-1">Tüm personeli görüntüle ve yönet</p>
		</div>
		<button 
			on:click={() => showForm = true}
			class="px-4 py-2 bg-slate-900 text-white rounded-xl text-sm font-medium hover:bg-black transition-colors">
			+ Yeni Personel
		</button>
	</div>

	{#if loading}
		<div class="text-slate-500">Yükleniyor...</div>
	{:else}
		<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
			{#each personnel as person}
				<div class="bg-white border rounded-2xl p-5">
					<div class="font-semibold text-lg">{person.name}</div>
					<div class="text-sm text-slate-500 mt-0.5">/{person.slug}</div>
					<div class="mt-2 text-sm text-slate-600">{person.role || 'Rol belirtilmemiş'}</div>
					<div class="mt-4 text-xs text-emerald-600">Detayları gör →</div>
				</div>
			{:else}
				<div class="col-span-full text-center py-12 text-slate-500">
					Henüz personel yok.
				</div>
			{/each}
		</div>
	{/if}
</div>

{#if showForm}
	<div class="fixed inset-0 bg-black/40 flex items-center justify-center z-50" on:click={() => showForm = false}>
		<div class="bg-white w-full max-w-md rounded-3xl p-6" on:click|stopPropagation>
			<div class="font-semibold text-xl mb-5">Yeni Personel Ekle</div>
			
			<div class="space-y-4">
				<div>
					<label class="text-xs text-slate-500 block mb-1">Organizasyon</label>
					<select bind:value={newPerson.organization_id} class="w-full border rounded-xl px-4 h-11">
						<option value="">Seçiniz...</option>
						{#each organizations as org}
							<option value={org.id}>{org.name}</option>
						{/each}
					</select>
				</div>
				<div>
					<label class="text-xs text-slate-500 block mb-1">Ad Soyad</label>
					<input bind:value={newPerson.name} type="text" class="w-full border rounded-xl px-4 h-11" placeholder="Ahmet Yılmaz">
				</div>
				<div>
					<label class="text-xs text-slate-500 block mb-1">Slug</label>
					<input bind:value={newPerson.slug} type="text" class="w-full border rounded-xl px-4 h-11" placeholder="ahmet-yilmaz">
				</div>
				<div>
					<label class="text-xs text-slate-500 block mb-1">Rol / Ünvan</label>
					<input bind:value={newPerson.role} type="text" class="w-full border rounded-xl px-4 h-11" placeholder="Yazılım Mühendisi">
				</div>
			</div>

			<div class="mt-6 flex gap-3">
				<button on:click={() => showForm = false} class="flex-1 h-11 rounded-xl border text-sm">İptal</button>
				<button on:click={createPersonnel} class="flex-1 h-11 rounded-xl bg-slate-900 text-white text-sm font-medium">Ekle</button>
			</div>
		</div>
	</div>
{/if}