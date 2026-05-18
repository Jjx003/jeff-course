<script lang="ts">
  /**
   * ProgressRing
   *
   * Compact SVG ring used on the /stats page and on track cards. Animates
   * the stroke smoothly on mount and whenever `value` changes. Renders a
   * centered label inside the ring.
   */
  interface Props {
    /** Current value in [0, 1]. */
    value: number;
    /** Outer diameter in px. */
    size?: number;
    /** Stroke width in px. */
    stroke?: number;
    /** Label rendered inside the ring (e.g. "8/24"). */
    label?: string;
    /** Sub-label rendered below the main label. */
    sublabel?: string;
    /** Override the ring color. Defaults to accent blue. */
    color?: string;
  }

  let {
    value,
    size = 96,
    stroke = 8,
    label = '',
    sublabel = '',
    color = '#60a5fa'
  }: Props = $props();

  let clamped = $derived(Math.max(0, Math.min(1, value)));
  let r = $derived((size - stroke) / 2);
  let c = $derived(2 * Math.PI * r);
  let dashOffset = $derived(c * (1 - clamped));
  let isFull = $derived(clamped >= 1);
</script>

<div class="ring-wrap" style="width: {size}px; height: {size}px;">
  <svg width={size} height={size} class="ring" class:full={isFull}>
    <circle
      class="ring-track"
      cx={size / 2}
      cy={size / 2}
      r={r}
      stroke-width={stroke}
      fill="none"
    />
    <circle
      class="ring-progress"
      cx={size / 2}
      cy={size / 2}
      r={r}
      stroke-width={stroke}
      stroke={color}
      fill="none"
      stroke-dasharray={c}
      stroke-dashoffset={dashOffset}
      stroke-linecap="round"
      transform="rotate(-90 {size / 2} {size / 2})"
    />
  </svg>
  <div class="ring-center">
    {#if label}<div class="ring-label">{label}</div>{/if}
    {#if sublabel}<div class="ring-sublabel">{sublabel}</div>{/if}
  </div>
</div>

<style>
  .ring-wrap {
    position: relative;
    display: inline-block;
  }
  .ring {
    transform: rotate(0deg);
  }
  .ring-track {
    stroke: #1f2937;
  }
  .ring-progress {
    transition: stroke-dashoffset 600ms cubic-bezier(0.22, 1, 0.36, 1);
  }
  .ring.full .ring-progress {
    /* Subtle "complete" highlight without going neon. */
    filter: drop-shadow(0 0 4px rgba(96, 165, 250, 0.35));
  }
  .ring-center {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    pointer-events: none;
  }
  .ring-label {
    font-size: 0.95rem;
    font-weight: 600;
    color: #e2e8f0;
    line-height: 1;
    font-variant-numeric: tabular-nums;
  }
  .ring-sublabel {
    font-size: 0.62rem;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.2rem;
  }
</style>
