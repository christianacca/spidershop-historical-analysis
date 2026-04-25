import type { Meta, StoryObj } from '@storybook/svelte';
import MarketEventsCard from './MarketEventsCard.svelte';
import { marketHealthCurrentQuarter } from './__fixtures__/marketHealth.currentQuarter.js';
import { marketHealthAllTime } from './__fixtures__/marketHealth.allTime.js';

const meta: Meta<typeof MarketEventsCard> = {
  component: MarketEventsCard,
  title: 'history-page/MarketEventsCard',
};

export default meta;
type Story = StoryObj<typeof meta>;

export const CurrentQuarter: Story = {
  args: {
    eventsData: marketHealthCurrentQuarter.events,
  },
};

export const AllTime: Story = {
  args: {
    eventsData: marketHealthAllTime.events,
  },
};
