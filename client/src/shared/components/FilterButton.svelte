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
    gap: 6px;
    padding: 8px 16px;
    border: 2px solid var(--color-border-light);
    background-color: var(--color-surface);
    border-radius: var(--radius-md);
    cursor: pointer;
    font-size: var(--font-base);
    transition: all 0.2s;
  }

  .filter-btn:hover {
    border-color: var(--color-accent);
    background-color: var(--color-surface-alt);
  }

  .filter-btn.is-active {
    background-color: var(--color-accent);
    border-color: var(--color-accent);
    color: #fff;
  }
</style>
