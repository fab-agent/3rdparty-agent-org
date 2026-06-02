<script lang="ts">
	import { onMount } from 'svelte';
	import { changeRequests as crApi, type ChangeRequest, type CRStatus } from '$lib/api/change_requests';
	import { personnel as personnelApi, type PersonnelItem } from '$lib/api/personnel';
	import { companyStore } from '$lib/stores/company.svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import {
		GitBranch, CheckCircle2, XCircle, Clock, Loader, AlertCircle,
		ChevronDown, ChevronUp, ExternalLink, ShieldCheck
	} from '@lucide/svelte';
	import { t } from '$lib/i18n/index.svelte';

	const activeCompanyId = $derived(companyStore.active?.id ?? '');
	const isAdmin = $derived(authStore.can(activeCompanyId, 'executive'));
	const isDeptHead = $derived(authStore.can(activeCompanyId, 'dept_head'));

	let crs: ChangeRequest[] = $state([]);
	let personnelMap: Record<string, PersonnelItem> = $state({});
	let loading = $state(true);
	let error: string | null = $state(null);
	let filterStatus: string = $state('');
	let expandedId: string | null = $state(null);
	let actionNote = $state('');
	let actioning: string | null = $state(null);

	async function load() {
		if (!activeCompanyId) return;
		loading = true;
		error = null;
		try {
			const [list, pList] = await Promise.all([
				crApi.list({ company_id: activeCompanyId, status: filterStatus || undefined }),
				personnelApi.list({ company_id: activeCompanyId })
			]);
			crs = list;
			personnelMap = Object.fromEntries(pList.map((p) => [p.id, p]));
		} catch (e) {
			error = (e as Error).message;
		} finally {
			loading = false;
		}
	}

	onMount(load);
	$effect(() => { if (companyStore.active) load(); });
	$effect(() => { load(); });  // re-runs when filterStatus changes

	function statusLabel(s: CRStatus): string {
		return ({
			submitted: t('cr_filter_pending'),
			dept_head_approved: t('cr_filter_dept_approved'),
			admin_approved: 'Admin Onaylandı',
			committed: t('cr_filter_committed'),
			rejected: t('cr_filter_rejected'),
		} as Record<string, string>)[s] ?? s;
	}

	function statusVariant(s: CRStatus): 'default' | 'secondary' | 'destructive' | 'outline' {
		if (s === 'committed') return 'default';
		if (s === 'rejected') return 'destructive';
		if (s === 'submitted') return 'outline';
		return 'secondary';
	}

	function typeLabel(t: string): string {
		return ({ agent_config: 'Ajan Yapılandırması', skill: 'Skill', policy: 'Politika' })[t] ?? t;
	}

	function relTime(iso: string): string {
		const diff = Date.now() - new Date(iso).getTime();
		const m = Math.floor(diff / 60000);
		if (m < 1) return 'az önce';
		if (m < 60) return `${m}dk önce`;
		const h = Math.floor(m / 60);
		if (h < 24) return `${h}sa önce`;
		return `${Math.floor(h / 24)}g önce`;
	}

	async function deptApprove(cr: ChangeRequest) {
		actioning = cr.id + '-dept-approve';
		try {
			const updated = await crApi.deptApprove(cr.id, actionNote || undefined);
			crs = crs.map((c) => c.id === cr.id ? updated : c);
			actionNote = '';
		} catch (e) { alert((e as Error).message); }
		finally { actioning = null; }
	}

	async function deptReject(cr: ChangeRequest) {
		actioning = cr.id + '-dept-reject';
		try {
			const updated = await crApi.deptReject(cr.id, actionNote || undefined);
			crs = crs.map((c) => c.id === cr.id ? updated : c);
			actionNote = '';
		} catch (e) { alert((e as Error).message); }
		finally { actioning = null; }
	}

	async function adminApprove(cr: ChangeRequest) {
		actioning = cr.id + '-admin-approve';
		try {
			const updated = await crApi.adminApprove(cr.id, activeCompanyId, actionNote || undefined);
			crs = crs.map((c) => c.id === cr.id ? updated : c);
			actionNote = '';
		} catch (e) { alert((e as Error).message); }
		finally { actioning = null; }
	}

	async function adminReject(cr: ChangeRequest) {
		actioning = cr.id + '-admin-reject';
		try {
			const updated = await crApi.adminReject(cr.id, actionNote || undefined);
			crs = crs.map((c) => c.id === cr.id ? updated : c);
			actionNote = '';
		} catch (e) { alert((e as Error).message); }
		finally { actioning = null; }
	}

	const pendingCount = $derived(crs.filter(c => c.status === 'submitted' || c.status === 'dept_head_approved').length);
</script>

<svelte:head>
	<title>Değişiklik Talepleri • fab.engineering</title>
</svelte:head>

<div class="space-y-6 max-w-4xl">
	<!-- Header -->
	<div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
		<div>
			<h1 class="font-display text-3xl tracking-tight">{t('cr_title')}</h1>
			<p class="text-muted-foreground mt-1">{t('cr_subtitle')}</p>
		</div>
		{#if pendingCount > 0}
			<Badge variant="secondary" class="text-sm px-3 py-1.5">
				{pendingCount} {t('cr_pending_badge')}
			</Badge>
		{/if}
	</div>

	<!-- Filter -->
	<div class="flex flex-wrap gap-2">
		{#each [
			{ value: '', label: t('cr_filter_all') },
			{ value: 'submitted', label: t('cr_filter_pending') },
			{ value: 'dept_head_approved', label: t('cr_filter_dept_approved') },
			{ value: 'committed', label: t('cr_filter_committed') },
			{ value: 'rejected', label: t('cr_filter_rejected') },
		] as f}
			<button
				onclick={() => { filterStatus = f.value; }}
				class={[
					'px-3 py-1.5 rounded-lg text-sm font-medium transition-colors',
					filterStatus === f.value
						? 'bg-primary text-primary-foreground'
						: 'bg-muted/60 text-muted-foreground hover:text-foreground'
				].join(' ')}
			>
				{f.label}
			</button>
		{/each}
	</div>

	<!-- Error -->
	{#if error}
		<div class="flex items-center gap-2 text-sm text-destructive rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3">
			<AlertCircle class="w-4 h-4 flex-shrink-0" />
			{error}
		</div>
	{/if}

	<!-- List -->
	{#if loading}
		<div class="flex items-center justify-center py-20 text-muted-foreground gap-2">
			<Loader class="w-4 h-4 animate-spin" />
			<span class="text-sm">{t('loading')}</span>
		</div>
	{:else if crs.length === 0}
		<div class="rounded-xl border bg-card flex flex-col items-center justify-center py-20 gap-3">
			<div class="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
				<GitBranch class="w-6 h-6 text-muted-foreground" />
			</div>
			<p class="font-medium">{t('cr_empty')}</p>
			<p class="text-sm text-muted-foreground">{t('cr_empty_subtitle')}</p>
		</div>
	{:else}
		<div class="space-y-3">
			{#each crs as cr (cr.id)}
				{@const agent = personnelMap[cr.personnel_id]}
				{@const expanded = expandedId === cr.id}
				<div class="rounded-xl border bg-card overflow-hidden">
					<!-- Header row -->
					<button
						class="w-full flex items-start gap-4 px-5 py-4 text-left hover:bg-muted/20 transition-colors"
						onclick={() => expandedId = expanded ? null : cr.id}
					>
						<!-- Status icon -->
						<div class="mt-0.5 flex-shrink-0">
							{#if cr.status === 'committed'}
								<CheckCircle2 class="w-5 h-5 text-emerald-500" />
							{:else if cr.status === 'rejected'}
								<XCircle class="w-5 h-5 text-destructive" />
							{:else}
								<Clock class="w-5 h-5 text-amber-500" />
							{/if}
						</div>

						<div class="flex-1 min-w-0">
							<div class="flex items-center gap-2 flex-wrap">
								<span class="font-medium">{cr.title}</span>
								<Badge variant={statusVariant(cr.status)} class="text-xs">{statusLabel(cr.status)}</Badge>
								<span class="text-xs text-muted-foreground px-2 py-0.5 bg-muted rounded-full">{typeLabel(cr.change_type)}</span>
							</div>
							<div class="text-xs text-muted-foreground mt-1 flex items-center gap-3">
								<span>{t('cr_agent_label')}: {agent?.name ?? cr.personnel_id}</span>
								<span>·</span>
								<span>{relTime(cr.created_at)}</span>
								{#if cr.commit_sha}
									<span>·</span>
									<a
										href={cr.commit_url ?? '#'}
										target="_blank"
										rel="noopener"
										class="flex items-center gap-1 text-primary hover:underline"
										onclick={(e) => e.stopPropagation()}
									>
										<ExternalLink class="w-3 h-3" />
										{cr.commit_sha.slice(0, 7)}
									</a>
								{/if}
							</div>
						</div>

						<div class="flex-shrink-0 text-muted-foreground mt-1">
							{#if expanded}
								<ChevronUp class="w-4 h-4" />
							{:else}
								<ChevronDown class="w-4 h-4" />
							{/if}
						</div>
					</button>

					<!-- Expanded detail -->
					{#if expanded}
						<div class="border-t px-5 py-4 space-y-4 bg-muted/10">
							<!-- Approval timeline -->
							<div class="space-y-2">
								<h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide">{t('cr_approval_flow')}</h4>
								<div class="space-y-1.5 text-sm">
									<div class="flex items-center gap-2">
										{#if cr.dept_head_approved_at}
											<CheckCircle2 class="w-4 h-4 text-emerald-500" />
											<span>{t('cr_dept_approval')} — {relTime(cr.dept_head_approved_at)}</span>
											{#if cr.dept_head_note}<span class="text-muted-foreground">· "{cr.dept_head_note}"</span>{/if}
										{:else if cr.dept_head_rejected_at}
											<XCircle class="w-4 h-4 text-destructive" />
											<span class="text-destructive">{t('cr_dept_rejection')}</span>
											{#if cr.dept_head_note}<span class="text-muted-foreground">· "{cr.dept_head_note}"</span>{/if}
										{:else}
											<Clock class="w-4 h-4 text-muted-foreground/50" />
											<span class="text-muted-foreground">{t('cr_dept_waiting')}</span>
										{/if}
									</div>
									<div class="flex items-center gap-2">
										{#if cr.admin_approved_at}
											<CheckCircle2 class="w-4 h-4 text-emerald-500" />
											<span>{t('cr_admin_approval')} — {relTime(cr.admin_approved_at)}</span>
											{#if cr.admin_note}<span class="text-muted-foreground">· "{cr.admin_note}"</span>{/if}
										{:else if cr.admin_rejected_at}
											<XCircle class="w-4 h-4 text-destructive" />
											<span class="text-destructive">{t('cr_admin_rejection')}</span>
											{#if cr.admin_note}<span class="text-muted-foreground">· "{cr.admin_note}"</span>{/if}
										{:else}
											<ShieldCheck class="w-4 h-4 text-muted-foreground/50" />
											<span class="text-muted-foreground">{t('cr_admin_waiting')}</span>
										{/if}
									</div>
								</div>
							</div>

							<!-- Proposed changes (JSON diff) -->
							<div>
								<h4 class="text-xs font-semibold text-muted-foreground uppercase tracking-wide mb-2">{t('cr_proposed_changes')}</h4>
								<pre class="text-xs bg-muted rounded-lg p-3 overflow-auto max-h-48">{JSON.stringify(cr.proposed, null, 2)}</pre>
							</div>

							<!-- Action buttons -->
							{#if cr.status === 'submitted' && isDeptHead}
								<div class="space-y-2 pt-1">
									<textarea
										bind:value={actionNote}
										placeholder={t('cr_note_placeholder')}
										class="w-full text-sm rounded-lg border border-input bg-background px-3 py-2 resize-none h-16 focus:outline-none focus:ring-1 focus:ring-ring"
									></textarea>
									<div class="flex gap-2">
										<Button
											size="sm"
											onclick={() => deptApprove(cr)}
											disabled={!!actioning}
										>
											{actioning === cr.id + '-dept-approve' ? t('approving') : t('cr_dept_approve_btn')}
										</Button>
										<Button
											size="sm"
											variant="destructive"
											onclick={() => deptReject(cr)}
											disabled={!!actioning}
										>
											{t('cr_reject_btn')}
										</Button>
									</div>
								</div>
							{/if}

							{#if cr.status === 'dept_head_approved' && isAdmin}
								<div class="space-y-2 pt-1">
									<textarea
										bind:value={actionNote}
										placeholder={t('cr_note_placeholder')}
										class="w-full text-sm rounded-lg border border-input bg-background px-3 py-2 resize-none h-16 focus:outline-none focus:ring-1 focus:ring-ring"
									></textarea>
									<div class="flex gap-2">
										<Button
											size="sm"
											onclick={() => adminApprove(cr)}
											disabled={!!actioning}
										>
											{actioning === cr.id + '-admin-approve' ? t('approving') : t('cr_admin_approve_btn')}
										</Button>
										<Button
											size="sm"
											variant="destructive"
											onclick={() => adminReject(cr)}
											disabled={!!actioning}
										>
											{t('cr_reject_btn')}
										</Button>
									</div>
								</div>
							{/if}
						</div>
					{/if}
				</div>
			{/each}
		</div>
	{/if}
</div>
