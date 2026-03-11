<script lang="ts">
  let { tip }: { tip: string } = $props();
</script>

{#if tip}
  <span class="info-tip" tabindex="0">ℹ️<span class="info-tip__text">{tip}</span></span>
{/if}

<style>
  /* Styles are global — defined in common.css (.info-tip, .info-tip__text) */
  /* This block intentionally left as a placeholder to preserve component structure */
  :global(.info-tip) {
    /* See common.css */
  }

  :global(.info-tip__text) {
    /* See common.css */
  }
</style>
