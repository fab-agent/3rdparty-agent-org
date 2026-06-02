<script lang="ts">
	import { onMount } from 'svelte';
	import {
		ArrowRight,
		CheckCircle2,
		XCircle,
		Clock,
		Loader2,
		Bot,
		RefreshCw,
		ChevronDown,
		ChevronUp
	} from '@lucide/svelte';
	import Button from '$lib/components/ui/button.svelte';
	import MessageContent from '$lib/components/MessageContent.svelte';
	import { a2aApi, statusLabel, statusColor, type A2ARequest } from '$lib/api/a2a';
	import { personnel as personnelApi } from '$lib/api/personnel';
	import { companyStore } from '$lib/stores/company.svelte';
	import { t } from '$lib/i18n/index.svelte';

	let requests = $state<A2ARequest[]>([]);
	let loading = $state(true);
	let activeTab = $state<'pending' | 'all'>('pending');
	let expandedId = $state<string | null>(null);
	let actioning = $state<string | null>(null);

	let humanPersonnel = $state<{ id: string; name: string }[]>([]);
	let selectedApproverId = $state('');

	onMount(async () => {
		await load();
	});

	$effect(() => {
		if (companyStore.active) load();
	});

	async function load() {
		loading = true;
		try {
			const [reqs, humans] = await Promise.all([
				a2aApi.list({ company_id: companyStore.active?.id }),
				personnelApi.list({ type: 'human', company_id: companyStore.active?.id }),
			]);
			requests = reqs;
			humanPersonnel = humans.map((p) => ({ id: p.id, name: p.name }));
			if (humanPersonnel.length > 0 && !selectedApproverId) {
				selectedApproverId = humanPersonnel[0].id;
			}
		} catch {
			requests = [];
		} finally {
			loading = false;
		}
	}

	function filteredRequests() {
		if (activeTab === 'pending') {
			return requests.filter(
				(r) => r.status === 'pending_approval' || r.status === 'pending_result_approval'
			);
		}
		return requests;
	}

	async function approve(req: A2ARequest) {
		actioning = req.id;
		try {
			await a2aApi.approve(req.id, selectedApproverId || req.approver_id || '');
			await load();
		} finally {
			actioning = null;
		}
	}

	async function approveResult(req: A2ARequest) {
		actioning = req.id;
		try {
			await a2aApi.approveResult(req.id, selectedApproverId || req.approver_id || '');
			await load();
		} finally {
			actioning = null;
		}
	}

	async function reject(req: A2ARequest, reason: string) {
		actioning = req.id;
		try {
			await a2aApi.reject(req.id, selectedApproverId || req.approver_id || '', reason);
			await load();
		} finally {
			actioning = null;
		}
	}

	function fmtDate(iso: string) {
		return new Date(iso).toLocaleString('tr', { dateStyle: 'short', timeStyle: 'short' });
	}
</script>

<svelte:head><title>A2A • fab.engineering</title></svelte:head>

<div class="p-6 max-w-4xl mx-auto">
	<!-- Header -->
	<div class="flex items-center justify-between mb-6">
		<div>
			<h1 class="text-xl font-semibold">{t('a2a_title')}</h1>
			<p class="text-sm text-muted-foreground mt-0.5">
				{t('a2a_subtitle')}
			</p>
		</div>
		<div class="flex items-center gap-3">
			<!-- Approver picker -->
			{#if humanPersonnel.length > 0}
				<div class="flex items-center gap-2">
					<span class="text-xs text-muted-foreground">{t('a2a_approver_label')}</span>
					<select
						bind:value={selectedApproverId}
						class="text-sm px-2 py-1.5 rounded-lg border border-border bg-background"
					>
						{#each humanPersonnel as p}
							<option value={p.id}>{p.name}</option>
						{/each}
					</select>
				</div>
			{/if}
			<Button variant="outline" size="sm" onclick={load} class="gap-2">
				<RefreshCw class="w-3.5 h-3.5" />
				{t('a2a_refresh')}
			</Button>
		</div>
	</div>

	<!-- Tabs -->
	<div class="flex gap-1 p-1 bg-muted/40 rounded-xl mb-4 w-fit">
		{#each [{ key: 'pending', label: t('a2a_tab_pending') }, { key: 'all', label: t('a2a_tab_all') }] as tab}
			<button
				class="px-4 py-1.5 rounded-lg text-sm font-medium transition-colors
					{activeTab === tab.key ? 'bg-background shadow-sm text-foreground' : 'text-muted-foreground hover:text-foreground'}"
				onclick={() => (activeTab = tab.key as 'pending' | 'all')}
			>
				{tab.label}
				{#if tab.key === 'pending'}
					{@const count = requests.filter((r) => r.status === 'pending_approval' || r.status === 'pending_result_approval').length}
					{#if count > 0}
						<span class="ml-1.5 px-1.5 py-0.5 rounded-full text-xs bg-amber-100 text-amber-700 font-semibold">
							{count}
						</span>
					{/if}
				{/if}
			</button>
		{/each}
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-16 text-muted-foreground">
			<Loader2 class="w-5 h-5 animate-spin" />
		</div>
	{:else if filteredRequests().length === 0}
		<div class="text-center py-16 text-muted-foreground">
			<Bot class="w-12 h-12 mx-auto mb-3 opacity-20" />
			<p class="text-sm">{activeTab === 'pending' ? t('a2a_no_pending') : t('a2a_no_requests')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each filteredRequests() as req (req.id)}
				<div class="border border-border rounded-2xl overflow-hidden bg-card">
					<!-- Request header -->
					<!-- svelte-ignore a11y_click_events_have_key_events -->
					<!-- svelte-ignore a11y_no_static_element_interactions -->
					<div
						class="flex items-start gap-3 p-4 cursor-pointer hover:bg-muted/20 transition-colors"
						onclick={() => (expandedId = expandedId === req.id ? null : req.id)}
					>
						<!-- Status icon -->
						<div class="mt-0.5 flex-shrink-0">
							{#if req.status === 'completed'}
								<CheckCircle2 class="w-5 h-5 text-green-500" />
							{:else if req.status === 'rejected'}
								<XCircle class="w-5 h-5 text-red-500" />
							{:else if req.status === 'running'}
								<Loader2 class="w-5 h-5 text-blue-500 animate-spin" />
							{:else}
								<Clock class="w-5 h-5 text-amber-500" />
							{/if}
						</div>

						<div class="flex-1 min-w-0">
							<!-- Agents -->
							<div class="flex items-center gap-2 flex-wrap mb-1">
								<span class="text-sm font-medium">{req.from_agent_name ?? 'Ajan'}</span>
								<ArrowRight class="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
								<span class="text-sm font-medium">{req.to_agent_name ?? 'Ajan'}</span>
								<span class="ml-1 px-2 py-0.5 rounded-full text-xs border font-medium {statusColor(req.status)}">
									{statusLabel(req.status)}
								</span>
							</div>
							<!-- Task preview -->
							<p class="text-sm text-muted-foreground truncate">{req.task}</p>
							<p class="text-xs text-muted-foreground/60 mt-0.5">{fmtDate(req.created_at)}</p>
						</div>

						<div class="flex-shrink-0 ml-2 text-muted-foreground">
							{#if expandedId === req.id}
								<ChevronUp class="w-4 h-4" />
							{:else}
								<ChevronDown class="w-4 h-4" />
							{/if}
						</div>
					</div>

					<!-- Expanded detail -->
					{#if expandedId === req.id}
						<div class="border-t border-border p-4 space-y-4">
							<!-- Task -->
							<div>
								<div class="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">{t('a2a_task_label')}</div>
								<p class="text-sm leading-relaxed">{req.task}</p>
							</div>

							{#if req.context}
								<div>
									<div class="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">{t('a2a_context_label')}</div>
									<div class="text-sm bg-muted/30 rounded-xl p-3 text-muted-foreground">{req.context}</div>
								</div>
							{/if}

							<!-- Result (if available) -->
							{#if req.result}
								<div>
									<div class="text-xs font-medium text-muted-foreground uppercase tracking-wide mb-1.5">{t('a2a_result_label')}</div>
									<div class="bg-muted/20 rounded-xl p-3 border border-border">
										<MessageContent content={req.result} />
									</div>
								</div>
							{/if}

							<!-- Action buttons -->
							{#if req.status === 'pending_approval'}
								<div class="flex gap-2 pt-2">
									<Button
										onclick={() => approve(req)}
										disabled={actioning === req.id}
										class="gap-2"
									>
										{#if actioning === req.id}
											<Loader2 class="w-3.5 h-3.5 animate-spin" />
										{:else}
											<CheckCircle2 class="w-3.5 h-3.5" />
										{/if}
										{t('a2a_approve_run')}
									</Button>
									<Button
										variant="outline"
										onclick={() => reject(req, 'Manuel red')}
										disabled={actioning === req.id}
										class="gap-2 text-destructive hover:text-destructive"
									>
										<XCircle class="w-3.5 h-3.5" />
										{t('a2a_reject')}
									</Button>
								</div>
							{:else if req.status === 'pending_result_approval'}
								<div class="flex gap-2 pt-2">
									<Button
										onclick={() => approveResult(req)}
										disabled={actioning === req.id}
										class="gap-2"
									>
										{#if actioning === req.id}
											<Loader2 class="w-3.5 h-3.5 animate-spin" />
										{:else}
											<CheckCircle2 class="w-3.5 h-3.5" />
										{/if}
										{t('a2a_approve_result')}
									</Button>
									<Button
										variant="outline"
										onclick={() => reject(req, 'Sonuç uygunsuz')}
										disabled={actioning === req.id}
										class="gap-2 text-destructive hover:text-destructive"
									>
										<XCircle class="w-3.5 h-3.5" />
										{t('a2a_reject_result')}
									</Button>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
