<script lang="ts">
	import { onMount } from 'svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Card from '$lib/components/ui/card.svelte';
	import {
		Users, Bot, MessageSquare, Zap, BrainCircuit, Clock,
		TrendingUp, Activity, UserCheck, Loader, ChevronRight,
		Cpu, Plus, RefreshCw, CheckCircle2, XCircle, Shield,
	} from '@lucide/svelte';
	import { dashboardApi, type CompanyStats, type MyDashboard, type VersionInfo, type AgentSla } from '$lib/api/dashboard';
	import { companyStore } from '$lib/stores/company.svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { t } from '$lib/i18n/index.svelte';

	let stats = $state<CompanyStats | null>(null);
	let myData = $state<MyDashboard | null>(null);
	let sla = $state<AgentSla | null>(null);
	let versionInfo = $state<VersionInfo | null>(null);
	let loading = $state(true);

	async function load() {
		loading = true;
		try {
			const cid = companyStore.active?.id;
			[stats, myData, sla] = await Promise.all([
				dashboardApi.stats(cid),
				dashboardApi.me(cid),
				dashboardApi.agentSla(cid),
			]);
		} catch {
			// ignore
		} finally {
			loading = false;
		}
	}

	onMount(async () => {
		load();
		try { versionInfo = await dashboardApi.version(); } catch { /* ignore */ }
	});
	$effect(() => { if (companyStore.active) load(); });

	const activeCompanyId = $derived(companyStore.active?.id ?? '');
	const isManager = $derived(authStore.can(activeCompanyId, 'dept_head'));
	const userName = $derived(authStore.user?.name?.split(' ')[0] ?? 'Merhaba');

	function fmtTokens(n: number): string {
		if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
		if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
		return String(n);
	}

	function fmtDate(iso: string): string {
		const d = new Date(iso);
		return d.toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
	}
</script>

<svelte:head>
	<title>Dashboard • fab.engineering</title>
</svelte:head>

<div class="space-y-8">

	<!-- Update notification banner -->
	{#if versionInfo?.update_available}
		<div class="flex items-center gap-3 rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm">
			<RefreshCw class="w-4 h-4 text-amber-500 shrink-0" />
			<span class="text-amber-700 dark:text-amber-400">
				Yeni sürüm mevcut: <strong>v{versionInfo.latest}</strong>
				(mevcut: v{versionInfo.current})
			</span>
			{#if versionInfo.release_url}
				<a
					href={versionInfo.release_url}
					target="_blank"
					rel="noopener noreferrer"
					class="ml-auto shrink-0 text-amber-600 dark:text-amber-400 underline underline-offset-2 hover:no-underline"
				>
					GitHub'da görüntüle →
				</a>
			{/if}
		</div>
	{/if}

	<!-- Header -->
	<div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="font-display text-3xl tracking-tight">Merhaba, {userName} 👋</h1>
			<p class="text-muted-foreground mt-1">
				{companyStore.active?.name ?? ''} · {new Date().toLocaleDateString('tr-TR', { weekday: 'long', day: 'numeric', month: 'long' })}
			</p>
		</div>
		{#if isManager}
			<a href="/personnel">
				<Button class="gap-x-2 w-full sm:w-auto">
					<Plus class="w-4 h-4" />
					{t('dash_new_personnel')}
				</Button>
			</a>
		{/if}
	</div>

	<!-- ── Company-wide telemetry (managers+) ─────────────────────────────── -->
	{#if isManager}
		<section>
			<div class="flex items-center gap-2 mb-4">
				<Activity class="w-4 h-4 text-muted-foreground" />
				<span class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Şirket Telemetrisi</span>
			</div>
			<div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
				{#if loading}
					{#each Array(6) as _}
						<Card class="p-4">
							<div class="h-3 w-16 bg-muted rounded animate-pulse mb-3"></div>
							<div class="h-8 w-10 bg-muted rounded animate-pulse"></div>
						</Card>
					{/each}
				{:else if stats}
					<Card class="p-4">
						<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
							<Users class="w-3.5 h-3.5" /> İnsan
						</div>
						<div class="text-3xl font-semibold tracking-tighter">{stats.human_count}</div>
					</Card>
					<Card class="p-4">
						<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
							<Bot class="w-3.5 h-3.5" /> Ajan
						</div>
						<div class="text-3xl font-semibold tracking-tighter">{stats.agent_count}</div>
						<div class="text-xs text-emerald-600 font-medium mt-1">{stats.active_agents} aktif</div>
					</Card>
					<Card class="p-4">
						<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
							<MessageSquare class="w-3.5 h-3.5" /> Bugün Oturum
						</div>
						<div class="text-3xl font-semibold tracking-tighter">{stats.today_sessions}</div>
						<div class="text-xs text-muted-foreground mt-1">{stats.total_sessions} toplam</div>
					</Card>
					<Card class="p-4">
						<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
							<Activity class="w-3.5 h-3.5" /> Aktif Oturum
						</div>
						<div class="text-3xl font-semibold tracking-tighter {stats.active_sessions > 0 ? 'text-emerald-600' : ''}">{stats.active_sessions}</div>
					</Card>
					<Card class="p-4">
						<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
							<Zap class="w-3.5 h-3.5" /> Token (Bugün)
						</div>
						<div class="text-3xl font-semibold tracking-tighter">{fmtTokens(stats.today_tokens)}</div>
						<div class="text-xs text-muted-foreground mt-1">{fmtTokens(stats.total_tokens)} toplam</div>
					</Card>
					<Card class="p-4">
						<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
							<BrainCircuit class="w-3.5 h-3.5" /> Hafıza
						</div>
						<div class="text-3xl font-semibold tracking-tighter">{stats.memory_count}</div>
						<div class="text-xs text-muted-foreground mt-1">uzun dönem</div>
					</Card>
				{/if}
			</div>
		</section>
	{/if}

	<!-- ── Personal dashboard ─────────────────────────────────────────────── -->
	{#if myData?.linked}
		<section>
			<div class="flex items-center gap-2 mb-4">
				<UserCheck class="w-4 h-4 text-muted-foreground" />
				<span class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Benim Aktivitem</span>
				{#if myData.personnel_name}
					<span class="text-xs text-muted-foreground">· {myData.personnel_name}</span>
				{/if}
			</div>

			<!-- Personal stats row -->
			<div class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
				<Card class="p-4">
					<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
						<MessageSquare class="w-3.5 h-3.5" /> Bugün Oturum
					</div>
					<div class="text-3xl font-semibold tracking-tighter">{myData.today_sessions ?? 0}</div>
					<div class="text-xs text-muted-foreground mt-1">{myData.total_sessions ?? 0} toplam</div>
				</Card>
				<Card class="p-4">
					<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
						<Activity class="w-3.5 h-3.5" /> Aktif Oturum
					</div>
					<div class="text-3xl font-semibold tracking-tighter {(myData.active_sessions ?? 0) > 0 ? 'text-emerald-600' : ''}">{myData.active_sessions ?? 0}</div>
				</Card>
				<Card class="p-4">
					<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
						<Zap class="w-3.5 h-3.5" /> Token (Bugün)
					</div>
					<div class="text-3xl font-semibold tracking-tighter">{fmtTokens(myData.today_tokens ?? 0)}</div>
					<div class="text-xs text-muted-foreground mt-1">{fmtTokens(myData.total_tokens ?? 0)} toplam</div>
				</Card>
				<Card class="p-4">
					<div class="flex items-center gap-1.5 text-xs text-muted-foreground mb-2">
						<BrainCircuit class="w-3.5 h-3.5" /> Hafıza
					</div>
					<div class="text-3xl font-semibold tracking-tighter">{myData.memories?.length ?? 0}</div>
					<div class="text-xs text-muted-foreground mt-1">uzun dönem</div>
				</Card>
			</div>

			<div class="grid lg:grid-cols-2 gap-6">

				<!-- Recent sessions -->
				<Card class="p-5">
					<div class="flex items-center justify-between mb-4">
						<div class="flex items-center gap-2">
							<MessageSquare class="w-4 h-4 text-muted-foreground" />
							<span class="font-semibold text-sm">Son Oturumlar</span>
						</div>
						<a href="/agents" class="text-xs text-muted-foreground hover:text-foreground flex items-center gap-1 transition-colors">
							Tümü <ChevronRight class="w-3 h-3" />
						</a>
					</div>
					{#if loading}
						<div class="space-y-2">
							{#each Array(3) as _}
								<div class="h-12 bg-muted rounded-lg animate-pulse"></div>
							{/each}
						</div>
					{:else if !myData.recent_sessions?.length}
						<div class="flex flex-col items-center justify-center py-8 text-center gap-2">
							<MessageSquare class="w-8 h-8 text-muted-foreground/40" />
							<p class="text-sm text-muted-foreground">Henüz oturum yok.</p>
						</div>
					{:else}
						<div class="space-y-2">
							{#each myData.recent_sessions as s}
								<div class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-muted/30 border border-border/50 hover:bg-muted/50 transition-colors">
									<div class="w-2 h-2 rounded-full flex-shrink-0 {s.status === 'active' ? 'bg-emerald-500 animate-pulse' : 'bg-muted-foreground/30'}"></div>
									<div class="flex-1 min-w-0">
										<div class="text-sm font-medium truncate">{s.title ?? 'Oturum'}</div>
										<div class="text-xs text-muted-foreground">{fmtDate(s.updated_at)}</div>
									</div>
									<span class="text-xs px-2 py-0.5 rounded-md font-medium flex-shrink-0
										{s.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-muted text-muted-foreground'}">
										{s.status === 'active' ? 'Aktif' : 'Kapalı'}
									</span>
								</div>
							{/each}
						</div>
					{/if}
				</Card>

				<!-- Memories -->
				<Card class="p-5">
					<div class="flex items-center gap-2 mb-4">
						<BrainCircuit class="w-4 h-4 text-muted-foreground" />
						<span class="font-semibold text-sm">Uzun Dönem Hafıza</span>
					</div>
					{#if loading}
						<div class="space-y-2">
							{#each Array(2) as _}
								<div class="h-16 bg-muted rounded-lg animate-pulse"></div>
							{/each}
						</div>
					{:else if !myData.memories?.length}
						<div class="flex flex-col items-center justify-center py-8 text-center gap-2">
							<BrainCircuit class="w-8 h-8 text-muted-foreground/40" />
							<p class="text-sm text-muted-foreground">Henüz hafıza özeti yok.</p>
							<p class="text-xs text-muted-foreground">Oturumlar kapandığında AI özet oluşturur.</p>
						</div>
					{:else}
						<div class="space-y-2 max-h-64 overflow-y-auto">
							{#each myData.memories as m}
								<div class="rounded-lg border border-border bg-muted/30 px-3 py-2.5">
									<p class="text-xs leading-relaxed text-foreground/80">{m.summary}</p>
									<div class="flex items-center gap-1 mt-1.5 text-xs text-muted-foreground">
										<Clock class="w-3 h-3" />
										{new Date(m.created_at).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short', year: 'numeric' })}
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</Card>

			</div>
		</section>
	{/if}

	<!-- ── Agent SLA (managers+) ────────────────────────────────────────────── -->
	{#if isManager && (sla?.agents?.length ?? 0) > 0}
		<section>
			<div class="flex items-center gap-2 mb-4">
				<Shield class="w-4 h-4 text-muted-foreground" />
				<span class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Ajan SLA & Başarı Oranı</span>
			</div>
			<Card class="overflow-hidden">
				<div class="overflow-x-auto">
					<table class="w-full text-sm">
						<thead>
							<tr class="border-b border-border/60 bg-muted/30">
								<th class="text-left px-4 py-3 font-medium text-muted-foreground text-xs">Ajan</th>
								<th class="text-right px-4 py-3 font-medium text-muted-foreground text-xs">Oturum</th>
								<th class="text-right px-4 py-3 font-medium text-muted-foreground text-xs">Token</th>
								<th class="text-right px-4 py-3 font-medium text-muted-foreground text-xs">Flow</th>
								<th class="text-right px-4 py-3 font-medium text-muted-foreground text-xs">Görev</th>
								<th class="text-right px-4 py-3 font-medium text-muted-foreground text-xs">Başarı</th>
							</tr>
						</thead>
						<tbody>
							{#each sla?.agents ?? [] as row}
								<tr class="border-b border-border/40 hover:bg-muted/20 transition-colors">
									<td class="px-4 py-3">
										<div class="font-medium">{row.name}</div>
										{#if row.title}
											<div class="text-xs text-muted-foreground">{row.title}</div>
										{/if}
									</td>
									<td class="px-4 py-3 text-right tabular-nums">
										<span>{row.total_sessions}</span>
										{#if row.active_sessions > 0}
											<span class="ml-1 text-xs text-emerald-600">({row.active_sessions} aktif)</span>
										{/if}
									</td>
									<td class="px-4 py-3 text-right tabular-nums text-muted-foreground">
										{fmtTokens(row.total_tokens)}
									</td>
									<td class="px-4 py-3 text-right tabular-nums">
										{#if row.flow_count > 0}
											<span class="text-emerald-600">{row.flow_success}✓</span>
											{#if row.flow_error > 0}
												<span class="ml-1 text-destructive">{row.flow_error}✗</span>
											{/if}
										{:else}
											<span class="text-muted-foreground">—</span>
										{/if}
									</td>
									<td class="px-4 py-3 text-right tabular-nums">
										{#if row.task_total > 0}
											{row.task_completed}/{row.task_total}
										{:else}
											<span class="text-muted-foreground">—</span>
										{/if}
									</td>
									<td class="px-4 py-3 text-right">
										{#if row.success_rate !== null}
											<span class="inline-flex items-center gap-1 font-semibold tabular-nums
												{row.success_rate >= 90 ? 'text-emerald-600' : row.success_rate >= 70 ? 'text-amber-600' : 'text-destructive'}">
												{#if row.success_rate >= 90}
													<CheckCircle2 class="w-3.5 h-3.5" />
												{:else}
													<XCircle class="w-3.5 h-3.5" />
												{/if}
												{row.success_rate}%
											</span>
										{:else}
											<span class="text-muted-foreground text-xs">Veri yok</span>
										{/if}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</Card>
		</section>
	{/if}

	<!-- ── Quick links (all users) ────────────────────────────────────────── -->
	<section>
		<div class="flex items-center gap-2 mb-4">
			<TrendingUp class="w-4 h-4 text-muted-foreground" />
			<span class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Hızlı Erişim</span>
		</div>
		<div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
			{#each [
				{ href: '/agents',    label: 'Ajanlar',    icon: Bot,           desc: 'Agent yönetimi' },
				{ href: '/personnel', label: 'Personel',   icon: Users,         desc: 'Ekip üyeleri' },
				{ href: '/settings',  label: 'Ayarlar',    icon: Cpu,           desc: 'AI sağlayıcıları' },
				{ href: '/orgtree',   label: 'Org Şeması', icon: TrendingUp,    desc: 'Hiyerarşi görünümü' },
			] as item}
				<a href={item.href} class="block">
					<Card class="p-4 hover:border-primary/40 hover:shadow-sm transition-all cursor-pointer h-full">
						<div class="w-8 h-8 rounded-lg bg-muted flex items-center justify-center mb-3">
							<item.icon class="w-4 h-4 text-muted-foreground" />
						</div>
						<div class="font-medium text-sm">{item.label}</div>
						<div class="text-xs text-muted-foreground mt-0.5">{item.desc}</div>
					</Card>
				</a>
			{/each}
		</div>
	</section>

</div>
