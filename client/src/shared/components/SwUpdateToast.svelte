<script lang="ts">
  import type { Writable } from 'svelte/store';

  let { needRefresh, updateServiceWorker }: {
    needRefresh: Writable<boolean>;
    updateServiceWorker: (reloadPage?: boolean) => Promise<void>;
  } = $props();
</script>

{#if $needRefresh}
  <div class="sw-update-toast" role="status" aria-live="polite">
    <span>New data has been deployed.</span>
    <button onclick={() => updateServiceWorker(true)}>Refresh</button>
    <button onclick={() => needRefresh.set(false)} aria-label="Dismiss">✕</button>
  </div>
{/if}

<style>
  @keyframes slide-up {
    from { transform: translateY(calc(100% + var(--spacing-lg))); opacity: 0; }
    to   { transform: translateY(0); opacity: 1; }
  }

  .sw-update-toast {
    position: fixed;
    bottom: var(--spacing-lg);
    right: var(--spacing-lg);
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    background: var(--color-accent);
    color: #fff;
    border-radius: var(--radius-md);
    padding: var(--spacing-sm) var(--spacing-md);
    /* rgba() used intentionally: no design token for shadow opacity */
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    z-index: 1000;
    font-size: var(--font-sm);
    animation: slide-up 0.25s ease-out;
  }

  button {
    background: none;
    border: 1px solid currentColor;
    border-radius: var(--radius-sm);
    color: inherit;
    cursor: pointer;
    padding: 2px 8px;
    font-size: var(--font-sm);
  }

  @media (max-width: 480px) {
    .sw-update-toast {
      left: var(--spacing-lg);
    }

    button {
      min-height: 44px;
    }
  }
</style>
