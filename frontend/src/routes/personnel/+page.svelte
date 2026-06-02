<script lang="ts">
	import { onMount } from 'svelte';
	import Button from '$lib/components/ui/button.svelte';
	import Badge from '$lib/components/ui/badge.svelte';
	import Dialog from '$lib/components/ui/dialog.svelte';
	import Table from '$lib/components/ui/table.svelte';
	import Input from '$lib/components/ui/input.svelte';
	import { Plus, Pencil, Trash2, Users, Bot, Loader, Mail, ShieldCheck, UserCheck } from '@lucide/svelte';
	import { personnel as personnelApi, type PersonnelItem, type PersonnelCreate } from '$lib/api/personnel';
	import { departments as deptApi, type Department } from '$lib/api/departments';
	import { companyStore } from '$lib/stores/company.svelte';
	import { authStore } from '$lib/stores/auth.svelte';
	import { invitePersonnel } from '$lib/api/client';
	import { t } from '$lib/i18n/index.svelte';

	let people: PersonnelItem[] = $state([]);
	let depts: Department[] = $state([]);
	let loading = $state(true);
	let error: string | null = $state(null);
	let saving = $state(false);

	async function load() {
		loading = true;
		error = null;
		try {
			[people, depts] = await Promise.all([
				personnelApi.list({ company_id: companyStore.active?.id, type: 'human' }),
				deptApi.list(companyStore.active?.id),
			]);
		} catch (e) {
			error = (e as Error).message;
		} finally {
			loading = false;
		}
	}

	onMount(load);

	$effect(() => {
		if (companyStore.active) load();
	});

	function slugify(text: string): string {
		return text
			.toLowerCase()
			.replace(/ğ/g, 'g').replace(/ş/g, 's').replace(/ı/g, 'i')
			.replace(/ö/g, 'o').replace(/ü/g, 'u').replace(/ç/g, 'c')
			.replace(/[^a-z0-9\s-]/g, '').trim()
			.replace(/\s+/g, '-').replace(/-+/g, '-');
	}

	// ── Form ──────────────────────────────────────────────────────────────────
	let showFormDialog = $state(false);
	let editingId: string | null = $state(null);
	let form = $state<PersonnelCreate & { title: string; email: string }>({
		name: '', slug: '', title: '', role: '',
		type: 'human', department_id: '', manager_id: '', email: '',
	});

	$effect(() => {
		if (editingId === null) {
			form.slug = slugify(form.name);
		}
	});

	function openCreate() {
		editingId = null;
		form = { name: '', slug: '', title: '', role: '', type: 'human', department_id: '', manager_id: '', email: '' };
		showFormDialog = true;
	}

	function openEdit(p: PersonnelItem) {
		editingId = p.id;
		form = {
			name: p.name, slug: p.slug, title: p.title ?? '',
			role: p.role ?? '', type: p.type,
			department_id: p.department_id ?? '',
			manager_id: p.manager_id ?? '',
			email: (p as any).email ?? '',
		};
		showFormDialog = true;
	}

	async function save() {
		if (!form.name.trim()) return;
		saving = true;
		try {
			const payload: PersonnelCreate = {
				name: form.name, slug: form.slug,
				title: form.title || undefined, role: form.role || undefined,
				type: form.type,
				email: form.email || undefined,
				department_id: form.department_id || undefined,
				manager_id: form.manager_id || undefined,
			};
			if (editingId) {
				const updated = await personnelApi.update(editingId, payload);
				people = people.map(p => p.id === editingId ? updated : p);
			} else {
				const created = await personnelApi.create(payload);
				people = [...people, created];
			}
			showFormDialog = false;
		} catch (e) {
			alert((e as Error).message);
		} finally {
			saving = false;
		}
	}

	// ── Delete ────────────────────────────────────────────────────────────────
	let deleteTarget: PersonnelItem | null = $state(null);
	let showDeleteDialog = $state(false);
	let deleting = $state(false);

	async function confirmDelete() {
		if (!deleteTarget) return;
		deleting = true;
		try {
			await personnelApi.delete(deleteTarget.id);
			people = people.filter(p => p.id !== deleteTarget!.id);
			deleteTarget = null;
			showDeleteDialog = false;
		} catch (e) {
			alert((e as Error).message);
		} finally {
			deleting = false;
		}
	}

	// ── Invite ────────────────────────────────────────────────────────────────
	const ROLE_OPTIONS = [
		{ value: 'executive',   label: 'Yönetici (Executive)' },
		{ value: 'dept_head',   label: 'Bölüm Yöneticisi' },
		{ value: 'agent_owner', label: 'Ajan Sorumlusu' },
		{ value: 'user',        label: 'Kullanıcı' },
	];

	let inviteTarget: PersonnelItem | null = $state(null);
	let showInviteDialog = $state(false);
	let inviteRole = $state('user');
	let inviting = $state(false);
	let inviteError = $state('');
	let inviteDone = $state(false);

	function openInvite(p: PersonnelItem) {
		inviteTarget = p;
		inviteRole = 'user';
		inviteError = '';
		inviteDone = false;
		showInviteDialog = true;
	}

	async function confirmInvite() {
		if (!inviteTarget) return;
		inviting = true;
		inviteError = '';
		try {
			await invitePersonnel(inviteTarget.id, inviteRole);
			inviteDone = true;
			// Update local record to show has_user
			people = people.map(p =>
				p.id === inviteTarget!.id ? { ...p, has_user: true } as any : p
			);
			setTimeout(() => { showInviteDialog = false; inviteTarget = null; }, 2000);
		} catch (e: any) {
			inviteError = e?.message ?? 'Davet gönderilemedi';
		} finally {
			inviting = false;
		}
	}

	// ── Permissions ───────────────────────────────────────────────────────────
	const activeCompanyId = $derived(companyStore.active?.id ?? '');
	const canManage = $derived(authStore.can(activeCompanyId, 'dept_head'));

	// ── Stats ─────────────────────────────────────────────────────────────────
	const humanCount = $derived(people.filter(p => p.type === 'human').length);
	const agentCount = $derived(people.filter(p => p.type === 'agent').length);
</script>

<svelte:head>
	<title>Personel • fab.engineering</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
		<div>
			<h1 class="font-display text-3xl tracking-tight">{t('personnel_title')}</h1>
			<p class="text-muted-foreground mt-1">
				{#if !loading}
					{humanCount} {t('personnel_type_human')} · {agentCount} {t('personnel_type_agent')}
				{:else}
					{t('loading')}
				{/if}
			</p>
		</div>
		<Button onclick={openCreate} class="w-full sm:w-auto">
			<Plus class="h-4 w-4" />
			{t('personnel_new')}
		</Button>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-20 text-muted-foreground gap-2">
			<Loader class="w-5 h-5 animate-spin" />
			<span class="text-sm">{t('loading')}</span>
		</div>
	{:else if error}
		<div class="rounded-xl border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
			{error}
		</div>
	{:else if people.length === 0}
		<div class="rounded-xl border bg-card flex flex-col items-center justify-center py-20 text-center gap-3">
			<div class="w-12 h-12 rounded-xl bg-muted flex items-center justify-center">
				<Users class="w-6 h-6 text-muted-foreground" />
			</div>
			<div>
				<p class="font-medium">{t('personnel_empty')}</p>
				<p class="text-sm text-muted-foreground mt-1">{t('personnel_empty_subtitle')}</p>
			</div>
			<Button onclick={openCreate} size="sm" class="mt-2">
				<Plus class="h-4 w-4" />
				{t('personnel_new')}
			</Button>
		</div>
	{:else}
		<div class="rounded-xl border bg-card overflow-hidden">
			<Table>
				<thead>
					<tr class="border-b bg-muted/50 text-left text-sm font-medium text-muted-foreground">
						<th class="h-12 px-4">{t('personnel_col_personnel')}</th>
						<th class="h-12 px-4 hidden md:table-cell">{t('personnel_col_dept')}</th>
						<th class="h-12 px-4 hidden lg:table-cell">{t('personnel_col_manager')}</th>
						<th class="h-12 px-4">{t('personnel_col_type')}</th>
						<th class="h-12 px-4 hidden xl:table-cell">{t('personnel_col_platform')}</th>
						<th class="h-12 w-[120px] px-4 text-right">{t('personnel_col_actions')}</th>
					</tr>
				</thead>
				<tbody class="divide-y">
					{#each people as person (person.id)}
						<tr class="hover:bg-muted/30 transition-colors">
							<td class="px-4 py-3">
								<div class="flex items-center gap-3">
									<div class="h-9 w-9 rounded-lg ring-1 ring-border flex-shrink-0 bg-muted flex items-center justify-center">
										{#if person.type === 'agent'}
											<Bot class="w-4 h-4 text-muted-foreground" />
										{:else}
											<span class="text-sm font-semibold text-muted-foreground">{person.name.charAt(0)}</span>
										{/if}
									</div>
									<div>
										<div class="font-medium">{person.name}</div>
										<div class="text-xs text-muted-foreground">{person.title ?? person.role ?? ''}</div>
									</div>
								</div>
							</td>
							<td class="px-4 py-3 text-sm text-muted-foreground hidden md:table-cell">
								{person.department_name ?? '—'}
							</td>
							<td class="px-4 py-3 text-sm text-muted-foreground hidden lg:table-cell">
								{person.manager_name ?? '—'}
							</td>
							<td class="px-4 py-3">
								{#if person.type === 'agent'}
									{#if person.agent_config}
										<Badge variant={person.agent_config.status === 'active' ? 'default' : person.agent_config.status === 'draft' ? 'secondary' : 'outline'}>
											{person.agent_config.status === 'active' ? t('status_active') : person.agent_config.status === 'draft' ? t('status_draft') : t('status_inactive')}
										</Badge>
									{:else}
										<Badge variant="outline">{t('personnel_type_agent')}</Badge>
									{/if}
								{:else}
									<Badge variant="secondary">{t('personnel_type_human')}</Badge>
								{/if}
							</td>
							<td class="px-4 py-3 hidden xl:table-cell">
								{#if person.type === 'human'}
									{#if (person as any).has_user}
										<span class="inline-flex items-center gap-1.5 text-xs text-emerald-600 font-medium">
											<UserCheck class="w-3.5 h-3.5" />
											{t('personnel_status_active')}
										</span>
									{:else if (person as any).email}
										<span class="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
											<Mail class="w-3.5 h-3.5" />
											{t('personnel_not_invited')}
										</span>
									{:else}
										<span class="text-xs text-muted-foreground">—</span>
									{/if}
								{:else}
									<span class="text-xs text-muted-foreground">—</span>
								{/if}
							</td>
							<td class="px-4 py-3">
								<div class="flex justify-end gap-1">
									{#if person.type === 'human' && canManage && (person as any).email && !(person as any).has_user}
										<Button
											variant="ghost" size="icon"
											onclick={() => openInvite(person)}
											aria-label={t('personnel_invite')}
											class="text-primary hover:text-primary hover:bg-primary/10"
											title={t('personnel_platform_invite')}
										>
											<Mail class="h-4 w-4" />
										</Button>
									{/if}
									<Button variant="ghost" size="icon" onclick={() => openEdit(person)} aria-label={t('edit')}>
										<Pencil class="h-4 w-4" />
									</Button>
									<Button
										variant="ghost" size="icon"
										onclick={() => { deleteTarget = person; showDeleteDialog = true; }}
										aria-label={t('delete')}
										class="text-destructive hover:text-destructive hover:bg-destructive/10"
									>
										<Trash2 class="h-4 w-4" />
									</Button>
								</div>
							</td>
						</tr>
					{/each}
				</tbody>
			</Table>
		</div>
	{/if}
</div>

<!-- Create / Edit Dialog -->
<Dialog bind:open={showFormDialog} label={editingId ? t('personnel_edit_title') : t('personnel_add_title')}>
	<div class="space-y-5">
		<h2 class="font-display text-xl tracking-tight">
			{editingId ? t('personnel_edit_title') : t('personnel_add_title')}
		</h2>

		<div class="space-y-4">
			<div class="grid grid-cols-2 gap-3">
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="person-name">{t('personnel_name_label')}</label>
					<Input id="person-name" bind:value={form.name} placeholder="Ahmet Yılmaz" autocomplete="off" />
				</div>
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="person-slug">{t('personnel_slug_label')}</label>
					<Input id="person-slug" bind:value={form.slug} placeholder="ahmet-yilmaz" autocomplete="off" class="font-mono text-xs" />
				</div>
			</div>

			<div class="grid grid-cols-2 gap-3">
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="person-title">{t('personnel_title_label')}</label>
					<Input id="person-title" bind:value={form.title} placeholder="Yazılım Mühendisi" autocomplete="off" />
				</div>
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="person-role">{t('personnel_role_label')}</label>
					<Input id="person-role" bind:value={form.role} placeholder="Engineer" autocomplete="off" />
				</div>
			</div>

			<div class="grid grid-cols-2 gap-3">
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="person-type">{t('personnel_type_label')}</label>
					<select id="person-type" class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" bind:value={form.type}>
						<option value="human">{t('personnel_type_human')}</option>
						<option value="agent">{t('personnel_type_agent')}</option>
					</select>
				</div>
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="person-dept">{t('personnel_dept_label')}</label>
					<select id="person-dept" class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" bind:value={form.department_id}>
						<option value="">{t('select_placeholder')}</option>
						{#each depts as d}
							<option value={d.id}>{d.name}</option>
						{/each}
					</select>
				</div>
			</div>

			<div class="space-y-1.5">
				<label class="text-sm font-medium" for="person-manager">{t('personnel_manager_label')}</label>
				<select id="person-manager" class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring" bind:value={form.manager_id}>
					<option value="">{t('select_placeholder')}</option>
					{#each people.filter(p => p.type === 'human') as p}
						<option value={p.id}>{p.name}</option>
					{/each}
				</select>
			</div>

			{#if form.type === 'human'}
				<div class="space-y-1.5">
					<label class="text-sm font-medium" for="person-email">{t('personnel_email_label')} <span class="text-muted-foreground font-normal">{t('personnel_email_hint')}</span></label>
					<Input id="person-email" type="email" bind:value={form.email} placeholder="ahmet@sirket.com" autocomplete="off" />
				</div>
			{/if}
		</div>

		<div class="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
			<Button variant="outline" onclick={() => (showFormDialog = false)} class="sm:w-auto">{t('cancel')}</Button>
			<Button onclick={save} disabled={!form.name.trim() || saving} class="sm:w-auto">
				{saving ? t('saving') : editingId ? t('update') : t('add')}
			</Button>
		</div>
	</div>
</Dialog>

<!-- Invite Dialog -->
<Dialog bind:open={showInviteDialog} label={t('personnel_invite_title')}>
	<div class="space-y-5">
		<div>
			<h2 class="font-display text-xl tracking-tight">{t('personnel_invite_title')}</h2>
			<p class="text-sm text-muted-foreground mt-1">
				<strong class="text-foreground">{inviteTarget?.name}</strong> adresine
				<strong class="text-foreground">{(inviteTarget as any)?.email}</strong> geçici şifre gönderilecek.
			</p>
		</div>

		{#if inviteDone}
			<div class="flex items-center gap-2 rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2.5 text-sm text-emerald-700">
				<UserCheck class="w-4 h-4 flex-shrink-0" />
				{t('personnel_invite_done')}
			</div>
		{:else}
			<div class="space-y-3">
				<div class="space-y-1.5">
					<label class="text-sm font-medium">{t('personnel_invite_role_label')}</label>
					<select
						class="flex h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
						bind:value={inviteRole}
					>
						{#each ROLE_OPTIONS as opt}
							<option value={opt.value}>{opt.label}</option>
						{/each}
					</select>
					<p class="text-xs text-muted-foreground">{t('personnel_invite_role_hint')}</p>
				</div>

				{#if inviteError}
					<div class="rounded-lg bg-destructive/10 border border-destructive/20 px-3 py-2 text-sm text-destructive">
						{inviteError}
					</div>
				{/if}
			</div>

			<div class="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-end">
				<Button variant="outline" onclick={() => { showInviteDialog = false; inviteTarget = null; }} class="sm:w-auto">{t('cancel')}</Button>
				<Button onclick={confirmInvite} disabled={inviting} class="sm:w-auto gap-2">
					{#if inviting}
						<Loader class="w-4 h-4 animate-spin" />
						{t('sending')}
					{:else}
						<Mail class="w-4 h-4" />
						{t('personnel_invite_send')}
					{/if}
				</Button>
			</div>
		{/if}
	</div>
</Dialog>

<!-- Delete Confirmation -->
<Dialog bind:open={showDeleteDialog} label={t('personnel_delete_title')}>
	<div class="space-y-4">
		<h2 class="font-display text-xl tracking-tight">{t('personnel_delete_title')}</h2>
		<p class="text-sm text-muted-foreground">
			<strong class="text-foreground">{deleteTarget?.name}</strong> {t('personnel_delete_confirm')}
		</p>
		<div class="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
			<Button variant="outline" onclick={() => { deleteTarget = null; showDeleteDialog = false; }} class="sm:w-auto">{t('cancel')}</Button>
			<Button variant="destructive" onclick={confirmDelete} disabled={deleting} class="sm:w-auto">
				{deleting ? t('deleting') : t('delete')}
			</Button>
		</div>
	</div>
</Dialog>
