import type { Meta, StoryObj } from '@storybook/svelte';
import MarketHealthSection from './MarketHealthSection.svelte';
import { marketHealthCurrentQuarter } from './__fixtures__/marketHealth.currentQuarter.js';
import { marketHealthLastQuarter } from './__fixtures__/marketHealth.lastQuarter.js';
import { marketHealthAllTime } from './__fixtures__/marketHealth.allTime.js';
import { marketHealthStockUnderPressure } from './__fixtures__/marketHealth.stockUnderPressure.js';

const meta: Meta<typeof MarketHealthSection> = {
  component: MarketHealthSection,
  title: 'history-page/MarketHealthSection',
};

export default meta;
type Story = StoryObj<typeof meta>;

export const CurrentQuarter: Story = {
  args: {
    payload: marketHealthCurrentQuarter,
  },
};

export const LastQuarter: Story = {
  args: {
    payload: marketHealthLastQuarter,
  },
};

export const AllTime: Story = {
  args: {
    payload: marketHealthAllTime,
  },
};

export const StockUnderPressure: Story = {
  args: {
    payload: marketHealthStockUnderPressure,
  },
};

export const RunSelected: Story = {
  args: {
    payload: marketHealthCurrentQuarter,
    initialSelectedRun: 8,
  },
};
