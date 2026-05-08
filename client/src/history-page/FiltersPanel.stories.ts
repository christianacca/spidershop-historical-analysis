import type { Meta, StoryObj } from '@storybook/svelte';
import FiltersPanel from './FiltersPanel.svelte';

const AVAILABLE_GENERA_68 = [
  'Acanthoscurria', 'Aphonopelma', 'Avicularia', 'Bonnetina', 'Brachionopus',
  'Brachypelma', 'Caribena', 'Catumiri', 'Ceratogyrus', 'Chilobrachys',
  'Chromatopelma', 'Cotztetlana', 'Crassicrus', 'Cyclosternum', 'Cyriopagopus',
  'Davus', 'Dolichothele', 'Duolandwalckenaeria', 'Encyocratella', 'Ephebopus',
  'Euathlus', 'Grammostola', 'Guyruita', 'Hapalopus', 'Haplocosmia',
  'Hemirrhagus', 'Holothele', 'Homoeomma', 'Hysterocrates', 'Idiothele',
  'Iridopelma', 'Ischnocolus', 'Kochiana', 'Lasiocyano', 'Lasiodora',
  'Lasiodontes', 'Lyrognathus', 'Megaphobema', 'Monocentropus', 'Neischnocolus',
  'Neoholothele', 'Neostenotarsus', 'Nesipelma', 'Nhandu', 'Nothopelma',
  'Oligoxystre', 'Orphnaecus', 'Ozopactus', 'Pamphobeteus', 'Pelinobius',
  'Phormictopus', 'Phormingochilus', 'Plesiopelma', 'Psalmopoeus', 'Pterinochilus',
  'Pterinopelma', 'Schismatothele', 'Selenobrachys', 'Sericopelma', 'Stromatopelma',
  'Tapinauchenius', 'Theraphosa', 'Thrigmopoeus', 'Tliltocatl', 'Typhochlaena',
  'Xenesthis', 'Yamia', 'Ybyrapora',
].sort();

const MOST_OBSERVED_12 = [
  'Avicularia', 'Brachypelma', 'Caribena', 'Chromatopelma', 'Grammostola',
  'Nhandu', 'Pamphobeteus', 'Psalmopoeus', 'Pterinochilus', 'Tapinauchenius',
  'Theraphosa', 'Tliltocatl',
];

const meta: Meta<typeof FiltersPanel> = {
  component: FiltersPanel,
  title: 'history-page/FiltersPanel',
  args: {
    onSelectionChange: (genera: string[], isAll: boolean) =>
      console.log('onSelectionChange', { genera, isAll }),
    onWindowChange: (id: string) =>
      console.log('onWindowChange', id),
  },
};

export default meta;
type Story = StoryObj<typeof meta>;

export const AllMode: Story = {
  args: {
    availableGenera: AVAILABLE_GENERA_68,
    selectedGenera: [],
    isAllSelected: true,
    mostObservedGenera: MOST_OBSERVED_12,
    windowId: 'current-quarter',
    basisNote: "Quarter in progress (Q2 2026) — comparing Apr 1 – May 8 against the same span into Q1 (Jan 1 – Feb 7).",
    windowLabel: 'Current quarter',
    scopeLabel: '',
  },
};

export const NarrowOneGenus: Story = {
  args: {
    availableGenera: AVAILABLE_GENERA_68,
    selectedGenera: ['Avicularia'],
    isAllSelected: false,
    mostObservedGenera: MOST_OBSERVED_12,
    windowId: 'current-quarter',
    basisNote: "Quarter in progress (Q2 2026) — comparing Apr 1 – May 8 against the same span into Q1 (Jan 1 – Feb 7).",
    windowLabel: 'Current quarter',
    scopeLabel: 'Avicularia',
  },
};

export const NarrowFourGenera: Story = {
  args: {
    availableGenera: AVAILABLE_GENERA_68,
    selectedGenera: ['Avicularia', 'Caribena', 'Grammostola', 'Psalmopoeus'],
    isAllSelected: false,
    mostObservedGenera: MOST_OBSERVED_12,
    windowId: 'last-quarter',
    basisNote: 'Comparison basis: last full quarter vs prior full quarter.',
    windowLabel: 'Last quarter',
    scopeLabel: 'your 4 selected genera',
  },
};
