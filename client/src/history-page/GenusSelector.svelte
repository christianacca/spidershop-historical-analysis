<script lang="ts" module>
  const LIFESTYLE_PRESETS = {
    arboreal: ['Avicularia', 'Caribena', 'Psalmopoeus', 'Poecilotheria', 'Tapinauchenius', 'Ybyrapora', 'Iridopelma'],
    terrestrial: ['Grammostola', 'Aphonopelma', 'Brachypelma', 'Tliltocatl', 'Nhandu', 'Chromatopelma', 'Euathlus'],
    fossorial: ['Chilobrachys', 'Cyriopagopus', 'Haplocosmia', 'Pelinobius', 'Ceratogyrus', 'Idiothele'],
  } as const;
</script>

<script lang="ts">
  interface Props {
    availableGenera: string[];
    selectedGenera: string[];
    isAllSelected: boolean;
    mostObservedGenera: string[];
    onSelectionChange: (genera: string[], isAll: boolean) => void;
    initialExpanded?: boolean;
  }

  let {
    availableGenera,
    selectedGenera,
    isAllSelected,
    mostObservedGenera,
    onSelectionChange,
    initialExpanded = false,
  }: Props = $props();

  let expanded: boolean = $state(initialExpanded);
  let search: string = $state('');

  const availableCount = $derived(availableGenera.length);
  const selectedCount = $derived(selectedGenera.length);
  const countLabel = $derived(
    isAllSelected
      ? `All genera • ${availableCount} available`
      : `${selectedCount} of ${availableCount} genera selected`
  );
  const filteredSuggestions = $derived(
    search.trim() === ''
      ? availableGenera
      : availableGenera.filter(g => g.toLowerCase().includes(search.toLowerCase()))
  );

  function toggleGenus(genus: string) {
    if (selectedGenera.includes(genus)) {
      const newGenera = selectedGenera.filter(g => g !== genus);
      if (newGenera.length === 0) {
        selectAll();
      } else {
        onSelectionChange(newGenera, false);
      }
    } else {
      onSelectionChange([...selectedGenera, genus], false);
    }
  }

  function selectAll() {
    onSelectionChange([], true);
    expanded = false;
  }

  function clearAll() {
    selectAll();
  }

  function applyPreset(key: keyof typeof LIFESTYLE_PRESETS) {
    const filtered = LIFESTYLE_PRESETS[key].filter(g => availableGenera.includes(g));
    onSelectionChange(filtered, false);
  }

  function applyMostObserved() {
    onSelectionChange(mostObservedGenera, false);
  }
</script>

<div class="selector-shell">
  <div class="selector-header">
    <div class="selector-title">
      <span class="scope-label">{countLabel}</span>
    </div>
    <button
      class="selector-toggle"
      aria-expanded={expanded}
      aria-controls="genus-expanded-content"
      onclick={() => (expanded = !expanded)}
    >
      <span class="toggle-icon" class:rotated={expanded}>▶</span>
      {expanded ? 'Hide genus selector' : 'Show genus selector'}
    </button>
  </div>

  {#if !isAllSelected}
    <div class="chips">
      {#each selectedGenera as genus}
        <span class="chip selected">
          {genus}
          <button class="dismiss" aria-label="Remove {genus}" onclick={() => toggleGenus(genus)}>×</button>
        </span>
      {/each}
    </div>
  {:else if !expanded}
    <p class="collapsed-note">All genera are in scope for Market Health KPIs. Select specific genera to narrow the focus and unlock comparison controls.</p>
  {/if}

  {#if expanded}
    <div class="expanded-preview" id="genus-expanded-content">
      <div class="search-shell">
        <div class="search-box">
          <span class="search-icon" aria-hidden="true">🔍</span>
          <input
            class="search-input"
            type="text"
            aria-label="Search genus"
            role="combobox"
            aria-expanded={filteredSuggestions.length > 0}
            aria-controls="genus-suggestion-list"
            bind:value={search}
          />
        </div>
        <div class="suggestion-list" id="genus-suggestion-list" role="listbox">
          {#each filteredSuggestions as genus}
            <button
              class="suggestion-row"
              role="option"
              aria-selected={selectedGenera.includes(genus)}
              onclick={() => toggleGenus(genus)}
            >
              <strong>{genus}</strong>
              <span class="suggestion-status" class:selected={selectedGenera.includes(genus)}>
                {selectedGenera.includes(genus) ? 'Selected' : 'Available'}
              </span>
            </button>
          {/each}
        </div>
      </div>
      <div class="quick-pick-row">
        <button class="quick-pick" class:active={isAllSelected} onclick={selectAll}>All</button>
        <button class="quick-pick" onclick={applyMostObserved}>Most observed</button>
        <button class="quick-pick" onclick={() => applyPreset('arboreal')}>Arboreal</button>
        <button class="quick-pick" onclick={() => applyPreset('terrestrial')}>Terrestrial</button>
        <button class="quick-pick" onclick={() => applyPreset('fossorial')}>Fossorial</button>
        <button class="quick-pick-action" onclick={clearAll}>Clear all</button>
      </div>
    </div>
  {/if}
</div>

<style>
  .selector-shell {
    display: grid;
    gap: 12px;
    padding: 12px;
    border: 1px solid var(--color-border-warm);
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.72);
  }

  .selector-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }

  .selector-title {
    display: flex;
    align-items: center;
    gap: 8px;
    min-width: 0;
  }

  .scope-label {
    display: inline-flex;
    padding: 8px 12px;
    border-radius: 999px;
    background: rgba(31, 122, 107, 0.12);
    color: var(--color-market-health);
    font-size: 0.86rem;
    font-weight: 700;
    white-space: nowrap;
  }

  .selector-toggle {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid var(--color-border-warm);
    background: #fff;
    color: var(--color-text);
    font-size: 0.86rem;
    cursor: pointer;
    white-space: nowrap;
  }

  .toggle-icon {
    display: inline-block;
    font-size: 0.6rem;
    transition: transform 0.2s;
  }

  .toggle-icon.rotated {
    transform: rotate(90deg);
  }

  .chips {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 9px 12px;
    border-radius: 999px;
    border: 1px solid var(--color-border-warm);
    background: #fff;
    color: var(--color-text);
    font-size: 0.92rem;
  }

  .chip.selected {
    background: rgba(204, 107, 73, 0.14);
    border-color: rgba(204, 107, 73, 0.28);
    font-weight: 700;
  }

  .dismiss {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0 2px;
    border: none;
    background: transparent;
    color: inherit;
    font-size: 1rem;
    cursor: pointer;
    line-height: 1;
  }

  .collapsed-note {
    color: var(--color-text-label);
    font-size: 0.9rem;
    margin: 0;
  }

  .search-shell {
    display: grid;
    gap: 8px;
  }

  .search-box {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid var(--color-border-warm);
    background: #fff;
  }

  .search-icon {
    font-size: 1rem;
  }

  .search-input {
    flex: 1;
    border: none;
    outline: none;
    background: transparent;
    color: var(--color-text);
    font-size: 0.92rem;
  }

  .suggestion-list {
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.84);
    max-height: 240px;
    overflow-y: auto;
    display: grid;
    gap: 4px;
    padding: 4px;
  }

  .suggestion-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 10px;
    border-radius: 12px;
    border: none;
    background: rgba(247, 242, 232, 0.7);
    color: var(--color-text);
    cursor: pointer;
    text-align: left;
    width: 100%;
  }

  .suggestion-status {
    padding: 4px 8px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 600;
    background: rgba(31, 122, 107, 0.08);
    color: var(--color-text-label);
    flex-shrink: 0;
  }

  .suggestion-status.selected {
    background: rgba(204, 107, 73, 0.14);
    color: var(--color-breeder-focus);
  }

  .quick-pick-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .quick-pick {
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px dashed rgba(31, 42, 44, 0.18);
    background: rgba(255, 255, 255, 0.78);
    color: var(--color-text);
    font-size: 0.86rem;
    font-weight: 700;
    cursor: pointer;
  }

  .quick-pick.active {
    background: var(--color-text);
    border-style: solid;
    color: #fff;
  }

  .quick-pick-action {
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid rgba(31, 42, 44, 0.22);
    background: transparent;
    color: var(--color-text-label);
    font-size: 0.86rem;
    font-weight: 400;
    cursor: pointer;
  }

  .expanded-preview {
    display: grid;
    gap: 12px;
  }
</style>
