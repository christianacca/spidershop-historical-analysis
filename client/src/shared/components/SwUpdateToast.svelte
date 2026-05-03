<script lang="ts">
  import type { Writable } from 'svelte/store';

  let { needRefresh, updateServiceWorker }: {
    needRefresh: Writable<boolean>;
    updateServiceWorker: () => Promise<void>;
  } = $props();

  const AUTO_REFRESH_SECONDS = 30;
  let countdown = $state(AUTO_REFRESH_SECONDS);
  let timer: ReturnType<typeof setInterval> | null = null;

  $effect(() => {
    if ($needRefresh) {
      countdown = AUTO_REFRESH_SECONDS;
      timer = setInterval(() => {
        countdown -= 1;
        if (countdown <= 0) {
          clearInterval(timer!);
          timer = null;
          void updateServiceWorker();
        }
      }, 1000);
      return () => {
        if (timer) {
          clearInterval(timer);
          timer = null;
        }
      };
    }
  });

  function dismiss() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
    needRefresh.set(false);
  }
</script>

{#if $needRefresh}
  <div class="sw-update-toast">
    <span role="status" aria-live="polite">New spider listings available.</span>
    <span aria-hidden="true">Refreshing in {countdown}s…</span>
    <button onclick={() => void updateServiceWorker()}>Refresh now</button>
    <button onclick={dismiss} aria-label="Dismiss">✕</button>
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
