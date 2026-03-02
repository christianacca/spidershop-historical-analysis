<script lang="ts">
  interface Props {
    label: string;
    value: string;
    active: boolean;
    onclick: () => void;
    /** Any additional HTML attributes (e.g. data-action, data-signal, data-limit)
     *  are spread directly onto the <button> element. */
    [key: string]: unknown;
  }

  let { label, value, active, onclick, ...rest }: Props = $props();
</script>

<button class={{ 'filter-btn': true, 'is-active': active }} data-value={value} {onclick} {...rest}>
  {label}
</button>

<style>
  .filter-btn {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    background-color: var(--color-surface);
    color: var(--color-text);
    font-size: var(--font-sm);
    cursor: pointer;
    transition: background-color 0.15s ease, border-color 0.15s ease;
  }

  .filter-btn:hover {
    background-color: var(--color-surface-light);
    border-color: var(--color-border-alt);
  }

  .filter-btn.is-active {
    background-color: var(--color-primary);
    border-color: var(--color-primary);
    color: #fff;
  }
</style>
