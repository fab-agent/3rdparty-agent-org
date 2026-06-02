<script lang="ts">
	import { onMount, tick } from 'svelte';
	import { page } from '$app/stores';
	import {
		Bot,
		Send,
		Plus,
		ChevronDown,
		Loader2,
		Wrench,
		CheckCircle2,
		X,
		MessageSquare,
		Shield,
		Zap,
		Info,
		ChevronRight
	} from '@lucide/svelte';
	import Button from '$lib/components/ui/button.svelte';
	import MessageContent from '$lib/components/MessageContent.svelte';
	import { sessionsApi, streamMessage, type Session, type SessionMessage } from '$lib/api/sessions';
	import { personnel as personnelApi, type PersonnelItem } from '$lib/api/personnel';
	import { companyStore } from '$lib/stores/company.svelte';

	// ── State ─────────────────────────────────────────────────────────────────

	let agents = $state<PersonnelItem[]>([]);
	let sessions = $state<Session[]>([]);
	let activeSession = $state<Session | null>(null);
	let messages = $state<SessionMessage[]>([]);

	let selectedAgent = $state<PersonnelItem | null>(null);
	let agentMenuOpen = $state(false);
	let infoPanelOpen = $state(true);
	let agentSkills = $state<Array<{ id: string; name: string; version: string; description: string | null; skill_type: string; is_active: boolean }>>([]);
	let agentPolicies = $state<string[]>([]);
	let input = $state('');
	let streaming = $state(false);
	let streamingText = $state('');
	let streamingTools = $state<Array<{ name: string; args: unknown; result?: string }>>([]);

	let messagesEl = $state<HTMLElement | null>(null);
	let inputEl = $state<HTMLTextAreaElement | null>(null);
	let abortController: AbortController | null = null;

	// ── Load ─────────────────────────────────────────────────────────────────

	onMount(async () => {
		await loadAgents();
		await loadSessions();

		// Pre-select agent from URL param
		const agentId = $page.url.searchParams.get('agent');
		if (agentId) {
			selectedAgent = agents.find((a) => a.id === agentId) ?? null;
		}
	});

	$effect(() => {
		if (companyStore.active) {
			activeSession = null;
			messages = [];
			selectedAgent = null;
			agentSkills = [];
			loadAgents();
			loadSessions();
		}
	});

	async function loadAgents() {
		try {
			agents = await personnelApi.list({
				type: 'agent',
				company_id: companyStore.active?.id
			});
		} catch {
			agents = [];
		}
	}

	async function loadSessions() {
		try {
			const all = await sessionsApi.list();
			const agentIds = new Set(agents.map(a => a.id));
			sessions = all.filter(s => agentIds.has(s.personnel_id));
		} catch {
			sessions = [];
		}
	}

	async function loadAgentInfo(agent: PersonnelItem) {
		// Skills
		try {
			const skills = await personnelApi.listSkills(agent.id);
			agentSkills = skills as typeof agentSkills;
		} catch {
			agentSkills = [];
		}
		// Policies from agent_config dept — fetch via agent detail
		try {
			const detail = await personnelApi.get(agent.id);
			// policies come from agent's org-tree or department — approximate via dept
			agentPolicies = [];
		} catch {
			agentPolicies = [];
		}
	}

	async function openSession(s: Session) {
		activeSession = s;
		const detail = await sessionsApi.get(s.id);
		messages = detail.messages ?? [];
		const agent = agents.find((a) => a.id === s.personnel_id) ?? null;
		selectedAgent = agent;
		if (agent) await loadAgentInfo(agent);
		await scrollToBottom();
	}

	async function newSession() {
		if (!selectedAgent) return;
		const s = await sessionsApi.create(selectedAgent.id);
		sessions = [s, ...sessions];
		activeSession = s;
		messages = [];
	}

	async function closeSession(s: Session) {
		await sessionsApi.close(s.id);
		sessions = sessions.filter((x) => x.id !== s.id);
		if (activeSession?.id === s.id) {
			activeSession = null;
			messages = [];
		}
	}

	// ── Messaging ─────────────────────────────────────────────────────────────

	async function send() {
		const content = input.trim();
		if (!content || streaming) return;

		if (!activeSession) {
			if (!selectedAgent) return;
			const s = await sessionsApi.create(selectedAgent.id);
			sessions = [s, ...sessions];
			activeSession = s;
			messages = [];
		}

		input = '';
		streaming = true;
		streamingText = '';
		streamingTools = [];

		// Optimistic user message
		const userMsg: SessionMessage = {
			id: crypto.randomUUID(),
			session_id: activeSession.id,
			role: 'user',
			content,
			tool_calls: [],
			tool_results: [],
			tokens_used: null,
			created_at: new Date().toISOString()
		};
		messages = [...messages, userMsg];
		await scrollToBottom();

		abortController = new AbortController();

		try {
			for await (const event of streamMessage(activeSession.id, content, abortController.signal)) {
				if (event.type === 'text') {
					streamingText += event.content;
					await scrollToBottom();
				} else if (event.type === 'tool_call') {
					streamingTools = [...streamingTools, { name: event.name, args: event.args }];
					await scrollToBottom();
				} else if (event.type === 'tool_result') {
					streamingTools = streamingTools.map((t) =>
						t.name === event.name && t.result === undefined
							? { ...t, result: event.result }
							: t
					);
					await scrollToBottom();
				} else if (event.type === 'done') {
					// Replace streaming state with final persisted message
					const detail = await sessionsApi.get(activeSession.id);
					messages = detail.messages ?? [];
					streamingText = '';
					streamingTools = [];
					// Update session title in list
					sessions = sessions.map((s) =>
						s.id === activeSession!.id ? { ...s, title: detail.title } : s
					);
					await scrollToBottom();
				} else if (event.type === 'error') {
					streamingText = `[Error: ${event.message}]`;
				} else if (event.type === 'stream_end') {
					break;
				}
			}
		} catch (e: unknown) {
			if ((e as Error)?.name !== 'AbortError') {
				streamingText = '[Connection error]';
			}
		} finally {
			streaming = false;
			abortController = null;
		}
	}

	function cancelStream() {
		abortController?.abort();
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			send();
		}
	}

	async function scrollToBottom() {
		await tick();
		if (messagesEl) {
			messagesEl.scrollTop = messagesEl.scrollHeight;
		}
	}

	function formatTime(iso: string) {
		return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
	}
</script>

<div class="flex h-full bg-background">
	<!-- ── Session sidebar ────────────────────────────────────────────────── -->
	<div class="w-64 border-r border-border flex flex-col flex-shrink-0 bg-muted/20">
		<!-- Agent selector -->
		<div class="p-3 border-b border-border">
			<div class="relative">
				<button
					class="w-full flex items-center gap-2 px-3 py-2 rounded-lg bg-background border border-border text-sm hover:bg-muted transition-colors"
					onclick={() => (agentMenuOpen = !agentMenuOpen)}
				>
					<Bot class="w-4 h-4 text-primary flex-shrink-0" />
					<span class="flex-1 text-left truncate text-foreground">
						{selectedAgent?.name ?? 'Ajan seç...'}
					</span>
					<ChevronDown class="w-3.5 h-3.5 text-muted-foreground flex-shrink-0" />
				</button>

				{#if agentMenuOpen}
					<div
						class="absolute top-full mt-1 left-0 right-0 bg-background border border-border rounded-xl shadow-lg z-20 overflow-hidden"
					>
						{#each agents as agent}
							<button
								class="w-full flex items-center gap-2 px-3 py-2.5 text-sm hover:bg-muted text-left transition-colors"
								onclick={() => {
									selectedAgent = agent;
									agentMenuOpen = false;
									loadAgentInfo(agent);
								}}
							>
								<div
									class="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0"
								>
									<Bot class="w-3.5 h-3.5 text-primary" />
								</div>
								<div class="min-w-0">
									<div class="font-medium truncate">{agent.name}</div>
									{#if agent.title}
										<div class="text-xs text-muted-foreground truncate">{agent.title}</div>
									{/if}
								</div>
							</button>
						{/each}
						{#if agents.length === 0}
							<div class="px-3 py-4 text-sm text-muted-foreground text-center">
								Henüz ajan yok
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>

		<!-- New session button -->
		<div class="p-2 border-b border-border">
			<Button
				variant="outline"
				class="w-full gap-2 text-sm h-9"
				onclick={newSession}
				disabled={!selectedAgent}
			>
				<Plus class="w-3.5 h-3.5" />
				Yeni Sohbet
			</Button>
		</div>

		<!-- Session list -->
		<div class="flex-1 overflow-y-auto p-2 space-y-1">
			{#each sessions as s}
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<!-- svelte-ignore a11y_click_events_have_key_events -->
				<div
					role="button"
					tabindex="0"
					class="w-full text-left px-3 py-2.5 rounded-xl text-sm transition-colors group relative cursor-pointer
						{activeSession?.id === s.id ? 'bg-primary/10 text-primary' : 'hover:bg-muted text-foreground'}"
					onclick={() => openSession(s)}
					onkeydown={(e) => e.key === 'Enter' && openSession(s)}
				>
					<div class="flex items-start gap-2 pr-6">
						<MessageSquare class="w-3.5 h-3.5 mt-0.5 flex-shrink-0 opacity-60" />
						<div class="min-w-0 flex-1">
							<div class="truncate font-medium text-xs leading-snug">
								{s.title ?? 'Yeni sohbet'}
							</div>
							{#if s.last_message}
								<div class="truncate text-xs text-muted-foreground mt-0.5">
									{s.last_message.content.slice(0, 40)}
								</div>
							{/if}
						</div>
					</div>
					<!-- Delete button on hover -->
					<button
						class="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 hover:text-destructive transition-all"
						onclick={(e) => {
							e.stopPropagation();
							closeSession(s);
						}}
					>
						<X class="w-3 h-3" />
					</button>
				</div>
			{/each}
			{#if sessions.length === 0}
				<div class="px-3 py-6 text-center text-xs text-muted-foreground">
					Sohbet yok
				</div>
			{/if}
		</div>
	</div>

	<!-- ── Chat area ──────────────────────────────────────────────────────── -->
	<div class="flex-1 flex min-w-0 overflow-hidden">
	<!-- Main chat column -->
	<div class="flex-1 flex flex-col min-w-0">
		{#if activeSession}
			<!-- Header -->
			<div class="px-6 py-4 border-b border-border flex items-center gap-3 flex-shrink-0">
				<div class="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
					<Bot class="w-4 h-4 text-primary" />
				</div>
				<div>
					<div class="font-semibold text-sm">{selectedAgent?.name ?? 'Ajan'}</div>
					{#if selectedAgent?.title}
						<div class="text-xs text-muted-foreground">{selectedAgent.title}</div>
					{/if}
				</div>
				<div class="ml-auto flex items-center gap-2">
					{#if streaming}
						<span class="text-xs text-muted-foreground flex items-center gap-1.5">
							<Loader2 class="w-3 h-3 animate-spin" />
							Yanıtlanıyor...
						</span>
						<button
							class="text-xs text-muted-foreground hover:text-foreground transition-colors"
							onclick={cancelStream}
						>
							Durdur
						</button>
					{/if}
				</div>
			</div>

			<!-- Messages -->
			<div
				bind:this={messagesEl}
				class="flex-1 overflow-y-auto px-6 py-4 space-y-4"
			>
				{#if messages.length === 0 && !streaming}
					<div class="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
						<Bot class="w-12 h-12 mb-3 opacity-20" />
						<p class="text-sm">Bir mesaj yazarak sohbete başlayın.</p>
					</div>
				{/if}

				{#each messages as msg (msg.id)}
					{#if msg.role === 'user'}
						<!-- User bubble -->
						<div class="flex justify-end">
							<div class="max-w-[72%]">
								<div class="bg-primary text-primary-foreground rounded-2xl rounded-tr-sm px-4 py-2.5">
									<MessageContent content={msg.content} />
								</div>
								<div class="text-xs text-muted-foreground text-right mt-1 px-1">
									{formatTime(msg.created_at)}
								</div>
							</div>
						</div>
					{:else}
						<!-- Assistant bubble -->
						<div class="flex gap-3">
							<div class="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
								<Bot class="w-3.5 h-3.5 text-primary" />
							</div>
							<div class="flex-1 min-w-0">
								{#if msg.tool_calls?.length > 0}
									<!-- Tool calls -->
									{#each msg.tool_calls as tc, i}
										<details class="mb-2 rounded-xl border border-border overflow-hidden text-xs" open={false}>
											<summary class="flex items-center gap-2 px-3 py-2 bg-muted/50 font-medium cursor-pointer list-none">
												<Wrench class="w-3 h-3 text-primary flex-shrink-0" />
												<span class="flex-1 font-mono">{tc.name}</span>
												<CheckCircle2 class="w-3 h-3 text-green-500 flex-shrink-0" />
											</summary>
											{#if msg.tool_results?.[i]}
												<div class="px-3 py-2.5 bg-background">
													<MessageContent content={msg.tool_results[i].result} />
												</div>
											{/if}
										</details>
									{/each}
								{/if}
								{#if msg.content}
									<div class="bg-muted/40 rounded-2xl rounded-tl-sm px-4 py-3">
										<MessageContent content={msg.content} />
									</div>
								{/if}
								<div class="text-xs text-muted-foreground mt-1 px-1">
									{formatTime(msg.created_at)}
								</div>
							</div>
						</div>
					{/if}
				{/each}

				<!-- Live streaming response -->
				{#if streaming}
					<div class="flex gap-3">
						<div class="w-7 h-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
							<Bot class="w-3.5 h-3.5 text-primary" />
						</div>
						<div class="flex-1 min-w-0">
							<!-- Live tool calls -->
							{#each streamingTools as t}
								<div class="mb-2 rounded-xl border border-border overflow-hidden text-xs">
									<div class="flex items-center gap-2 px-3 py-2 bg-muted/50 font-medium">
										<Wrench class="w-3 h-3 text-primary" />
										<span>{t.name}</span>
										{#if t.result === undefined}
											<Loader2 class="w-3 h-3 animate-spin ml-auto" />
										{:else}
											<CheckCircle2 class="w-3 h-3 text-green-500 ml-auto" />
										{/if}
									</div>
									{#if t.result !== undefined}
										<div class="px-3 py-2.5 bg-background">
											<MessageContent content={t.result} />
										</div>
									{/if}
								</div>
							{/each}

							<!-- Live text -->
							{#if streamingText}
								<div class="bg-muted/40 rounded-2xl rounded-tl-sm px-4 py-3">
									<MessageContent content={streamingText} streaming={true} />
									<span class="inline-block w-0.5 h-3.5 bg-foreground/60 ml-0.5 animate-pulse align-text-bottom"></span>
								</div>
							{:else if streamingTools.length === 0}
								<div class="bg-muted/40 rounded-2xl rounded-tl-sm px-4 py-2.5">
									<Loader2 class="w-4 h-4 animate-spin text-muted-foreground" />
								</div>
							{/if}
						</div>
					</div>
				{/if}
			</div>

			<!-- Input -->
			<div class="px-6 py-4 border-t border-border flex-shrink-0">
				<div class="flex items-end gap-3 bg-muted/30 rounded-2xl border border-border px-4 py-3 focus-within:border-primary/50 transition-colors">
					<textarea
						bind:this={inputEl}
						bind:value={input}
						onkeydown={handleKeydown}
						placeholder="Mesaj yazın... (Enter gönderin, Shift+Enter yeni satır)"
						rows={1}
						disabled={streaming}
						class="flex-1 bg-transparent text-sm resize-none outline-none placeholder:text-muted-foreground min-h-[20px] max-h-[120px] leading-5 disabled:opacity-50"
						style="height: auto; overflow-y: hidden;"
						oninput={(e) => {
							const t = e.currentTarget;
							t.style.height = 'auto';
							t.style.height = Math.min(t.scrollHeight, 120) + 'px';
						}}
					></textarea>
					<Button
						size="sm"
						onclick={send}
						disabled={!input.trim() || streaming}
						class="rounded-xl h-8 w-8 p-0 flex-shrink-0"
					>
						<Send class="w-3.5 h-3.5" />
					</Button>
				</div>
				<p class="text-xs text-muted-foreground text-center mt-2">
					{selectedAgent?.name ?? 'Ajan'} · Mesajlar kaydedilir
				</p>
			</div>
		{:else}
			<!-- Empty state - no active session -->
			<div class="flex-1 flex flex-col items-center justify-center text-muted-foreground p-8">
				<div class="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
					<MessageSquare class="w-8 h-8 text-primary/50" />
				</div>
				<h2 class="text-lg font-semibold text-foreground mb-1">Sohbete Başlayın</h2>
				<p class="text-sm text-center max-w-sm mb-6">
					Bir ajan seçin ve yeni sohbet başlatın. Ajanlar politika ve araçlarıyla yanıt verecektir.
				</p>
				{#if selectedAgent}
					<Button onclick={newSession} class="gap-2">
						<Plus class="w-4 h-4" />
						{selectedAgent.name} ile Sohbet Başlat
					</Button>
				{:else if agents.length > 0}
					<p class="text-sm">Sol panelden bir ajan seçin.</p>
				{:else}
					<p class="text-sm">
						Önce <a href="/agents" class="text-primary underline">Ajanlar</a> sayfasından bir ajan yapılandırın.
					</p>
				{/if}
			</div>
		{/if}
	</div>

	<!-- ── Agent Info Panel ───────────────────────────────────────────────── -->
	{#if selectedAgent && infoPanelOpen}
		<div class="w-72 border-l border-border flex flex-col flex-shrink-0 bg-muted/10 overflow-y-auto">
			<!-- Agent card -->
			<div class="p-4 border-b border-border">
				<div class="flex items-center justify-between mb-3">
					<span class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Ajan Bilgisi</span>
					<button
						class="text-muted-foreground hover:text-foreground transition-colors"
						onclick={() => (infoPanelOpen = false)}
					>
						<X class="w-3.5 h-3.5" />
					</button>
				</div>
				<div class="flex items-center gap-2.5">
					<div class="w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
						<Bot class="w-4.5 h-4.5 text-primary" />
					</div>
					<div class="min-w-0">
						<div class="font-semibold text-sm truncate">{selectedAgent.name}</div>
						{#if selectedAgent.title}
							<div class="text-xs text-muted-foreground truncate">{selectedAgent.title}</div>
						{/if}
					</div>
				</div>

				{#if selectedAgent.agent_config}
					{@const cfg = selectedAgent.agent_config}
					<div class="mt-3 flex flex-wrap gap-1.5">
						<span class="px-2 py-0.5 rounded-full text-xs bg-muted border border-border font-mono">
							{cfg.model}
						</span>
						<span class="px-2 py-0.5 rounded-full text-xs border font-medium
							{cfg.status === 'active' ? 'bg-green-50 text-green-700 border-green-200' :
							 cfg.status === 'draft'  ? 'bg-amber-50 text-amber-700 border-amber-200' :
							                          'bg-muted text-muted-foreground border-border'}">
							{cfg.status === 'active' ? 'Aktif' : cfg.status === 'draft' ? 'Taslak' : 'Pasif'}
						</span>
					</div>
				{/if}
			</div>

			<!-- Skills -->
			{#if agentSkills.length > 0}
				<div class="p-4 border-b border-border">
					<div class="flex items-center gap-1.5 mb-2.5">
						<Zap class="w-3.5 h-3.5 text-primary" />
						<span class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Araçlar & Yetenekler</span>
					</div>
					<div class="space-y-1.5">
						{#each agentSkills as skill}
							<div class="flex items-start gap-2 px-2.5 py-2 rounded-lg bg-background border border-border/60">
								<div class="flex-1 min-w-0">
									<div class="flex items-center gap-1.5">
										<span class="text-xs font-medium truncate">{skill.name}</span>
										{#if !skill.is_active}
											<span class="text-xs text-muted-foreground">(pasif)</span>
										{/if}
									</div>
									{#if skill.description}
										<div class="text-xs text-muted-foreground mt-0.5 leading-snug">{skill.description}</div>
									{/if}
								</div>
								<span class="flex-shrink-0 px-1.5 py-0.5 rounded text-[10px] font-medium uppercase tracking-wide
									{skill.skill_type === 'builtin' ? 'bg-blue-50 text-blue-600' :
									 skill.skill_type === 'mcp'     ? 'bg-purple-50 text-purple-600' :
									 skill.skill_type === 'http'    ? 'bg-green-50 text-green-600' :
									                                   'bg-orange-50 text-orange-600'}">
									{skill.skill_type}
								</span>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Department policies -->
			{#if selectedAgent.department_name}
				<div class="p-4">
					<div class="flex items-center gap-1.5 mb-2.5">
						<Shield class="w-3.5 h-3.5 text-primary" />
						<span class="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Departman</span>
					</div>
					<div class="flex items-center gap-2 px-2.5 py-2 rounded-lg bg-background border border-border/60 mb-2">
						<span class="text-xs font-medium">{selectedAgent.department_name}</span>
					</div>
					{#if selectedAgent.manager_name}
						<div class="text-xs text-muted-foreground">
							Yönetici: {selectedAgent.manager_name}
						</div>
					{/if}
				</div>
			{/if}
		</div>
	{:else if selectedAgent && !infoPanelOpen}
		<!-- Collapsed toggle -->
		<div class="w-8 border-l border-border flex flex-col items-center pt-4 flex-shrink-0 bg-muted/10">
			<button
				class="text-muted-foreground hover:text-foreground transition-colors p-1"
				onclick={() => (infoPanelOpen = true)}
				title="Ajan bilgisini göster"
			>
				<Info class="w-4 h-4" />
			</button>
		</div>
	{/if}
	</div>
</div>

<!-- Click outside to close agent menu -->
{#if agentMenuOpen}
	<!-- svelte-ignore a11y_click_events_have_key_events -->
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div class="fixed inset-0 z-10" onclick={() => (agentMenuOpen = false)}></div>
{/if}
