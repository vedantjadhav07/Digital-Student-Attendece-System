/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Slate & Teal Brand Tokens
        brand: {
          deep: '#163B42',
          teal: '#397C78',
          soft: '#B6D2C9',
          warm: '#E9E7DF',
          ink: '#202B2C',
          darkAction: '#79B5A8',
        },
        // Semantic Theme Tokens
        theme: {
          bg: 'var(--color-bg)',
          surface: 'var(--color-surface)',
          border: 'var(--color-border)',
          text: 'var(--color-text)',
          muted: 'var(--color-muted)',
          action: 'var(--color-action)',
          'action-hover': 'var(--color-action-hover)',
          'action-text': 'var(--color-action-text)',
          secondary: 'var(--color-secondary)',
          highlight: 'var(--color-highlight)',
          deep: 'var(--color-deep)',
        },
        // Theme specific helper tokens
        light: {
          bg: '#F7F8F5',
          card: '#FFFFFF',
          surface: '#FFFFFF',
          secondary: '#EFEFEA',
          border: '#E5EAE6',
          text: '#202B2C',
          muted: '#64716E',
          action: '#397C78',
        },
        dark: {
          bg: '#151D1E',
          card: '#202B2C',
          surface: '#202B2C',
          secondary: '#1B2425',
          border: '#344344',
          text: '#E7EEEA',
          muted: '#A0AEAA',
          action: '#79B5A8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      borderRadius: {
        'sm': '4px',
        DEFAULT: '6px',
        'md': '8px',
        'lg': '10px',
        'xl': '12px',
        '2xl': '14px',
      },
      boxShadow: {
        'subtle': '0 1px 2px 0 rgba(22, 59, 66, 0.05)',
        'card': '0 1px 3px 0 rgba(22, 59, 66, 0.08), 0 1px 2px -1px rgba(22, 59, 66, 0.08)',
        'modal': '0 10px 25px -5px rgba(22, 59, 66, 0.15), 0 8px 10px -6px rgba(22, 59, 66, 0.15)',
        'popover': '0 4px 12px 0 rgba(22, 59, 66, 0.12)',
      }
    },
  },
  plugins: [],
}
