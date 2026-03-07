/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        surface: {
          50:  '#f8f9fa',
          100: '#f1f3f5',
          200: '#e9ecef',
          700: '#343a40',
          800: '#212529',
          900: '#16181b',
          950: '#0d0f10'
        },
        accent: {
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb'
        }
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Cascadia Code', 'monospace']
      },
      typography: (theme) => ({
        invert: {
          css: {
            '--tw-prose-body':         theme('colors.slate[300]'),
            '--tw-prose-headings':     theme('colors.slate[100]'),
            '--tw-prose-lead':         theme('colors.slate[400]'),
            '--tw-prose-links':        theme('colors.blue[400]'),
            '--tw-prose-bold':         theme('colors.slate[100]'),
            '--tw-prose-counters':     theme('colors.slate[400]'),
            '--tw-prose-bullets':      theme('colors.slate[500]'),
            '--tw-prose-hr':           theme('colors.slate[700]'),
            '--tw-prose-quotes':       theme('colors.slate[300]'),
            '--tw-prose-quote-borders':theme('colors.slate[600]'),
            '--tw-prose-captions':     theme('colors.slate[400]'),
            '--tw-prose-code':         theme('colors.sky[300]'),
            '--tw-prose-pre-code':     theme('colors.slate[300]'),
            '--tw-prose-pre-bg':       '#1e293b',
            '--tw-prose-th-borders':   theme('colors.slate[600]'),
            '--tw-prose-td-borders':   theme('colors.slate[700]')
          }
        }
      })
    }
  },
  plugins: [
    // @tailwindcss/typography is added for prose classes used in MarkdownRenderer
    // Install: npm install -D @tailwindcss/typography
    require('@tailwindcss/typography')
  ]
};
