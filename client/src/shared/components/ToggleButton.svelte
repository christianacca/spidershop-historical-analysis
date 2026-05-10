<script lang="ts">
  import type { Snippet } from 'svelte';

  // ── Types ───────────────────────────────────────────────────────────────────

  interface Props {
    /** Whether the toggle is currently in the expanded state. */
    expanded: boolean;
    /** Callback fired when the button is clicked. */
    onToggle: () => void;
    /** Optional count badge. Pass 0 to render hidden; omit entirely to render nothing. */
    badge?: number;
    /** Forwarded as the `id` attribute on the badge span (for E2E selectors). */
    badgeId?: string;
    /**
     * Extra space-separated class names appended to the button element.
     * Use for E2E selector hooks (e.g. "advanced-filters-toggle") and
     * per-button theming via scoped CSS custom properties on the parent.
     */
    class?: string;
    /**
     * Visual style variant.
     * - `'default'` (default): outlined style matching the signal filter buttons.
     * - `'primary'`: filled blue style for prominent standalone toggles.
     * - `'muted'`: compact transparent style for low-emphasis panel toggles.
     * - `'pill'`: pill-shaped style for embedded card toggles (e.g. GenusSelector).
     */
    variant?: 'default' | 'primary' | 'muted' | 'pill';
    /**
     * Label content. Receives the current `expanded` boolean so the caller
     * can vary the text (or any content) based on state.
     *
     * @example — static label
     * {#snippet children()}More Filters{/snippet}
     *
     * @example — dynamic label
     * {#snippet children(expanded)}
     *   {expanded ? 'Hide individual dates' : 'Show individual dates'}
     * {/snippet}
     */
    children: Snippet<[boolean]>;
    [key: string]: unknown;
  }

  let {
    expanded,
    onToggle,
    badge,
    badgeId,
    class: extraClass = '',
    variant = 'default',
    children,
    ...rest
  }: Props = $props();
</script>

<button
  class="btn toggle-btn {extraClass}"
  class:toggle-btn--primary={variant === 'primary'}
  class:toggle-btn--muted={variant === 'muted'}
  class:toggle-btn--pill={variant === 'pill'}
  class:is-expanded={expanded}
  onclick={onToggle}
  {...rest}
>
  <span class="toggle-btn__arrow">▶</span>
  {@render children(expanded)}
  {#if badge !== undefined}
    <span class="toggle-btn__badge" class:hidden={badge === 0} id={badgeId}>{badge}</span>
  {/if}
</button>

<style>
  .toggle-btn {
    background: var(--toggle-btn-bg, var(--color-surface));
    color: var(--toggle-btn-color, inherit);
    border: var(--toggle-btn-border, 2px solid var(--color-border-light));
    padding: var(--toggle-btn-padding, 8px 16px);
    border-radius: var(--toggle-btn-radius, var(--radius-md));
    font-size: var(--toggle-btn-font-size, inherit);
    font-weight: var(--toggle-btn-font-weight, inherit);
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    transition: all 0.2s;
  }

  .toggle-btn:hover {
    background: var(--toggle-btn-hover-bg, var(--color-surface-alt));
    border-color: var(--toggle-btn-hover-border, var(--color-accent));
  }

  /* ── Primary variant: filled blue, matches .btn--primary ──────────────── */

  .toggle-btn--primary {
    background: var(--toggle-btn-bg, var(--color-accent));
    color: var(--toggle-btn-color, white);
    border: var(--toggle-btn-border, none);
    padding: var(--toggle-btn-padding, 10px 20px);
    font-weight: 600;
  }

  .toggle-btn--primary:hover {
    background: var(--toggle-btn-hover-bg, var(--color-accent-hover));
    border-color: var(--toggle-btn-hover-border, transparent);
  }

  /* ── Muted variant: compact transparent style for low-emphasis panel toggles ── */

  .toggle-btn--muted {
    background: transparent;
    color: var(--color-text-label);
    border: 1px solid var(--color-border-warm);
    padding: 6px 10px;
    font-size: 0.82rem;
    font-weight: normal;
  }

  .toggle-btn--muted:hover {
    background: rgba(0, 0, 0, 0.04);
    border-color: var(--color-border-warm);
  }

  /* ── Pill variant: rounded pill for embedded-card toggles ─────────────── */

  .toggle-btn--pill {
    background: var(--toggle-btn-bg, transparent);
    color: var(--toggle-btn-color, var(--color-text));
    border: var(--toggle-btn-border, 1px solid var(--color-border-warm));
    padding: var(--toggle-btn-padding, 8px 12px);
    border-radius: 999px;
    font-size: var(--toggle-btn-font-size, 0.86rem);
    white-space: nowrap;
  }

  .toggle-btn--pill:hover {
    background: var(--toggle-btn-hover-bg, rgba(0, 0, 0, 0.04));
    border-color: var(--toggle-btn-hover-border, var(--color-border-warm));
  }

  .toggle-btn--pill .toggle-btn__arrow {
    font-size: 0.6rem;
  }

  /* ── Shadow-part equivalent: stable names for consumers to target ─────── */

  .toggle-btn__arrow {
    transition: transform 0.2s;
    font-size: 0.8rem;
  }

  .toggle-btn.is-expanded .toggle-btn__arrow {
    transform: rotate(90deg);
  }

  .toggle-btn__badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    background: var(--color-accent);
    color: #fff;
    border-radius: 50%;
    width: 1.2em;
    height: 1.2em;
    font-size: 0.75em;
    font-weight: 700;
  }

  .toggle-btn__badge.hidden {
    display: none;
  }
</style>
