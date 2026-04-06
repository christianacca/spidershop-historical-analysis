import type { Meta, StoryObj } from '@storybook/svelte';
import MarketSparkline from './MarketSparkline.svelte';

const SERIES = [170, 172, 173, 175, 176, 178, 180, 181, 183, 184, 184, 184];
const PRIOR  = [165, 166, 168, 169, 171, 172, 174, 175, 176, 177, 177, 177];

const meta: Meta<typeof MarketSparkline> = {
  title: 'History Page/MarketSparkline',
  component: MarketSparkline,
  tags: ['autodocs'],
  args: {
    series: SERIES,
    priorSeries: PRIOR,
    showPrior: true,
    color: '#1f7a6b',
    formatValue: (v: number) => String(v),
    selectedRun: null,
    onRunSelect: (run: number | null) => console.log('onRunSelect', run),
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
};

export const ShowPriorFalse: Story = {
  args: {
    showPrior: false,
    priorSeries: [],
    color: '#cc6b49',
    series: [72, 70, 69, 68, 67, 66, 65, 64, 63, 62, 62, 61],
  },
};

export const RunSelected: Story = {
  args: {
    selectedRun: 5,
  },
};
