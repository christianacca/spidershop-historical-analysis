<script lang="ts">
  import type { WindowId } from './types.js';

  interface Props {
    windowId: WindowId;
    basisNote: string;
    onWindowChange: (id: WindowId) => void;
  }

  const WINDOWS: { id: WindowId; label: string }[] = [
    { id: 'this-month',       label: 'This month' },
    { id: 'last-month',       label: 'Last month' },
    { id: 'current-quarter',  label: 'Current quarter' },
    { id: 'last-quarter',     label: 'Last quarter' },
    { id: 'this-year',        label: 'This year' },
    { id: 'last-year',        label: 'Last year' },
    { id: 'all-time',         label: 'All time' },
  ];

  let { windowId, basisNote, onWindowChange }: Props = $props();
</script>

<div class="window-row">
  {#each WINDOWS as w}
    <button
      class={{ window: true, active: windowId === w.id }}
      aria-pressed={windowId === w.id}
      onclick={() => onWindowChange(w.id)}
    >
      {w.label}
    </button>
  {/each}
</div>
<p class="micro-note">{basisNote}</p>

<style>
  .window-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .window {
    padding: 9px 12px;
    border-radius: 999px;
    border: 1px solid var(--color-border-warm);
    background: #fff;
    color: var(--color-text);
    font-size: 0.88rem;
    cursor: pointer;
    line-height: 1;
    white-space: nowrap;
  }

  .window.active {
    background: var(--color-text);
    border-color: var(--color-text);
    color: #fff;
  }

  .micro-note {
    color: var(--color-text-label);
    font-size: 0.84rem;
    margin: 0;
  }
</style>
