<script>
	let title = 'Dashboard';
</script>

<svelte:head>
	<title>{title} • 3rdParty Agent</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h1 class="text-3xl font-semibold tracking-tight">Dashboard</h1>
		<p class="text-slate-600 mt-1">3rdParty Agent Organization platformuna hoş geldin.</p>
	</div>

	<div class="grid grid-cols-1 md:grid-cols-3 gap-6">
		<div class="bg-white border rounded-2xl p-6">
			<div class="text-sm text-slate-500">Organizasyon</div>
			<div class="text-3xl font-semibold mt-2">—</div>
		</div>
		<div class="bg-white border rounded-2xl p-6">
			<div class="text-sm text-slate-500">Personel</div>
			<div class="text-3xl font-semibold mt-2">—</div>
		</div>
		<div class="bg-white border rounded-2xl p-6">
			<div class="text-sm text-slate-500">Aktif Ajan</div>
			<div class="text-3xl font-semibold mt-2">—</div>
		</div>
	</div>
</div>