import type { Meta, StoryObj } from '@storybook/svelte';
import TimeWindowSelector from './TimeWindowSelector.svelte';

const meta: Meta<typeof TimeWindowSelector> = {
  component: TimeWindowSelector,
  title: 'history-page/TimeWindowSelector',
  args: {
    onWindowChange: (id: string) => console.log('onWindowChange', id),
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const ThisMonthActive: Story = {
  args: {
    windowId: 'this-month',
    basisNote: 'Month in progress (May 2026) — comparing May 1 – May 8 against the same span last month (Apr 1 – Apr 8).',
  },
};

export const LastMonthActive: Story = {
  args: {
    windowId: 'last-month',
    basisNote: 'Comparison basis: last full month vs prior full month.',
  },
};

export const CurrentQuarterActive: Story = {
  args: {
    windowId: 'current-quarter',
    basisNote: 'Quarter in progress (Q2 2026) — comparing Apr 1 – May 8 against the same span into Q1 (Jan 1 – Feb 7).',
  },
};

export const LastQuarterActive: Story = {
  args: {
    windowId: 'last-quarter',
    basisNote: 'Comparison basis: last full quarter vs prior full quarter.',
  },
};

export const ThisYearActive: Story = {
  args: {
    windowId: 'this-year',
    basisNote: 'Year in progress (2026) — comparing Jan 1 – May 8 against the same span in 2025.',
  },
};

export const LastYearActive: Story = {
  args: {
    windowId: 'last-year',
    basisNote: 'Comparison basis: last full year vs year before.',
  },
};

export const AllTimeActive: Story = {
  args: {
    windowId: 'all-time',
    basisNote: 'Comparison basis: structural context only, with no prior-period delta.',
  },
};

export const Interactive: Story = {
  args: {
    windowId: 'current-quarter',
    basisNote: 'Quarter in progress (Q2 2026) — comparing Apr 1 – May 8 against the same span into Q1 (Jan 1 – Feb 7).',
  },
};
