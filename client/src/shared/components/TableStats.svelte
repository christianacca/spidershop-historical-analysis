<script lang="ts">
  interface Props {
    tableId: string;
    visibleCount: number;
    totalRows: number;
    statsLabel?: string;
    onDownload: () => void;
  }

  let { tableId, visibleCount, totalRows, statsLabel = 'rows', onDownload }: Props = $props();
</script>

<div class="table-stats">
  <span>
    <strong>Showing:</strong>
    <span id="visible-count-{tableId}">{visibleCount}</span> of {totalRows} {statsLabel}
  </span>
  <a
    href="#download"
    download
    class="btn btn--download"
    data-action="download-filtered-csv"
    data-table-id={tableId}
    onclick={(e) => { e.preventDefault(); onDownload(); }}
  >⬇️ Download Filtered CSV</a>
</div>

<style>
  .table-stats {
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: var(--spacing-sm);
    font-size: var(--font-sm);
    color: var(--color-text);
    margin-bottom: var(--spacing-xs);
    background: var(--color-info-bg);
    padding: var(--spacing-md);
    border-radius: var(--radius-sm);
  }
</style>
