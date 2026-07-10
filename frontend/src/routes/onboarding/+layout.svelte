<script lang="ts">
	import '../../app.css';
	import type { Snippet } from 'svelte';
	let { children }: { children: Snippet } = $props();
</script>

<!-- Blank layout — no sidebar, no topnav -->
{@render children()}
