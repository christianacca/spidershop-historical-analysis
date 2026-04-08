import type { Meta, StoryObj } from '@storybook/svelte';
import MarketKpiCard from './MarketKpiCard.svelte';
import { marketHealthCurrentQuarter } from './__fixtures__/marketHealth.currentQuarter.js';
import { marketHealthAllTime } from './__fixtures__/marketHealth.allTime.js';

const { observed, stock, price } = marketHealthCurrentQuarter.kpis;

const meta: Meta<typeof MarketKpiCard> = {
  title: 'History Page/MarketKpiCard',
  component: MarketKpiCard,
  tags: ['autodocs'],
  args: {
    card: observed,
    series: marketHealthCurrentQuarter.sparklineSeries.observed,
    showPrior: true,
    selectedRun: null,
    onRunSelect: (run: number | null) => console.log('onRunSelect', run),
    windowScopeLabel: 'current quarter',
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const PositiveDelta: Story = {
  args: {},
};

export const NegativeDelta: Story = {
  args: {
    card: stock,
    series: marketHealthCurrentQuarter.sparklineSeries.stock,
  },
};

export const FlatDelta: Story = {
  args: {
    card: price,
    series: marketHealthAllTime.sparklineSeries.price,
    showPrior: false,
    windowScopeLabel: 'all time',
  },
};

export const AllTimeNoPrior: Story = {
  args: {
    card: marketHealthAllTime.kpis.observed,
    series: marketHealthAllTime.sparklineSeries.observed,
    showPrior: false,
    windowScopeLabel: 'all time',
  },
};

export const RunSelected: Story = {
  args: {
    card: observed,
    series: marketHealthCurrentQuarter.sparklineSeries.observed,
    selectedRun: 5,
  },
};
