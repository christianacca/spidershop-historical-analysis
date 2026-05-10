<script lang="ts">
  import type { Writable } from 'svelte/store';
  import Spinner from './Spinner.svelte';

  let { needRefresh, updateServiceWorker }: {
    needRefresh: Writable<boolean>;
    updateServiceWorker: () => Promise<void>;
  } = $props();

  const AUTO_REFRESH_SECONDS = 30;
  let countdown = $state(AUTO_REFRESH_SECONDS);
  let refreshing = $state(false);
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

  async function handleRefresh() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
    refreshing = true;
    await updateServiceWorker();
    // Reload is handled by updateServiceWorker in register-sw.ts:
    // - Normal case (waiting SW): via the 'controlling' event listener.
    // - Race case (no waiting SW): via direct window.location.reload().
  }
</script>

{#if $needRefresh}
  <div class="sw-update-toast">
    <span role="status" aria-live="polite">New spider listings available.</span>
    {#if refreshing}
      <Spinner label="Refreshing page" />
    {:else}
      <span aria-hidden="true">Refreshing in {countdown}s…</span>
    {/if}
    <button onclick={handleRefresh} disabled={refreshing}>
      {#if refreshing}Refreshing…{:else}Refresh now{/if}
    </button>
    <button onclick={dismiss} aria-label="Dismiss" disabled={refreshing}>✕</button>
  </div>
{/if}

<style>
  @keyframes slide-up {
    from { transform: translateY(calc(100% + var(--spacing-lg))); opacity: 0; }
    to   { transform: translateY(0); opacity: 1; }
  }

  @keyframes slide-down {
    from { transform: translateY(calc(-100% - var(--spacing-md))); opacity: 0; }
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

  button:disabled {
    cursor: not-allowed;
    opacity: 0.5;
  }

  @media (max-width: 480px) {
    .sw-update-toast {
      /* On mobile, position at the top of the viewport rather than the bottom.
         position:fixed;bottom:N uses the CSS viewport height, which on iOS Safari
         and Android Chrome may exceed the actual visible area (URL bar + system
         navigation bar), pushing the toast below the visible screen.
         top:N is always visible — browser chrome at the top pushes content
         downward, so the toast stays within the visual viewport. */
      top: var(--spacing-md);
      bottom: auto;
      left: var(--spacing-lg);
      flex-wrap: wrap;
      animation-name: slide-down;
    }

    button {
      min-height: 44px;
    }
  }
</style>
