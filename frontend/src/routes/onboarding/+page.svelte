<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { marked } from 'marked';
	import {
		Layers, Loader2, Send, Sparkles, Check, ChevronRight,
		Building2, Users, Bot, Zap, FileText, ArrowRight, X,
	} from '@lucide/svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { companyStore } from '$lib/stores/company.svelte';
	import { onboardingApi, type ChatMessage, type OrgStructure } from '$lib/api/onboarding';
	import { i18n } from '$lib/i18n/index.svelte';

	// ── Phase management ──────────────────────────────────────────────────────
	// phase: 'search' | 'chat' | 'preview' | 'creating' | 'done'
	type Phase = 'search' | 'chat' | 'preview' | 'creating' | 'done';
	let phase = $state<Phase>('search');

	// ── Company info ──────────────────────────────────────────────────────────
	const companyId   = $derived($page.url.searchParams.get('company_id') ?? companyStore.active?.id ?? '');
	const companyName = $derived($page.url.searchParams.get('company_name') ?? companyStore.active?.name ?? '');

	// ── Search phase ──────────────────────────────────────────────────────────
	let searching     = $state(false);
	let searchContext = $state('');
	let searchError   = $state('');

	// ── Chat phase ────────────────────────────────────────────────────────────
	let messages    = $state<ChatMessage[]>([]);
	let userInput   = $state('');
	let streaming   = $state(false);
	let streamingText = $state('');
	let aiSignaledReady = $state(false); // AI sent <READY_TO_GENERATE/>
	let chatEl      = $state<HTMLElement | null>(null);
	let inputEl     = $state<HTMLTextAreaElement | null>(null);
	let cleanup: (() => void) | null = null;

	// Count real user replies (exclude the hidden initial trigger that starts with 'Şirket adı:')
	const userReplies = $derived(
		messages.filter(m => m.role === 'user' && !m.content.startsWith('Şirket adı:')).length
	);

	// Gate: show "Yapıyı Oluştur" only after AI signals AND user gave at least 2 real answers
	const readyToGenerate = $derived(aiSignaledReady && userReplies >= 2);

	// ── Preview phase ─────────────────────────────────────────────────────────
	let generating    = $state(false);
	let structure     = $state<OrgStructure | null>(null);
	let generateError = $state('');

	// ── Create phase ──────────────────────────────────────────────────────────
	let createSummary = $state<Record<string, number> | null>(null);
	let createError   = $state('');

	// ── Resume state ─────────────────────────────────────────────────────────
	let resumeBanner = $state(false); // show "kaldığın yerden devam ediyoruz" banner

	// ── Init ──────────────────────────────────────────────────────────────────
	onMount(async () => {
		if (!authStore.isLoggedIn) { goto('/login'); return; }
		if (!companyId) { goto('/settings'); return; }

		// Check for a saved session first
		try {
			const status = await onboardingApi.status(companyId);
			if (status.session) {
				const s = status.session;
				searchContext = s.search_context ?? '';
				messages = s.messages ?? [];
				structure = s.structure ?? null;

				if (s.phase === 'preview' && structure) {
					phase = 'preview';
					resumeBanner = true;
				} else if (s.phase === 'chat' && messages.length > 0) {
					phase = 'chat';
					resumeBanner = true;
					await tick();
					scrollChat();
				} else {
					await startSearch();
				}
				return;
			}
		} catch { /* no saved session, start fresh */ }

		await startSearch();
	});

	async function startSearch() {
		searching = true; searchError = '';
		try {
			const res = await onboardingApi.search(companyName, companyId);
			searchContext = res.context;
			phase = 'chat';
			// Kick off initial AI greeting
			await sendInitialGreeting();
		} catch (e: any) {
			searchError = e?.message ?? i18n.t('ob_error_search');
		} finally {
			searching = false;
		}
	}

	async function sendInitialGreeting() {
		// Send an empty user trigger so AI introduces itself
		const greeting = `Şirket adı: ${companyName}. Lütfen beni onboarding sürecinde yönlendir.`;
		messages = [{ role: 'user', content: greeting }];
		await sendMessage(true);
	}

	async function sendMessage(isAuto = false) {
		if (!isAuto && (!userInput.trim() || streaming)) return;

		const content = isAuto ? '' : userInput.trim();
		if (!isAuto) {
			messages = [...messages, { role: 'user', content }];
			userInput = '';
		}

		streaming = true; streamingText = '';
		await tick();
		scrollChat();

		const token = authStore.token ?? '';
		cleanup = onboardingApi.streamChat(
			companyName,
			searchContext,
			messages,
			token,
			(chunk) => {
				streamingText += chunk;
				scrollChat();
			},
			(ready) => {
				const finalText = streamingText.replace('<READY_TO_GENERATE/>', '').trim();
				messages = [...messages, { role: 'assistant', content: finalText }];
				streamingText = '';
				streaming = false;
				if (ready) aiSignaledReady = true;
				scrollChat();
			},
			(err) => {
				streamingText = '';
				streaming = false;
				messages = [...messages, {
					role: 'assistant',
					content: `${i18n.t('ob_error_prefix')} ${err}`
				}];
			},
			companyId,
			i18n.locale,
		);
	}

	function scrollChat() {
		tick().then(() => {
			if (chatEl) chatEl.scrollTop = chatEl.scrollHeight;
		});
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			sendMessage();
		}
	}

	async function generatePreview() {
		generating = true; generateError = '';
		try {
			const res = await onboardingApi.generate(companyName, searchContext, messages, companyId, i18n.locale);
			structure = res.structure;
			phase = 'preview';
		} catch (e: any) {
			generateError = e?.message ?? i18n.t('ob_error_generate');
		} finally {
			generating = false;
		}
	}

	async function confirmCreate() {
		if (!structure) return;
		phase = 'creating';
		try {
			const res = await onboardingApi.create(companyId, structure);
			createSummary = res.summary;
			phase = 'done';
		} catch (e: any) {
			createError = e?.message ?? i18n.t('ob_error_create');
			phase = 'preview';
		}
	}

	function goToApp() {
		goto('/');
	}

	// ── Helpers ───────────────────────────────────────────────────────────────
	function renderMd(text: string) {
		return marked(text) as string;
	}

	const totalCount = $derived(structure ? (
		(structure.departments?.length ?? 0) +
		(structure.humans?.length ?? 0) +
		(structure.agents?.length ?? 0) +
		(structure.company_skills?.length ?? 0) +
		(structure.policies?.length ?? 0)
	) : 0);
</script>

<svelte:head>
	<title>AI Onboarding • fab.engineering</title>
</svelte:head>

<div class="ob-shell">
	<!-- ── Header ─────────────────────────────────────────────────────────── -->
	<header class="ob-header">
		<div class="flex items-center gap-2.5">
			<div class="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
				<Layers class="w-4 h-4 text-primary-foreground" />
			</div>
			<span class="font-bold tracking-tight text-sm">fab.engineering</span>
		</div>
		<div class="flex items-center gap-2 text-sm text-muted-foreground">
			<Sparkles class="w-4 h-4 text-primary" />
			AI Onboarding
			{#if companyName}
				<span class="text-foreground font-medium">— {companyName}</span>
			{/if}
		</div>
		<a href="/" class="text-xs text-muted-foreground hover:text-foreground transition-colors">
			{i18n.t('ob_skip')} →
		</a>
	</header>

	<!-- ── Step indicators ───────────────────────────────────────────────── -->
	<div class="ob-steps">
		{#each [
			['search', i18n.t('ob_step_search')],
			['chat',   i18n.t('ob_step_chat')],
			['preview',i18n.t('ob_step_preview')],
			['done',   i18n.t('ob_step_done')],
		] as [p, label], i}
			{@const phases = ['search','chat','preview','done']}
			{@const idx = phases.indexOf(phase)}
			{@const stepIdx = phases.indexOf(p)}
			{@const done = idx > stepIdx}
			{@const active = idx === stepIdx}
			<div class="ob-step {active ? 'ob-step-active' : done ? 'ob-step-done' : 'ob-step-pending'}">
				<div class="ob-step-dot">
					{#if done}
						<Check class="w-3 h-3" />
					{:else}
						{i + 1}
					{/if}
				</div>
				<span class="hidden sm:block">{label}</span>
			</div>
			{#if i < 3}
				<div class="ob-step-line {done ? 'bg-primary/50' : 'bg-border'}"></div>
			{/if}
		{/each}
	</div>

	<!-- ── Main content ──────────────────────────────────────────────────── -->
	<main class="ob-main">

		<!-- SEARCH PHASE -->
		{#if phase === 'search'}
			<div class="ob-center">
				<div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6">
					<Sparkles class="w-8 h-8 text-primary animate-pulse" />
				</div>
				{#if searching}
					<h2 class="text-xl font-semibold mb-2">{i18n.t('ob_searching')}</h2>
					<p class="text-muted-foreground text-sm">
						{i18n.t('ob_searching_desc').replace('{name}', companyName)}
					</p>
					<div class="flex gap-1 mt-6">
						{#each [0,1,2] as i}
							<div class="w-2 h-2 rounded-full bg-primary animate-bounce" style="animation-delay: {i * 0.15}s"></div>
						{/each}
					</div>
				{:else if searchError}
					<h2 class="text-xl font-semibold mb-2 text-destructive">{i18n.t('ob_search_error_title')}</h2>
					<p class="text-sm text-muted-foreground mb-4">{searchError}</p>
					<button class="ob-btn-primary" onclick={startSearch}>{i18n.t('ob_retry')}</button>
				{/if}
			</div>

		<!-- CHAT PHASE -->
		{:else if phase === 'chat'}
			<div class="ob-chat-layout">
				{#if resumeBanner}
					<div class="flex items-center gap-2 px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-xl mt-3 text-sm text-amber-800">
						<Check class="w-4 h-4 text-amber-600 flex-shrink-0" />
						{i18n.t('ob_resume_chat')}
						<button class="ml-auto text-xs underline opacity-70 hover:opacity-100" onclick={() => { resumeBanner = false; }}>{i18n.t('ob_close')}</button>
					</div>
				{/if}
				<!-- Messages -->
				<div class="ob-messages" bind:this={chatEl}>
					{#each messages as msg}
						{#if msg.role === 'user' && msg.content.startsWith('Şirket adı:')}
							<!-- skip internal trigger message -->
						{:else}
							<div class="ob-msg ob-msg-{msg.role}">
								{#if msg.role === 'assistant'}
									<div class="ob-avatar">
										<Sparkles class="w-3.5 h-3.5 text-primary" />
									</div>
								{/if}
								<div class="ob-bubble ob-bubble-{msg.role}">
									{#if msg.role === 'assistant'}
										<div class="prose-sm" style="font-size:0.875rem;line-height:1.7">
											{@html renderMd(msg.content)}
										</div>
									{:else}
										<p style="font-size:0.875rem">{msg.content}</p>
									{/if}
								</div>
							</div>
						{/if}
					{/each}

					{#if streaming && streamingText}
						<div class="ob-msg ob-msg-assistant">
							<div class="ob-avatar">
								<Sparkles class="w-3.5 h-3.5 text-primary animate-pulse" />
							</div>
							<div class="ob-bubble ob-bubble-assistant">
								<div class="prose-sm" style="font-size:0.875rem;line-height:1.7">
									{@html renderMd(streamingText.replace('<READY_TO_GENERATE/>', ''))}
								</div>
							</div>
						</div>
					{/if}

					{#if streaming && !streamingText}
						<div class="ob-msg ob-msg-assistant">
							<div class="ob-avatar">
								<Sparkles class="w-3.5 h-3.5 text-primary animate-pulse" />
							</div>
							<div class="ob-bubble ob-bubble-assistant">
								<div class="flex gap-1">
									{#each [0,1,2] as i}
										<div class="w-1.5 h-1.5 rounded-full bg-muted-foreground/50 animate-bounce"
											style="animation-delay: {i * 0.15}s"></div>
									{/each}
								</div>
							</div>
						</div>
					{/if}
				</div>

				<!-- Input area -->
				<div class="ob-input-wrap">
					{#if generateError}
						<div class="text-sm text-destructive mb-2 text-center">{generateError}</div>
					{/if}
					{#if readyToGenerate}
						<!-- AI signaled ready AND user gave ≥2 real answers → show confirm panel -->
						<div class="ob-ready-panel">
							<div class="flex items-center gap-2 text-sm font-medium text-emerald-700">
								<Check class="w-4 h-4 text-emerald-600 flex-shrink-0" />
								{i18n.t('ob_ready_msg')}
							</div>
							<div class="flex gap-3 mt-3">
								<button class="ob-btn-outline" onclick={() => { aiSignaledReady = false; }}>
									{i18n.t('ob_keep_talking')}
								</button>
								<button class="ob-btn-primary" onclick={generatePreview} disabled={generating}>
									{#if generating}
										<Loader2 class="w-4 h-4 animate-spin" />
									{:else}
										<Sparkles class="w-4 h-4" />
									{/if}
									{i18n.t('ob_generate_btn')}
								</button>
							</div>
						</div>
					{:else}
						<div class="ob-input-row">
							<textarea
								bind:this={inputEl}
								bind:value={userInput}
								class="ob-textarea"
								rows="2"
								placeholder={i18n.t('ob_input_placeholder')}
								disabled={streaming}
								onkeydown={handleKeydown}
							></textarea>
							<button
								class="ob-send-btn"
								onclick={() => sendMessage()}
								disabled={!userInput.trim() || streaming}
							>
								{#if streaming}
									<Loader2 class="w-5 h-5 animate-spin" />
								{:else}
									<Send class="w-5 h-5" />
								{/if}
							</button>
						</div>
					{/if}
				</div>
			</div>

		<!-- PREVIEW PHASE -->
		{:else if phase === 'preview' && structure}
			<div class="ob-preview">
				{#if resumeBanner}
					<div class="flex items-center gap-2 px-4 py-2.5 bg-amber-50 border border-amber-200 rounded-xl mb-4 text-sm text-amber-800">
						<Check class="w-4 h-4 text-amber-600 flex-shrink-0" />
						{i18n.t('ob_resume_preview')}
						<button class="ml-auto text-xs underline opacity-70 hover:opacity-100" onclick={() => { resumeBanner = false; }}>{i18n.t('ob_close')}</button>
					</div>
				{/if}
				<div class="mb-6">
					<h2 class="text-2xl font-bold tracking-tight mb-1">{i18n.t('ob_preview_title')}</h2>
					<p class="text-muted-foreground text-sm">
						{i18n.t('ob_preview_desc')}
					</p>
				</div>

				<div class="grid grid-cols-2 sm:grid-cols-5 gap-3 mb-6">
					<div class="rounded-xl border bg-card p-4 flex flex-col items-center gap-2">
						<div class="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center"><Building2 class="w-5 h-5 text-blue-600" /></div>
						<div class="text-2xl font-bold">{structure.departments?.length ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_dept')}</div>
					</div>
					<div class="rounded-xl border bg-card p-4 flex flex-col items-center gap-2">
						<div class="w-10 h-10 rounded-xl bg-green-50 flex items-center justify-center"><Users class="w-5 h-5 text-green-600" /></div>
						<div class="text-2xl font-bold">{structure.humans?.length ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_human')}</div>
					</div>
					<div class="rounded-xl border bg-card p-4 flex flex-col items-center gap-2">
						<div class="w-10 h-10 rounded-xl bg-violet-50 flex items-center justify-center"><Bot class="w-5 h-5 text-violet-600" /></div>
						<div class="text-2xl font-bold">{structure.agents?.length ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_agent')}</div>
					</div>
					<div class="rounded-xl border bg-card p-4 flex flex-col items-center gap-2">
						<div class="w-10 h-10 rounded-xl bg-amber-50 flex items-center justify-center"><Zap class="w-5 h-5 text-amber-600" /></div>
						<div class="text-2xl font-bold">{structure.company_skills?.length ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_skill')}</div>
					</div>
					<div class="rounded-xl border bg-card p-4 flex flex-col items-center gap-2">
						<div class="w-10 h-10 rounded-xl bg-rose-50 flex items-center justify-center"><FileText class="w-5 h-5 text-rose-600" /></div>
						<div class="text-2xl font-bold">{structure.policies?.length ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_policy')}</div>
					</div>
				</div>

				<!-- Collapsible details -->
				<div class="space-y-3 mb-6">
					<!-- Departments -->
					<details class="ob-detail-block">
						<summary class="ob-detail-summary">
							<Building2 class="w-4 h-4 text-blue-600" />
							{i18n.t('ob_section_depts')} ({structure.departments?.length ?? 0})
						</summary>
						<div class="pt-3 space-y-2">
							{#each (structure.departments ?? []) as d}
								<div class="flex items-start gap-2 text-sm">
									<ChevronRight class="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
									<div>
										<span class="font-medium">{d.name}</span>
										{#if d.description}
											<span class="text-muted-foreground"> — {d.description}</span>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					</details>

					<!-- Agents -->
					<details class="ob-detail-block">
						<summary class="ob-detail-summary">
							<Bot class="w-4 h-4 text-violet-600" />
							{i18n.t('ob_section_agents')} ({structure.agents?.length ?? 0})
						</summary>
						<div class="pt-3 space-y-2">
							{#each (structure.agents ?? []) as ag}
								<div class="flex items-start gap-2 text-sm">
									<ChevronRight class="w-4 h-4 text-muted-foreground mt-0.5 flex-shrink-0" />
									<div>
										<span class="font-medium">{ag.name}</span>
										<span class="text-muted-foreground"> ({ag.title})</span>
										{#if ag.skills?.length}
											<div class="flex gap-1 mt-1 flex-wrap">
												{#each ag.skills as sk}
													<span class="text-xs bg-muted px-1.5 py-0.5 rounded">{sk}</span>
												{/each}
											</div>
										{/if}
									</div>
								</div>
							{/each}
						</div>
					</details>

					<!-- Skills -->
					<details class="ob-detail-block">
						<summary class="ob-detail-summary">
							<Zap class="w-4 h-4 text-amber-600" />
							{i18n.t('ob_section_skills')} ({structure.company_skills?.length ?? 0})
						</summary>
						<div class="pt-3 grid sm:grid-cols-2 gap-2">
							{#each (structure.company_skills ?? []) as sk}
								<div class="text-sm flex items-center gap-2">
									<ChevronRight class="w-4 h-4 text-muted-foreground flex-shrink-0" />
									<span class="font-medium">{sk.name}</span>
									<span class="text-muted-foreground text-xs">— {sk.description}</span>
								</div>
							{/each}
						</div>
					</details>

					<!-- Policies -->
					<details class="ob-detail-block">
						<summary class="ob-detail-summary">
							<FileText class="w-4 h-4 text-rose-600" />
							{i18n.t('ob_section_policies')} ({structure.policies?.length ?? 0})
						</summary>
						<div class="pt-3 space-y-1.5">
							{#each (structure.policies ?? []) as pol}
								<div class="text-sm flex items-center gap-2">
									<ChevronRight class="w-4 h-4 text-muted-foreground flex-shrink-0" />
									<span class="font-medium">{pol.name}</span>
									<span class="text-xs bg-muted px-1.5 py-0.5 rounded">{pol.scope}</span>
								</div>
							{/each}
						</div>
					</details>
				</div>

				{#if createError}
					<div class="rounded-lg border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive mb-4">
						{createError}
					</div>
				{/if}

				<div class="flex gap-3 justify-end">
					<button class="ob-btn-outline" onclick={() => { phase = 'chat'; aiSignaledReady = false; }}>
						{i18n.t('ob_back_chat')}
					</button>
					<button class="ob-btn-primary" onclick={confirmCreate}>
						<Sparkles class="w-4 h-4" />
						{totalCount} {i18n.t('ob_create_btn')}
					</button>
				</div>
			</div>

		<!-- CREATING PHASE -->
		{:else if phase === 'creating'}
			<div class="ob-center">
				<div class="w-16 h-16 rounded-2xl bg-primary/10 flex items-center justify-center mb-6">
					<Loader2 class="w-8 h-8 text-primary animate-spin" />
				</div>
				<h2 class="text-xl font-semibold mb-2">{i18n.t('ob_creating')}</h2>
				<p class="text-muted-foreground text-sm">
					{i18n.t('ob_creating_desc')}
				</p>
			</div>

		<!-- DONE PHASE -->
		{:else if phase === 'done' && createSummary}
			<div class="ob-center">
				<div class="w-20 h-20 rounded-2xl bg-emerald-100 flex items-center justify-center mb-6">
					<Check class="w-10 h-10 text-emerald-600" />
				</div>
				<h2 class="text-2xl font-bold mb-1">{i18n.t('ob_done_title')}</h2>
				<p class="text-muted-foreground text-sm mb-8">
					{i18n.t('ob_done_desc').replace('{name}', companyName)}
				</p>

				<div class="grid grid-cols-3 sm:grid-cols-5 gap-3 mb-10">
					<div class="flex flex-col items-center gap-1.5 p-4 rounded-xl border bg-card">
						<div class="w-10 h-10 bg-blue-50 rounded-xl flex items-center justify-center"><Building2 class="w-5 h-5 text-blue-600" /></div>
						<div class="text-2xl font-bold">{createSummary['departments'] ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_dept')}</div>
					</div>
					<div class="flex flex-col items-center gap-1.5 p-4 rounded-xl border bg-card">
						<div class="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center"><Users class="w-5 h-5 text-green-600" /></div>
						<div class="text-2xl font-bold">{createSummary['humans'] ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_human')}</div>
					</div>
					<div class="flex flex-col items-center gap-1.5 p-4 rounded-xl border bg-card">
						<div class="w-10 h-10 bg-violet-50 rounded-xl flex items-center justify-center"><Bot class="w-5 h-5 text-violet-600" /></div>
						<div class="text-2xl font-bold">{createSummary['agents'] ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_agent')}</div>
					</div>
					<div class="flex flex-col items-center gap-1.5 p-4 rounded-xl border bg-card">
						<div class="w-10 h-10 bg-amber-50 rounded-xl flex items-center justify-center"><Zap class="w-5 h-5 text-amber-600" /></div>
						<div class="text-2xl font-bold">{createSummary['skills'] ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_skill')}</div>
					</div>
					<div class="flex flex-col items-center gap-1.5 p-4 rounded-xl border bg-card">
						<div class="w-10 h-10 bg-rose-50 rounded-xl flex items-center justify-center"><FileText class="w-5 h-5 text-rose-600" /></div>
						<div class="text-2xl font-bold">{createSummary['policies'] ?? 0}</div>
						<div class="text-xs text-muted-foreground">{i18n.t('ob_stat_policy')}</div>
					</div>
				</div>

				<button class="ob-btn-primary text-base px-8 py-3" onclick={goToApp}>
					{i18n.t('ob_go_app')} <ArrowRight class="w-5 h-5 ml-1" />
				</button>
			</div>
		{/if}

	</main>
</div>

<style>
.ob-shell {
	min-height: 100vh;
	background: hsl(var(--background));
	display: flex;
	flex-direction: column;
}
.ob-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	padding: 1rem 2rem;
	border-bottom: 1px solid hsl(var(--border));
	background: hsl(var(--card));
	flex-shrink: 0;
}
.ob-steps {
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 0;
	padding: 1.25rem 2rem;
	border-bottom: 1px solid hsl(var(--border));
	background: hsl(var(--card)/0.5);
	flex-shrink: 0;
}
.ob-step {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	font-size: 0.8125rem;
	font-weight: 500;
}
.ob-step-dot {
	width: 1.5rem; height: 1.5rem;
	border-radius: 9999px;
	display: flex; align-items: center; justify-content: center;
	font-size: 0.6875rem; font-weight: 700;
	flex-shrink: 0;
}
.ob-step-active .ob-step-dot { background: hsl(var(--primary)); color: hsl(var(--primary-foreground)); }
.ob-step-active { color: hsl(var(--foreground)); }
.ob-step-done .ob-step-dot { background: hsl(var(--primary)/0.15); color: hsl(var(--primary)); }
.ob-step-done { color: hsl(var(--muted-foreground)); }
.ob-step-pending .ob-step-dot { background: hsl(var(--muted)); color: hsl(var(--muted-foreground)); }
.ob-step-pending { color: hsl(var(--muted-foreground)); }
.ob-step-line { flex: 1; height: 1px; max-width: 80px; margin: 0 0.5rem; }

.ob-main {
	flex: 1;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}
.ob-center {
	flex: 1;
	display: flex;
	flex-direction: column;
	align-items: center;
	justify-content: center;
	padding: 3rem 2rem;
	text-align: center;
}

/* ── Chat layout ── */
.ob-chat-layout {
	flex: 1;
	display: flex;
	flex-direction: column;
	max-width: 760px;
	width: 100%;
	margin: 0 auto;
	padding: 0 1rem;
	overflow: hidden;
}
.ob-messages {
	flex: 1;
	overflow-y: auto;
	padding: 1.5rem 0;
	space-y: 1rem;
	display: flex;
	flex-direction: column;
	gap: 1rem;
}
.ob-msg { display: flex; gap: 0.75rem; align-items: flex-start; }
.ob-msg-user { flex-direction: row-reverse; }
.ob-avatar {
	width: 2rem; height: 2rem;
	border-radius: 9999px;
	background: hsl(var(--primary)/0.1);
	display: flex; align-items: center; justify-content: center;
	flex-shrink: 0;
}
.ob-bubble {
	max-width: 80%;
	padding: 0.75rem 1rem;
	border-radius: 1rem;
}
.ob-bubble-assistant {
	background: hsl(var(--muted));
	border-bottom-left-radius: 0.25rem;
}
.ob-bubble-user {
	background: hsl(var(--primary));
	color: hsl(var(--primary-foreground));
	border-bottom-right-radius: 0.25rem;
}
.ob-input-wrap {
	padding: 1rem 0 1.5rem;
	border-top: 1px solid hsl(var(--border));
	flex-shrink: 0;
}
.ob-input-row { display: flex; gap: 0.75rem; align-items: flex-end; }
.ob-textarea {
	flex: 1;
	border: 1px solid hsl(var(--input));
	border-radius: 0.75rem;
	background: hsl(var(--background));
	padding: 0.625rem 0.875rem;
	font-size: 0.875rem;
	line-height: 1.5;
	resize: none;
	outline: none;
	font-family: inherit;
}
.ob-textarea:focus { box-shadow: 0 0 0 2px hsl(var(--ring)/0.3); }
.ob-send-btn {
	width: 2.5rem; height: 2.5rem;
	border-radius: 0.75rem;
	background: hsl(var(--primary));
	color: hsl(var(--primary-foreground));
	display: flex; align-items: center; justify-content: center;
	border: none; cursor: pointer; flex-shrink: 0;
	transition: opacity 0.15s;
}
.ob-send-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.ob-ready-panel {
	background: #f0fdf4;
	border: 1px solid #bbf7d0;
	border-radius: 0.875rem;
	padding: 1rem 1.25rem;
	margin-bottom: 0.25rem;
}

/* ── Preview ── */
.ob-preview {
	flex: 1;
	overflow-y: auto;
	max-width: 860px;
	width: 100%;
	margin: 0 auto;
	padding: 2rem 1rem;
}
.ob-detail-block {
	border: 1px solid hsl(var(--border));
	border-radius: 0.75rem;
	padding: 0.875rem 1rem;
	background: hsl(var(--card));
}
.ob-detail-block[open] { padding-bottom: 1rem; }
.ob-detail-summary {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	font-size: 0.875rem;
	font-weight: 600;
	cursor: pointer;
	list-style: none;
	user-select: none;
}
.ob-detail-summary::-webkit-details-marker { display: none; }

/* ── Buttons ── */
.ob-btn-primary {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
	padding: 0.625rem 1.25rem;
	background: hsl(var(--primary));
	color: hsl(var(--primary-foreground));
	border: none;
	border-radius: 0.625rem;
	font-size: 0.875rem;
	font-weight: 600;
	cursor: pointer;
	transition: opacity 0.15s;
}
.ob-btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.ob-btn-outline {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
	padding: 0.625rem 1.25rem;
	background: transparent;
	border: 1px solid hsl(var(--border));
	border-radius: 0.625rem;
	font-size: 0.875rem;
	font-weight: 500;
	cursor: pointer;
	transition: background 0.15s;
}
.ob-btn-outline:hover { background: hsl(var(--muted)); }

/* ── Prose ── */
:global(.ob-bubble-assistant .prose-sm h1) { font-size: 1rem; font-weight: 700; margin: 0.5rem 0 0.3rem; }
:global(.ob-bubble-assistant .prose-sm h2) { font-size: 0.9rem; font-weight: 600; margin: 0.5rem 0 0.25rem; }
:global(.ob-bubble-assistant .prose-sm p)  { margin: 0.2rem 0; }
:global(.ob-bubble-assistant .prose-sm ul) { padding-left: 1.25rem; margin: 0.25rem 0; }
:global(.ob-bubble-assistant .prose-sm li) { margin: 0.1rem 0; }
:global(.ob-bubble-assistant .prose-sm strong) { font-weight: 600; }
:global(.ob-bubble-assistant .prose-sm code) {
	font-family: monospace; font-size: 0.8em;
	background: hsl(var(--muted-foreground)/0.1); padding: 0.1em 0.3em; border-radius: 0.25rem;
}
</style>
