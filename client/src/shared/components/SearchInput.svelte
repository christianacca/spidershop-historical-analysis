<script lang="ts">
  interface Props {
    placeholder: string;
    tableId: string;
    oninput: (value: string) => void;
  }

  let { placeholder, tableId, oninput }: Props = $props();

  function handleInput(event: Event): void {
    oninput((event.target as HTMLInputElement).value);
  }
</script>

<input
  id="search-{tableId}"
  type="text"
  class="search-input"
  data-action="search"
  {placeholder}
  data-table-id={tableId}
  oninput={handleInput}
/>

<style>
  .search-input {
    width: 100%;
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    font-size: var(--font-base);
    color: var(--color-text);
    background-color: var(--color-surface);
  }

  .search-input:focus {
    outline: none;
    border-color: var(--color-primary);
  }

  .search-input::placeholder {
    color: var(--color-text-dim);
  }
</style>
