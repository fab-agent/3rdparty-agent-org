<script>
	import '../app.css';
</script>

<div class="min-h-screen bg-slate-50">
	<nav class="border-b bg-white">
		<div class="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
			<div class="flex items-center gap-3">
				<div class="w-8 h-8 bg-slate-900 rounded-xl flex items-center justify-center">
					<span class="text-white text-sm font-bold">3P</span>
				</div>
				<span class="font-semibold text-xl">3rdParty Agent</span>
			</div>
			<div class="flex gap-6 text-sm">
				<a href="/" class="hover:text-slate-600">Dashboard</a>
				<a href="/organizations" class="hover:text-slate-600">Organizasyonlar</a>
				<a href="/personnel" class="hover:text-slate-600">Personel</a>
			</div>
		</div>
	</nav>

	<main class="max-w-7xl mx-auto px-6 py-8">
		<slot />
	</main>
</div>