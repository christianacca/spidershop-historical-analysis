<script lang="ts">
  interface Props {
    children: import('svelte').Snippet;
  }
  let { children }: Props = $props();
</script>

<div class="filters-panel advanced-filters-content">
  {@render children()}
</div>

<style>
  .filters-panel {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
    background: var(--color-surface);
    border-radius: var(--radius-md);
    border: 1px solid var(--color-border-light);
    margin-bottom: var(--spacing-sm);
  }
</style>
