<script lang="ts">
  import type { Snippet } from 'svelte';

  let { label, children }: { label: string; children?: Snippet } = $props();
</script>

<div class="filter-section">
  <span class="filter-label">{label}</span>
  <div class="filter-controls">
    {#if children}{@render children()}{/if}
  </div>
</div>

<style>
  .filter-section {
    display: flex;
    align-items: center;
    margin-bottom: 15px;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
  }

  .filter-label {
    color: var(--color-primary-light);
    margin-right: 10px;
    white-space: nowrap;
  }

  .filter-controls {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    align-items: center;
  }
</style>
