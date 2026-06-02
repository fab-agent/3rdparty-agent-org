<script lang="ts">
	import { onMount } from 'svelte';
	import { flows as flowsApi, type Flow } from '$lib/api/flows';
	import { personnel as personnelApi, type PersonnelItem } from '$lib/api/personnel';
	import { companyStore } from '$lib/stores/company.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import {
		Zap, Plus, Pencil, Trash2, Play, X, CheckCircle2,
		XCircle, Clock, Loader, AlertCircle, ToggleLeft, ToggleRight
	} from '@lucide/svelte';
	import { t } from '$lib/i18n/index.svelte';

	const activeCompanyId = $derived(companyStore.active?.id ?? '');

	let flowList: Flow[] = $state([]);
	let agents: PersonnelItem[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);

	async function load() {
		if (!activeCompanyId) return;
		loading = true; error = null;
		try {
			const [f, p] = await Promise.all([
				flowsApi.list(activeCompanyId),
				personnelApi.list({ company_id: activeCompanyId, type: 'agent' }),
			]);
			flowList = f;
			agents = p;
		} catch (e) { error = (e as Error).message; }
		finally { loading = false; }
	}

	onMount(load);
	$effect(() => { if (companyStore.active) load(); });

	// ── Panel ─────────────────────────────────────────────────────────────────
	let panelOpen = $state(false);
	let saving = $state(false);
	let editingFlow: Flow | null = $state(null);

	type FormData = { personnel_id: string; name: string; description: string; schedule: string; prompt: string; enabled: boolean; };
	let form: FormData = $state({ personnel_id: '', name: '', description: '', schedule: '0 9 * * 1-5', prompt: '', enabled: true });

	function openCreate() {
		editingFlow = null;
		form = { personnel_id: '', name: '', description: '', schedule: '0 9 * * 1-5', prompt: '', enabled: true };
		panelOpen = true;
	}

	function openEdit(f: Flow) {
		editingFlow = f;
		form = { personnel_id: f.personnel_id, name: f.name, description: f.description ?? '', schedule: f.schedule, prompt: f.prompt, enabled: f.enabled };
		panelOpen = true;
	}

	async function save() {
		if (!form.name || !form.personnel_id || !form.schedule || !form.prompt) return;
		saving = true;
		try {
			if (editingFlow) {
				const updated = await flowsApi.update(editingFlow.id, form);
				flowList = flowList.map(f => f.id === editingFlow!.id ? updated : f);
			} else {
				const created = await flowsApi.create(form, activeCompanyId);
				flowList = [created, ...flowList];
			}
			panelOpen = false;
		} catch (e) { alert((e as Error).message); }
		finally { saving = false; }
	}

	let running: string | null = $state(null);
	async function runNow(id: string) {
		running = id;
		try {
			const updated = await flowsApi.run(id);
			flowList = flowList.map(f => f.id === id ? updated : f);
		} catch (e) { alert((e as Error).message); }
		finally { running = null; }
	}

	async function toggleEnabled(flow: Flow) {
		const updated = await flowsApi.update(flow.id, { enabled: !flow.enabled });
		flowList = flowList.map(f => f.id === flow.id ? updated : f);
	}

	let deleteTarget: Flow | null = $state(null);
	async function confirmDelete() {
		if (!deleteTarget) return;
		await flowsApi.delete(deleteTarget.id);
		flowList = flowList.filter(f => f.id !== deleteTarget!.id);
		deleteTarget = null;
	}

	function relTime(iso: string | null) {
		if (!iso) return '—';
		const diff = Date.now() - new Date(iso).getTime();
		const m = Math.floor(diff / 60000);
		if (m < 1) return 'az önce';
		if (m < 60) return `${m}dk önce`;
		const h = Math.floor(m / 60);
		if (h < 24) return `${h}sa önce`;
		return `${Math.floor(h / 24)}g önce`;
	}

	function agentName(id: string) {
		return agents.find(a => a.id === id)?.name ?? id;
	}

	// Common cron presets
	const PRESETS = [
		{ label: 'Her gün 09:00', value: '0 9 * * *' },
		{ label: 'Hafta içi 09:00', value: '0 9 * * 1-5' },
		{ label: 'Her Pazartesi 08:00', value: '0 8 * * 1' },
		{ label: 'Her saat başı', value: '0 * * * *' },
		{ label: 'Özel', value: 'custom' },
	];
	let selectedPreset = $state('0 9 * * 1-5');

	function applyPreset(v: string) {
		selectedPreset = v;
		if (v !== 'custom') form.schedule = v;
	}
</script>

<svelte:head><title>Otonom Akışlar • fab.engineering</title></svelte:head>

<div class={['space-y-6 transition-all duration-200', panelOpen ? 'lg:mr-[600px]' : ''].join(' ')}>
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
		<div>
			<h1 class="font-display text-3xl tracking-tight">{t('flow_title')}</h1>
			<p class="text-muted-foreground mt-1">{t('flow_subtitle')}</p>
		</div>
		<Button onclick={openCreate}><Plus class="w-4 h-4" /> {t('flow_new')}</Button>
	</div>

	{#if error}
		<div class="flex items-center gap-2 text-sm text-destructive bg-destructive/10 rounded-xl border border-destructive/30 px-4 py-3">
			<AlertCircle class="w-4 h-4" /> {error}
		</div>
	{/if}

	{#if loading}
		<div class="flex items-center justify-center py-20 text-muted-foreground gap-2">
			<Loader class="w-4 h-4 animate-spin" />
			<span class="text-sm">{t('loading')}</span>
		</div>
	{:else if flowList.length === 0}
		<div class="rounded-xl border bg-card flex flex-col items-center justify-center py-20 gap-3">
			<div class="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
				<Zap class="w-6 h-6 text-muted-foreground" />
			</div>
			<p class="font-medium">{t('flow_empty')}</p>
			<p class="text-sm text-muted-foreground">{t('flow_empty_subtitle')}</p>
			<Button size="sm" onclick={openCreate}><Plus class="w-4 h-4" /> {t('flow_new')}</Button>
		</div>
	{:else}
		<div class="rounded-xl border bg-card overflow-hidden">
			<table class="w-full text-sm">
				<thead>
					<tr class="border-b bg-muted/50 text-left">
						<th class="h-10 px-4 text-xs font-medium text-muted-foreground">{t('flow_col_flow')}</th>
						<th class="h-10 px-4 text-xs font-medium text-muted-foreground hidden md:table-cell">{t('flow_col_agent')}</th>
						<th class="h-10 px-4 text-xs font-medium text-muted-foreground hidden lg:table-cell">{t('flow_col_schedule')}</th>
						<th class="h-10 px-4 text-xs font-medium text-muted-foreground">{t('flow_col_last_run')}</th>
						<th class="h-10 px-4 text-xs font-medium text-muted-foreground">{t('flow_col_status')}</th>
						<th class="h-10 px-4 text-right text-xs font-medium text-muted-foreground">{t('flow_col_action')}</th>
					</tr>
				</thead>
				<tbody class="divide-y">
					{#each flowList as flow (flow.id)}
						<tr class="hover:bg-muted/20 transition-colors group">
							<td class="px-4 py-3">
								<div class="font-medium">{flow.name}</div>
								{#if flow.description}
									<div class="text-xs text-muted-foreground">{flow.description}</div>
								{/if}
							</td>
							<td class="px-4 py-3 hidden md:table-cell text-muted-foreground text-xs">{agentName(flow.personnel_id)}</td>
							<td class="px-4 py-3 hidden lg:table-cell">
								<code class="text-xs bg-muted px-1.5 py-0.5 rounded">{flow.schedule}</code>
							</td>
							<td class="px-4 py-3 text-xs text-muted-foreground">
								{relTime(flow.last_run_at)}
								{#if flow.last_run_status === 'error'}
									<div class="text-destructive text-xs">{t('flow_last_run_error')}</div>
								{/if}
							</td>
							<td class="px-4 py-3">
								<button onclick={() => toggleEnabled(flow)} class="flex items-center gap-1.5 text-xs">
									{#if flow.enabled}
										<ToggleRight class="w-5 h-5 text-emerald-500" />
										<span class="text-emerald-600 font-medium">{t('flow_status_active')}</span>
									{:else}
										<ToggleLeft class="w-5 h-5 text-muted-foreground" />
										<span class="text-muted-foreground">{t('flow_status_inactive')}</span>
									{/if}
								</button>
							</td>
							<td class="px-4 py-3">
								<div class="flex justify-end gap-1">
									<Button variant="ghost" size="icon" onclick={() => runNow(flow.id)} disabled={running === flow.id} title={t('flow_run_now')}>
										{#if running === flow.id}
											<Loader class="w-4 h-4 animate-spin" />
										{:else}
											<Play class="w-4 h-4" />
										{/if}
									</Button>
									<Button variant="ghost" size="icon" onclick={() => openEdit(flow)}><Pencil class="w-4 h-4" /></Button>
									<Button variant="ghost" size="icon" onclick={() => (deleteTarget = flow)} class="text-destructive hover:text-destructive hover:bg-destructive/10"><Trash2 class="w-4 h-4" /></Button>
								</div>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
	{/if}
</div>

<!-- Side Panel -->
{#if panelOpen}
	<div class="fixed inset-0 z-30 bg-black/40 lg:hidden" onclick={() => (panelOpen = false)} aria-hidden="true"></div>
{/if}

<div class={['fixed top-0 right-0 h-full w-full max-w-[592px] bg-background border-l shadow-xl z-40 flex flex-col transition-transform duration-200', panelOpen ? 'translate-x-0' : 'translate-x-full'].join(' ')}>
	<div class="flex items-center justify-between px-6 py-4 border-b">
		<div class="flex items-center gap-2.5">
			<div class="w-8 h-8 rounded-lg bg-violet-100 flex items-center justify-center">
				<Zap class="w-4 h-4 text-violet-600" />
			</div>
			<div>
				<div class="font-semibold text-sm">{editingFlow ? t('flow_edit_title') : t('flow_create_title')}</div>
				<div class="text-xs text-muted-foreground">{editingFlow ? editingFlow.name : t('flow_create_subtitle')}</div>
			</div>
		</div>
		<Button variant="ghost" size="icon" onclick={() => (panelOpen = false)}><X class="w-4 h-4" /></Button>
	</div>

	<div class="flex-1 overflow-y-auto px-6 py-5 space-y-5">
		<div class="space-y-1.5">
			<label class="text-sm font-medium">{t('flow_name_label')}</label>
			<Input bind:value={form.name} placeholder="Günlük Satış Raporu" />
		</div>

		<div class="space-y-1.5">
			<label class="text-sm font-medium">{t('flow_agent_label')}</label>
			<select bind:value={form.personnel_id} class="w-full h-9 px-3 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-1 focus:ring-ring">
				<option value="">{t('flow_agent_placeholder')}</option>
				{#each agents as a (a.id)}
					<option value={a.id}>{a.name} {a.title ? `· ${a.title}` : ''}</option>
				{/each}
			</select>
		</div>

		<div class="space-y-2">
			<label class="text-sm font-medium">{t('flow_schedule_label')}</label>
			<div class="flex flex-wrap gap-1.5">
				{#each PRESETS as p}
					<button
						onclick={() => applyPreset(p.value)}
						class={['px-2.5 py-1 rounded-lg text-xs font-medium transition-colors', selectedPreset === p.value ? 'bg-primary text-primary-foreground' : 'bg-muted text-muted-foreground hover:text-foreground'].join(' ')}
					>
						{p.label}
					</button>
				{/each}
			</div>
			<Input bind:value={form.schedule} placeholder="0 9 * * 1-5" class="font-mono text-sm" />
			<p class="text-xs text-muted-foreground">{t('flow_cron_hint')}</p>
		</div>

		<div class="space-y-1.5">
			<label class="text-sm font-medium">{t('flow_desc_label')}</label>
			<Input bind:value={form.description} placeholder="Bu akış ne işe yarar?" />
		</div>

		<div class="space-y-1.5">
			<label class="text-sm font-medium">{t('flow_prompt_label')}</label>
			<textarea
				bind:value={form.prompt}
				rows={5}
				placeholder={t('flow_prompt_placeholder')}
				class="w-full px-3 py-2 text-sm rounded-md border border-input bg-background focus:outline-none focus:ring-1 focus:ring-ring resize-y"
			></textarea>
		</div>

		<label class="flex items-center gap-2.5 cursor-pointer">
			<input type="checkbox" bind:checked={form.enabled} class="rounded" />
			<span class="text-sm font-medium">{t('flow_enable_label')}</span>
		</label>
	</div>

	<div class="border-t px-6 py-4 flex gap-3 justify-end bg-background">
		<Button variant="outline" onclick={() => (panelOpen = false)}>{t('cancel')}</Button>
		<Button onclick={save} disabled={saving || !form.name || !form.personnel_id || !form.schedule || !form.prompt}>
			{saving ? t('saving') : editingFlow ? t('update') : t('create')}
		</Button>
	</div>
</div>

<!-- Delete confirm -->
{#if deleteTarget}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onclick={() => (deleteTarget = null)} aria-hidden="true">
		<div class="bg-background rounded-xl border p-6 shadow-lg max-w-sm w-full mx-4" onclick={(e) => e.stopPropagation()} role="dialog">
			<h2 class="font-display text-xl">{t('flow_delete_title')}</h2>
			<p class="text-sm text-muted-foreground mt-1"><strong>{deleteTarget.name}</strong> {t('flow_delete_confirm')}</p>
			<div class="flex gap-3 justify-end mt-5">
				<Button variant="outline" onclick={() => (deleteTarget = null)}>{t('cancel')}</Button>
				<Button variant="destructive" onclick={confirmDelete}>{t('delete')}</Button>
			</div>
		</div>
	</div>
{/if}
