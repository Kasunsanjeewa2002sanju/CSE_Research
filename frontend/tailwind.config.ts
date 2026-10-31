import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
    './dev/**/*.{js,ts,jsx,tsx}',
    './tests/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // 60% White & Cool Neutrals
        surface: {
          white: 'var(--surface-white)',
          card: 'var(--surface-card)',
          subtle: 'var(--surface-card-subtle)',
        },
        background: 'var(--background)',
        border: {
          DEFAULT: 'var(--border)',
          strong: 'var(--border-strong)',
        },
        text: {
          primary: 'var(--text-primary)',
          muted: 'var(--text-muted)',
          subtle: 'var(--text-subtle)',
        },

        // 30% Blue Family (Headers, Headings, Key Surfaces & Series)
        blue: {
          navy: 'var(--blue-navy)',
          cobalt: 'var(--blue-cobalt)',
          vibrant: 'var(--blue-vibrant)',
          soft: 'var(--blue-soft)',
          ice: 'var(--blue-ice)',
        },

        // 10% Cyan Accent (Buttons, Active Highlights)
        accent: {
          DEFAULT: 'var(--accent)',
          hover: 'var(--accent-hover)',
          subtle: 'var(--accent-subtle)',
          foreground: 'var(--accent-foreground)',
        },

        // Semantic Data Colors (Used strictly for econometric/data meaning)
        data: {
          up: 'var(--data-up)',
          'up-subtle': 'var(--data-up-subtle)',
          down: 'var(--data-down)',
          'down-subtle': 'var(--data-down-subtle)',
          warning: 'var(--data-warning)',
          'warning-subtle': 'var(--data-warning-subtle)',
          neutral: 'var(--data-neutral)',
          'ci-band': 'var(--data-ci-band)',
        },
      },
      fontFamily: {
        heading: ['Manrope', 'system-ui', 'sans-serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        card: '12px',
        button: '8px',
        chip: '9999px',
        xl: '12px',
      },
      boxShadow: {
        soft: 'var(--shadow-soft)',
        card: 'var(--shadow-card)',
        elevated: 'var(--shadow-elevated)',
      },
      transitionDuration: {
        DEFAULT: '180ms',
        standard: '180ms',
      },
    },
  },
  plugins: [],
};

export default config;
