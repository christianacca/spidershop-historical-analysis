import type { Preview } from '@storybook/svelte';

// Import global design tokens so CSS custom properties are available
// in the Storybook canvas (they are defined on :root in common.css).
import '../../templates/common.css';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
  },
};

export default preview;
