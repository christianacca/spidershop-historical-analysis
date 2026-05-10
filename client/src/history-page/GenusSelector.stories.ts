import type { Meta, StoryObj } from '@storybook/svelte';
import GenusSelector from './GenusSelector.svelte';

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

const meta: Meta<typeof GenusSelector> = {
  component: GenusSelector,
  title: 'history-page/GenusSelector',
  args: {
    onSelectionChange: (genera: string[], isAll: boolean) =>
      console.log('onSelectionChange', { genera, isAll }),
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
  },
};

export const NarrowOneGenus: Story = {
  args: {
    availableGenera: AVAILABLE_GENERA_68,
    selectedGenera: ['Avicularia'],
    isAllSelected: false,
    mostObservedGenera: MOST_OBSERVED_12,
  },
};

export const NarrowMultipleGenera: Story = {
  args: {
    availableGenera: AVAILABLE_GENERA_68,
    selectedGenera: ['Avicularia', 'Caribena', 'Psalmopoeus', 'Chromatopelma'],
    isAllSelected: false,
    mostObservedGenera: MOST_OBSERVED_12,
  },
};

export const ExpandedWithSearch: Story = {
  args: {
    availableGenera: AVAILABLE_GENERA_68,
    selectedGenera: [],
    isAllSelected: true,
    mostObservedGenera: MOST_OBSERVED_12,
    initialExpanded: true,
  },
};

export const ExpandedWithResults: Story = {
  args: {
    availableGenera: ['Avicularia', 'Caribena', 'Chromatopelma'],
    selectedGenera: ['Caribena'],
    isAllSelected: false,
    mostObservedGenera: ['Avicularia', 'Caribena'],
    initialExpanded: true,
  },
};
