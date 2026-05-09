<script lang="ts">
  let {
    size = '1em',
    label = 'Loading',
  }: {
    /** CSS length value for the spinner's width and height. Defaults to `'1em'`. */
    size?: string;
    /** Accessible label announced by screen readers. Defaults to `'Loading'`. */
    label?: string;
  } = $props();
</script>

<span class="spinner" role="status" aria-label={label} style:--spinner-size={size}></span>

<style>
  .spinner {
    display: inline-block;
    width: var(--spinner-size, 1em);
    height: var(--spinner-size, 1em);
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
    flex-shrink: 0;
    vertical-align: middle;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
