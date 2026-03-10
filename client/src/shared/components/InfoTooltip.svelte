<script lang="ts">
  let { tip }: { tip: string } = $props();
</script>

{#if tip}
  <span class="info-icon" tabindex="0">ℹ️<span class="tooltip">{tip}</span></span>
{/if}

<style>
  .info-icon {
    display: inline-block;
    margin-left: 6px;
    cursor: pointer;
    font-size: 0.85rem;
    opacity: 0.7;
    position: relative;
    transition: opacity 0.2s;
  }

  .info-icon:hover,
  .info-icon:focus {
    opacity: 1;
    outline: none;
  }

  .tooltip {
    visibility: hidden;
    opacity: 0;
    position: absolute;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    background-color: var(--color-primary);
    color: #fff;
    padding: 12px 16px;
    border-radius: var(--radius-md);
    font-size: 0.85rem;
    min-width: 200px;
    max-width: 400px;
    text-align: left;
    text-transform: none;
    letter-spacing: normal;
    line-height: 1.5;
    z-index: 1000;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    transition: opacity 0.3s, visibility 0.3s;
    pointer-events: none;
    white-space: normal;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  /* Tooltip arrow */
  .tooltip::after {
    content: '';
    position: absolute;
    top: 100%;
    left: 50%;
    transform: translateX(-50%);
    border: 6px solid transparent;
    border-top-color: var(--color-primary);
  }

  /* Show tooltip on hover (desktop) */
  .info-icon:hover .tooltip {
    visibility: visible;
    opacity: 1;
  }

  /* Show tooltip on focus (keyboard navigation) */
  .info-icon:focus .tooltip {
    visibility: visible;
    opacity: 1;
  }

  /* Mobile: show tooltip on tap */
  @media (hover: none) and (pointer: coarse) {
    .info-icon:active .tooltip {
      visibility: visible;
      opacity: 1;
    }
  }

  /* Adjust tooltip position for mobile to avoid overflow */
  @media (max-width: 768px) {
    .tooltip {
      width: 240px;
      font-size: 0.8rem;
    }
  }
</style>
