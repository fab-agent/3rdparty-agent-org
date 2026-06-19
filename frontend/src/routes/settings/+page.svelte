<script lang="ts">
	import { onMount } from 'svelte';
	import { providers as providerApi, type ProviderStatus } from '$lib/api/providers.js';
	import { git as gitApi, type GitConfig, type SyncLog } from '$lib/api/git.js';
	import { companyStore } from '$lib/stores/company.svelte';
	import Button from '$lib/components/ui/button.svelte';
	import {
		Settings,
		Cpu,
		GitBranch,
		CheckCircle2,
		XCircle,
		Circle,
		Eye,
		EyeOff,
		RefreshCw,
		Trash2,
		Link,
		Unlink,
		ArrowDown,
		ArrowUp,
		AlertTriangle,
		Loader2,
		Clock,
		User
	} from '@lucide/svelte';
	import { t } from '$lib/i18n/index.svelte';

	// ── Tabs ─────────────────────────────────────────────────────────────────
	let tab = $state<'providers' | 'git' | 'audit'>('providers');

	// ── Provider state ────────────────────────────────────────────────────────
	type ProviderCard = ProviderStatus & {
		keyInput: string;
		showKey: boolean;
		editMode: boolean; // show key input even when has_key
		saving: boolean;
		testing: boolean;
		deleting: boolean;
		error: string;
	};

	let providerCards = $state<ProviderCard[]>([]);
	let providerLoading = $state(true);

	async function loadProviders() {
		providerLoading = true;
		try {
			const list = await providerApi.status();
			providerCards = list.map((p) => ({
				...p,
				keyInput: '',
				showKey: false,
				editMode: !p.has_key,
				saving: false,
				testing: false,
				deleting: false,
				error: ''
			}));
		} finally {
			providerLoading = false;
		}
	}

	async function saveKey(card: ProviderCard) {
		if (!card.keyInput.trim()) return;
		card.saving = true;
		card.error = '';
		try {
			const updated = await providerApi.setKey(card.provider, card.keyInput.trim());
			Object.assign(card, updated, {
				keyInput: '',
				showKey: false,
				editMode: updated.status !== 'active',
				saving: false,
				error: updated.status === 'invalid' ? t('settings_provider_invalid_err') : ''
			});
		} catch {
			card.saving = false;
			card.error = t('settings_provider_save_err');
		}
	}

	async function testKey(card: ProviderCard) {
		card.testing = true;
		card.error = '';
		try {
			const updated = await providerApi.test(card.provider);
			Object.assign(card, updated, {
				testing: false,
				editMode: updated.status !== 'active',
				error: updated.status === 'invalid' ? t('settings_provider_invalid_err') : ''
			});
		} catch {
			card.testing = false;
			card.error = t('settings_provider_test_err');
		}
	}

	async function deleteKey(card: ProviderCard) {
		card.deleting = true;
		try {
			await providerApi.deleteKey(card.provider);
			card.status = 'unconfigured';
			card.has_key = false;
			card.models = [];
			card.last_tested = null;
			card.editMode = true;
			card.keyInput = '';
			card.error = '';
		} finally {
			card.deleting = false;
		}
	}

	// ── Git state ─────────────────────────────────────────────────────────────
	let gitConfig = $state<GitConfig | null>(null);
	let gitLogs = $state<SyncLog[]>([]);
	let gitLoading = $state(true);
	let gitSyncing = $state<'pull' | 'push' | null>(null);
	let gitConnecting = $state(false);
	let gitDisconnecting = $state(false);
	let gitError = $state('');

	// connect form
	let gitForm = $state({
		provider: 'github',
		repo_url: '',
		branch: 'main',
		token: '',
		showToken: false,
		sync_interval: 30,
		auto_pr: false
	});

	const activeCompanyId = $derived(companyStore.active?.id);

	async function loadGit() {
		gitLoading = true;
		try {
			const [cfg, logs] = await Promise.all([gitApi.config(activeCompanyId), gitApi.logs(10)]);
			gitConfig = cfg;
			gitLogs = logs;
		} finally {
			gitLoading = false;
		}
	}

	async function connectGit() {
		gitConnecting = true;
		gitError = '';
		try {
			gitConfig = await gitApi.connect({
				provider: gitForm.provider,
				repo_url: gitForm.repo_url.trim(),
				branch: gitForm.branch.trim() || 'main',
				token: gitForm.token.trim(),
				sync_interval: gitForm.sync_interval,
				auto_pr: gitForm.auto_pr
			}, activeCompanyId);
			gitForm = { provider: 'github', repo_url: '', branch: 'main', token: '', showToken: false, sync_interval: 30, auto_pr: false };
		} catch {
			gitError = t('settings_git_connect_err');
		} finally {
			gitConnecting = false;
		}
	}

	async function disconnectGit() {
		gitDisconnecting = true;
		try {
			await gitApi.disconnect(activeCompanyId);
			gitConfig = null;
			gitLogs = [];
		} finally {
			gitDisconnecting = false;
		}
	}

	async function triggerSync(direction: 'pull' | 'push') {
		gitSyncing = direction;
		gitError = '';
		try {
			const log = direction === 'pull'
				? await gitApi.pull(activeCompanyId)
				: await gitApi.push(undefined, activeCompanyId);
			gitLogs = [log, ...gitLogs].slice(0, 10);
			gitConfig = await gitApi.config(activeCompanyId);
		} catch {
			gitError = `${direction === 'pull' ? 'Pull' : 'Push'} ${t('settings_git_sync_err')}`;
		} finally {
			gitSyncing = null;
		}
	}

	// ── Audit log state ───────────────────────────────────────────────────────
	let auditLogs = $state<any[]>([]);
	let auditLoading = $state(false);
	let auditEntityFilter = $state('');

	async function loadAuditLogs() {
		auditLoading = true;
		try {
			const company = companyStore.active;
			const params = new URLSearchParams({ limit: '100' });
			if (company?.id) params.set('company_id', company.id);
			if (auditEntityFilter) params.set('entity_type', auditEntityFilter);
			const resp = await fetch(`${import.meta.env.VITE_API_URL}/audit?${params}`);
			auditLogs = await resp.json();
		} finally {
			auditLoading = false;
		}
	}

	function switchTab(newTab: 'providers' | 'git' | 'audit') {
		tab = newTab;
		if (newTab === 'audit') loadAuditLogs();
	}

	// ── Helpers ───────────────────────────────────────────────────────────────
	function relativeTime(iso: string | null): string {
		if (!iso) return '—';
		const diff = Date.now() - new Date(iso).getTime();
		const min = Math.floor(diff / 60000);
		if (min < 1) return 'az önce';
		if (min < 60) return `${min} dakika önce`;
		const h = Math.floor(min / 60);
		if (h < 24) return `${h} saat önce`;
		return `${Math.floor(h / 24)} gün önce`;
	}

	function shortSha(sha: string | null) {
		return sha ? sha.slice(0, 7) : '—';
	}

	onMount(() => {
		loadProviders();
		loadGit();
	});
</script>

<svelte:head><title>{t('settings_title')} • fab.engineering</title></svelte:head>

<div class="max-w-3xl mx-auto">
	<!-- Header -->
	<div class="flex items-center gap-x-3 mb-8">
		<div class="w-10 h-10 rounded-xl bg-muted flex items-center justify-center">
			<Settings class="w-5 h-5 text-muted-foreground" />
		</div>
		<div>
			<h1 class="text-2xl font-bold tracking-tight">{t('settings_title')}</h1>
			<p class="text-sm text-muted-foreground">{t('settings_subtitle')}</p>
		</div>
	</div>

	<!-- Tabs -->
	<div class="flex gap-x-1 mb-8 border-b">
		<button
			class={[
				'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-x-2',
				tab === 'providers'
					? 'border-primary text-foreground'
					: 'border-transparent text-muted-foreground hover:text-foreground'
			].join(' ')}
			onclick={() => switchTab('providers')}
		>
			<Cpu class="w-4 h-4" />
			{t('settings_providers')}
		</button>
		<button
			class={[
				'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-x-2',
				tab === 'git'
					? 'border-primary text-foreground'
					: 'border-transparent text-muted-foreground hover:text-foreground'
			].join(' ')}
			onclick={() => switchTab('git')}
		>
			<GitBranch class="w-4 h-4" />
			{t('settings_git')}
		</button>
		<button
			class={[
				'px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors flex items-center gap-x-2',
				tab === 'audit'
					? 'border-primary text-foreground'
					: 'border-transparent text-muted-foreground hover:text-foreground'
			].join(' ')}
			onclick={() => switchTab('audit')}
		>
			<Clock class="w-4 h-4" />
			Audit Log
		</button>
	</div>

	<!-- ── PROVIDERS TAB ─────────────────────────────────────────────────── -->
	{#if tab === 'providers'}
		<div class="mb-4">
			<p class="text-sm text-muted-foreground">
				{t('settings_providers_desc')}
			</p>
		</div>

		{#if providerLoading}
			<div class="flex items-center gap-x-2 text-muted-foreground py-12 justify-center">
				<Loader2 class="w-4 h-4 animate-spin" />
				<span class="text-sm">{t('loading')}</span>
			</div>
		{:else}
			<div class="space-y-3">
				{#each providerCards as card (card.provider)}
					{@const isActive = card.status === 'active'}
					{@const isInvalid = card.status === 'invalid'}

					<div
						class={[
							'rounded-2xl border bg-card transition-all',
							isActive ? 'border-emerald-500/30' : isInvalid ? 'border-destructive/30' : 'border-border'
						].join(' ')}
					>
						<!-- Card header -->
						<div class="flex items-center justify-between px-5 py-4">
							<div class="flex items-center gap-x-3">
								<!-- Status dot -->
								{#if isActive}
									<CheckCircle2 class="w-5 h-5 text-emerald-500 flex-shrink-0" />
								{:else if isInvalid}
									<AlertTriangle class="w-5 h-5 text-destructive flex-shrink-0" />
								{:else}
									<Circle class="w-5 h-5 text-muted-foreground/40 flex-shrink-0" />
								{/if}
								<div>
									<div class="font-semibold text-sm">{card.display_name}</div>
									{#if isActive}
										<div class="text-xs text-muted-foreground mt-0.5">
											{t('settings_provider_last_tested')} {relativeTime(card.last_tested)}
										</div>
									{:else if isInvalid}
										<div class="text-xs text-destructive mt-0.5">{t('settings_provider_invalid')}</div>
									{:else}
										<div class="text-xs text-muted-foreground mt-0.5">{t('settings_provider_unconfigured')}</div>
									{/if}
								</div>
							</div>

							<!-- Action buttons -->
							<div class="flex items-center gap-x-2">
								{#if isActive}
									<Button
										variant="ghost"
										size="sm"
										class="h-8 px-3 text-xs gap-x-1.5"
										onclick={() => (card.editMode = !card.editMode)}
									>
										{t('settings_provider_update_key')}
									</Button>
									<Button
										variant="ghost"
										size="sm"
										class="h-8 px-3 text-xs gap-x-1.5"
										disabled={card.testing}
										onclick={() => testKey(card)}
									>
										{#if card.testing}
											<Loader2 class="w-3.5 h-3.5 animate-spin" />
										{:else}
											<RefreshCw class="w-3.5 h-3.5" />
										{/if}
										{t('settings_provider_test')}
									</Button>
									<Button
										variant="ghost"
										size="sm"
										class="h-8 px-3 text-xs text-destructive hover:text-destructive gap-x-1.5"
										disabled={card.deleting}
										onclick={() => deleteKey(card)}
									>
										{#if card.deleting}
											<Loader2 class="w-3.5 h-3.5 animate-spin" />
										{:else}
											<Trash2 class="w-3.5 h-3.5" />
										{/if}
										{t('settings_provider_delete')}
									</Button>
								{:else if isInvalid}
									<Button
										variant="ghost"
										size="sm"
										class="h-8 px-3 text-xs gap-x-1.5"
										disabled={card.deleting}
										onclick={() => deleteKey(card)}
									>
										{#if card.deleting}
											<Loader2 class="w-3.5 h-3.5 animate-spin" />
										{:else}
											<Trash2 class="w-3.5 h-3.5" />
										{/if}
										{t('settings_provider_delete')}
									</Button>
								{/if}
							</div>
						</div>

						<!-- Active: model chips -->
						{#if isActive && card.models.length > 0}
							<div class="px-5 pb-3 flex flex-wrap gap-1.5">
								{#each card.models as model}
									<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20">
										{model.name}
									</span>
								{/each}
							</div>
						{/if}

						<!-- Key input (unconfigured or editMode) -->
						{#if card.editMode || isInvalid}
							<div class="px-5 pb-4 pt-1 border-t border-border/50">
								{#if card.error}
									<div class="mb-3 text-xs text-destructive flex items-center gap-x-1.5">
										<XCircle class="w-3.5 h-3.5 flex-shrink-0" />
										{card.error}
									</div>
								{/if}
								<div class="flex gap-x-2">
									<div class="relative flex-1">
										<input
											type={card.showKey ? 'text' : 'password'}
											bind:value={card.keyInput}
											placeholder={t('settings_provider_key_ph')}
											class="w-full h-9 px-3 pr-10 text-sm rounded-lg border border-input bg-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring font-mono"
											onkeydown={(e) => e.key === 'Enter' && saveKey(card)}
										/>
										<button
											class="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
											onclick={() => (card.showKey = !card.showKey)}
											type="button"
											tabindex="-1"
										>
											{#if card.showKey}
												<EyeOff class="w-4 h-4" />
											{:else}
												<Eye class="w-4 h-4" />
											{/if}
										</button>
									</div>
									<Button
										variant="default"
										size="sm"
										class="h-9 px-4 text-xs"
										disabled={card.saving || !card.keyInput.trim()}
										onclick={() => saveKey(card)}
									>
										{#if card.saving}
											<Loader2 class="w-3.5 h-3.5 animate-spin mr-1.5" />
											{t('settings_provider_testing')}
										{:else}
											{t('settings_provider_save_test')}
										{/if}
									</Button>
								</div>
							</div>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	{/if}

	<!-- ── GIT TAB ────────────────────────────────────────────────────────── -->
	{#if tab === 'git'}
		{#if gitLoading}
			<div class="flex items-center gap-x-2 text-muted-foreground py-12 justify-center">
				<Loader2 class="w-4 h-4 animate-spin" />
				<span class="text-sm">{t('loading')}</span>
			</div>
		{:else if gitConfig}
			<!-- Connected state -->
			<div class="rounded-2xl border bg-card">
				<div class="flex items-center justify-between px-5 py-4">
					<div class="flex items-center gap-x-3">
						<CheckCircle2 class="w-5 h-5 text-emerald-500" />
						<div>
							<div class="font-semibold text-sm capitalize">{gitConfig.provider}</div>
							<div class="text-xs text-muted-foreground font-mono mt-0.5 max-w-xs truncate">
								{gitConfig.repo_url}
							</div>
						</div>
					</div>
					<div class="flex items-center gap-x-2">
						<span class="text-xs text-muted-foreground px-2 py-1 bg-muted rounded-lg font-mono">
							{gitConfig.branch}
						</span>
						<Button
							variant="ghost"
							size="sm"
							class="h-8 px-3 text-xs text-destructive hover:text-destructive gap-x-1.5"
							disabled={gitDisconnecting}
							onclick={disconnectGit}
						>
							{#if gitDisconnecting}
								<Loader2 class="w-3.5 h-3.5 animate-spin" />
							{:else}
								<Unlink class="w-3.5 h-3.5" />
							{/if}
							{t('settings_git_disconnect')}
						</Button>
					</div>
				</div>

				<!-- Stats row -->
				<div class="px-5 pb-4 grid grid-cols-3 gap-4 border-t border-border/50 pt-4">
					<div>
						<div class="text-xs text-muted-foreground">{t('settings_git_last_sync')}</div>
						<div class="text-sm font-medium mt-0.5">{relativeTime(gitConfig.last_synced)}</div>
					</div>
					<div>
						<div class="text-xs text-muted-foreground">{t('settings_git_last_commit')}</div>
						<div class="text-sm font-mono font-medium mt-0.5">{shortSha(gitConfig.last_commit_sha)}</div>
					</div>
					<div>
						<div class="text-xs text-muted-foreground">{t('settings_git_status')}</div>
						<div class={['text-sm font-medium mt-0.5', gitConfig.status === 'connected' ? 'text-emerald-600' : 'text-destructive'].join(' ')}>
							{gitConfig.status === 'connected' ? t('settings_git_connected') : gitConfig.status}
						</div>
					</div>
				</div>

				<!-- Sync actions -->
				<div class="px-5 pb-4 flex items-center gap-x-2 border-t border-border/50 pt-4">
					{#if gitError}
						<p class="text-xs text-destructive flex-1 flex items-center gap-x-1.5">
							<XCircle class="w-3.5 h-3.5" /> {gitError}
						</p>
					{/if}
					<div class="flex gap-x-2 ml-auto">
						<Button
							variant="outline"
							size="sm"
							class="h-8 px-3 text-xs gap-x-1.5"
							disabled={gitSyncing !== null}
							onclick={() => triggerSync('pull')}
						>
							{#if gitSyncing === 'pull'}
								<Loader2 class="w-3.5 h-3.5 animate-spin" />
							{:else}
								<ArrowDown class="w-3.5 h-3.5" />
							{/if}
							{t('settings_git_pull')}
						</Button>
						<Button
							variant="outline"
							size="sm"
							class="h-8 px-3 text-xs gap-x-1.5"
							disabled={gitSyncing !== null}
							onclick={() => triggerSync('push')}
						>
							{#if gitSyncing === 'push'}
								<Loader2 class="w-3.5 h-3.5 animate-spin" />
							{:else}
								<ArrowUp class="w-3.5 h-3.5" />
							{/if}
							{t('settings_git_push')}
						</Button>
					</div>
				</div>
			</div>

			<!-- Sync logs -->
			{#if gitLogs.length > 0}
				<div class="mt-6">
					<h3 class="text-sm font-semibold mb-3 text-muted-foreground tracking-wide uppercase text-xs">
						{t('settings_git_sync_history')}
					</h3>
					<div class="rounded-xl border overflow-hidden">
						<table class="w-full text-sm">
							<thead>
								<tr class="border-b bg-muted/40">
									<th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">{t('settings_git_col_dir')}</th>
									<th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">{t('settings_git_col_status')}</th>
									<th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">{t('settings_git_col_files')}</th>
									<th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">{t('settings_git_col_commit')}</th>
									<th class="text-left px-4 py-2.5 text-xs font-medium text-muted-foreground">{t('settings_git_col_message')}</th>
									<th class="text-right px-4 py-2.5 text-xs font-medium text-muted-foreground">{t('settings_git_col_time')}</th>
								</tr>
							</thead>
							<tbody>
								{#each gitLogs as log}
									<tr class="border-b last:border-0 hover:bg-muted/30 transition-colors">
										<td class="px-4 py-2.5">
											<span class="flex items-center gap-x-1.5 text-xs font-medium">
												{#if log.direction === 'pull'}
													<ArrowDown class="w-3.5 h-3.5 text-blue-500" />
													Pull
												{:else}
													<ArrowUp class="w-3.5 h-3.5 text-purple-500" />
													Push
												{/if}
											</span>
										</td>
										<td class="px-4 py-2.5">
											<span class={[
												'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
												log.status === 'success'    ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400' :
												log.status === 'error'      ? 'bg-destructive/10 text-destructive' :
												                              'bg-muted text-muted-foreground'
											].join(' ')}>
												{log.status === 'success' ? t('settings_git_success') : log.status === 'error' ? t('settings_git_error') : t('settings_git_no_change')}
											</span>
										</td>
										<td class="px-4 py-2.5 text-xs text-muted-foreground">{log.files_changed}</td>
										<td class="px-4 py-2.5 font-mono text-xs text-muted-foreground">{shortSha(log.commit_sha)}</td>
										<td class="px-4 py-2.5 text-xs text-muted-foreground max-w-xs truncate">{log.message ?? '—'}</td>
										<td class="px-4 py-2.5 text-xs text-muted-foreground text-right">{relativeTime(log.created_at)}</td>
									</tr>
								{/each}
							</tbody>
						</table>
					</div>
				</div>
			{/if}
		{:else}
			<!-- Connect form -->
			<div class="mb-4">
				<p class="text-sm text-muted-foreground">
					{t('settings_git_desc')}
				</p>
			</div>

			<div class="rounded-2xl border bg-card p-5 space-y-4">
				<h3 class="font-semibold text-sm flex items-center gap-x-2">
					<Link class="w-4 h-4" />
					{t('settings_git_new_conn')}
				</h3>

				{#if gitError}
					<div class="text-xs text-destructive flex items-center gap-x-1.5 bg-destructive/10 px-3 py-2 rounded-lg">
						<XCircle class="w-3.5 h-3.5" /> {gitError}
					</div>
				{/if}

				<div class="grid grid-cols-2 gap-3">
					<div>
						<label class="block text-xs font-medium text-muted-foreground mb-1.5">{t('settings_git_provider_label')}</label>
						<select
							bind:value={gitForm.provider}
							class="w-full h-9 px-3 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring"
						>
							<option value="github">GitHub</option>
							<option value="gitlab">GitLab</option>
							<option value="gitea">Gitea</option>
						</select>
					</div>
					<div>
						<label class="block text-xs font-medium text-muted-foreground mb-1.5">{t('settings_git_branch_label')}</label>
						<input
							type="text"
							bind:value={gitForm.branch}
							placeholder="main"
							class="w-full h-9 px-3 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-ring font-mono"
						/>
					</div>
				</div>

				<div>
					<label class="block text-xs font-medium text-muted-foreground mb-1.5">{t('settings_git_repo_label')}</label>
					<input
						type="url"
						bind:value={gitForm.repo_url}
						placeholder="https://github.com/organization/ai-capabilities"
						class="w-full h-9 px-3 text-sm rounded-lg border border-input bg-background font-mono focus:outline-none focus:ring-2 focus:ring-ring"
					/>
				</div>

				<div>
					<label class="block text-xs font-medium text-muted-foreground mb-1.5">
						{t('settings_git_token_label')}
						<span class="font-normal text-muted-foreground/70">
							({gitForm.provider === 'github' ? 'ghp_...' : 'glpat-...'})
						</span>
					</label>
					<div class="relative">
						<input
							type={gitForm.showToken ? 'text' : 'password'}
							bind:value={gitForm.token}
							placeholder={t('settings_git_token_ph')}
							class="w-full h-9 px-3 pr-10 text-sm rounded-lg border border-input bg-background font-mono focus:outline-none focus:ring-2 focus:ring-ring"
						/>
						<button
							class="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
							onclick={() => (gitForm.showToken = !gitForm.showToken)}
							type="button"
						>
							{#if gitForm.showToken}
								<EyeOff class="w-4 h-4" />
							{:else}
								<Eye class="w-4 h-4" />
							{/if}
						</button>
					</div>
				</div>

				<div class="flex items-center justify-between pt-1">
					<label class="flex items-center gap-x-2 text-sm cursor-pointer select-none">
						<input type="checkbox" bind:checked={gitForm.auto_pr} class="rounded" />
						<span>{t('settings_git_auto_pr')}</span>
					</label>
					<Button
						variant="default"
						size="sm"
						class="h-9 px-5"
						disabled={gitConnecting || !gitForm.repo_url.trim() || !gitForm.token.trim()}
						onclick={connectGit}
					>
						{#if gitConnecting}
							<Loader2 class="w-3.5 h-3.5 animate-spin mr-1.5" />
							{t('settings_git_connecting')}
						{:else}
							<Link class="w-3.5 h-3.5 mr-1.5" />
							{t('settings_git_connect')}
						{/if}
					</Button>
				</div>
			</div>
		{/if}
	{/if}

	<!-- ── AUDIT LOG TAB ─────────────────────────────────────────────────── -->
	{#if tab === 'audit'}
	<div class="space-y-4">
		<div class="flex items-center gap-3">
			<select
				bind:value={auditEntityFilter}
				onchange={loadAuditLogs}
				class="h-9 rounded-md border border-border bg-background px-3 py-1 text-sm"
			>
				<option value="">All types</option>
				<option value="department">Departments</option>
				<option value="personnel">Personnel</option>
				<option value="agent_config">Agent Config</option>
				<option value="skill">Skills</option>
				<option value="flow">Flows</option>
				<option value="change_request">Change Requests</option>
				<option value="provider_key">Provider Keys</option>
			</select>
			<button onclick={loadAuditLogs} class="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-border text-sm hover:bg-muted">
				<RefreshCw class="h-3.5 w-3.5" />
				Refresh
			</button>
		</div>

		{#if auditLoading}
			<div class="flex justify-center py-8">
				<Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
			</div>
		{:else if auditLogs.length === 0}
			<div class="text-center py-8 text-muted-foreground text-sm">No audit logs found.</div>
		{:else}
			<div class="rounded-md border border-border overflow-hidden">
				<table class="w-full text-sm">
					<thead class="bg-muted/50">
						<tr>
							<th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Time</th>
							<th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Action</th>
							<th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Type</th>
							<th class="text-left px-4 py-2.5 font-medium text-muted-foreground">Entity</th>
						</tr>
					</thead>
					<tbody>
						{#each auditLogs as log}
							<tr class="border-t border-border hover:bg-muted/30">
								<td class="px-4 py-2.5 text-muted-foreground whitespace-nowrap">
									{new Date(log.created_at).toLocaleString()}
								</td>
								<td class="px-4 py-2.5">
									<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium
										{log.action === 'create' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
										 log.action === 'delete' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
										 log.action === 'approve' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400' :
										 log.action === 'reject' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
										 'bg-muted text-muted-foreground'}">
										{log.action}
									</span>
								</td>
								<td class="px-4 py-2.5 text-muted-foreground">{log.entity_type}</td>
								<td class="px-4 py-2.5 font-medium">{log.entity_name || log.entity_id || '—'}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</div>
	{/if}
</div>
