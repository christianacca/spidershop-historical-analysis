<script lang="ts">
  import type { SparklineDto } from '../types.js';

  interface Props {
    dto: SparklineDto | string;
  }

  let { dto }: Props = $props();

  const isDto = $derived(typeof dto === 'object' && dto !== null && 'bars' in dto);
</script>

{#if isDto}
  {@const d = dto as SparklineDto}
  <svg
    class="sparkline"
    width={d.svg_width}
    height={d.svg_height}
    viewBox="0 0 {d.svg_width} {d.svg_height}"
  >
    <title>{d.title}</title>
    {#each d.bars as bar, i}
      {#if bar !== null}
        <rect
          x={i * 10}
          y={d.svg_height - bar.bar_height}
          width="8"
          height={bar.bar_height}
          fill={bar.fill}
          opacity={bar.opacity}
        ><title>{bar.tooltip}</title></rect>
      {/if}
    {/each}
  </svg>
{:else}
  {dto}
{/if}

<style>
  .sparkline {
    vertical-align: middle;
  }
</style>
