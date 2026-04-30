import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'PromptLint',
  description: 'The static analysis tool for LLM prompts — catch cost waste, security risks, and quality issues before they reach production.',

  appearance: 'force-dark',

  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: '/logo.svg' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.googleapis.com' }],
    ['link', { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' }],
    ['link', { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=JetBrains+Mono:ital,wght@0,300;0,400;0,500;0,600;1,300&display=swap' }],
    ['meta', { name: 'theme-color', content: '#00ff88' }],
    ['meta', { property: 'og:type', content: 'website' }],
    ['meta', { property: 'og:locale', content: 'en' }],
    ['meta', { property: 'og:title', content: 'PromptLint — Lint your LLM prompts' }],
    ['meta', { property: 'og:description', content: 'Catch cost waste, security risks, PII leaks, and quality issues in your AI prompts before they reach production. 21 rules, 5 auto-fixes, zero API calls.' }],
    ['meta', { property: 'og:site_name', content: 'PromptLint Docs' }],
  ],

  themeConfig: {
    logo: { src: '/logo.svg', width: 24, height: 24 },

    nav: [
      { text: 'Guide', link: '/guide/getting-started', activeMatch: '/guide/' },
      { text: 'Rules', link: '/rules/', activeMatch: '/rules/' },
      { text: 'Reference', link: '/reference/cli', activeMatch: '/reference/' },
      { text: 'Integrations', link: '/integrations/github-actions', activeMatch: '/integrations/' },
      {
        text: 'v1.4.0',
        items: [
          { text: 'Changelog', link: '/changelog' },
          { text: 'Contributing', link: 'https://github.com/AryaanSheth/promptlint/blob/main/CONTRIBUTING.md' },
        ],
      },
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Introduction',
          items: [
            { text: 'What is PromptLint?', link: '/guide/what-is-promptlint' },
            { text: 'Getting Started', link: '/guide/getting-started' },
            { text: 'Installation', link: '/guide/installation' },
          ],
        },
        {
          text: 'Core Concepts',
          items: [
            { text: 'How It Works', link: '/guide/how-it-works' },
            { text: 'Configuration', link: '/guide/configuration' },
            { text: 'Auto-Fix', link: '/guide/auto-fix' },
          ],
        },
        {
          text: 'Resources',
          items: [
            { text: 'Config Examples', link: '/guide/config-examples' },
            { text: 'Best Practices', link: '/guide/best-practices' },
            { text: 'FAQ', link: '/guide/faq' },
          ],
        },
      ],

      '/rules/': [
        {
          text: 'Rules',
          items: [
            { text: 'Overview', link: '/rules/' },
          ],
        },
        {
          text: '💰 Cost & Tokens',
          items: [
            { text: 'cost', link: '/rules/cost' },
            { text: 'cost-limit', link: '/rules/cost-limit' },
          ],
        },
        {
          text: '🔒 Security',
          items: [
            { text: 'prompt-injection', link: '/rules/prompt-injection' },
            { text: 'jailbreak-pattern', link: '/rules/jailbreak-pattern' },
            { text: 'secret-in-prompt', link: '/rules/secret-in-prompt' },
            { text: 'pii-in-prompt', link: '/rules/pii-in-prompt' },
            { text: 'context-injection-boundary', link: '/rules/context-injection-boundary' },
          ],
        },
        {
          text: '🏗️ Structure',
          items: [
            { text: 'structure-sections', link: '/rules/structure-sections' },
            { text: 'role-clarity', link: '/rules/role-clarity' },
            { text: 'output-format-missing', link: '/rules/output-format-missing' },
            { text: 'output-length-missing', link: '/rules/output-length-missing' },
            { text: 'hallucination-risk', link: '/rules/hallucination-risk' },
          ],
        },
        {
          text: '✨ Quality',
          items: [
            { text: 'clarity-vague-terms', link: '/rules/clarity-vague-terms' },
            { text: 'specificity-examples', link: '/rules/specificity-examples' },
            { text: 'specificity-constraints', link: '/rules/specificity-constraints' },
            { text: 'politeness-bloat', link: '/rules/politeness-bloat' },
            { text: 'verbosity-redundancy', link: '/rules/verbosity-redundancy' },
            { text: 'verbosity-sentence-length', link: '/rules/verbosity-sentence-length' },
            { text: 'actionability-weak-verbs', link: '/rules/actionability-weak-verbs' },
            { text: 'consistency-terminology', link: '/rules/consistency-terminology' },
            { text: 'completeness-edge-cases', link: '/rules/completeness-edge-cases' },
          ],
        },
      ],

      '/reference/': [
        {
          text: 'Reference',
          items: [
            { text: 'CLI Reference', link: '/reference/cli' },
            { text: 'Configuration', link: '/reference/configuration' },
            { text: 'Exit Codes', link: '/reference/exit-codes' },
            { text: 'Output Formats', link: '/reference/output-formats' },
          ],
        },
      ],

      '/integrations/': [
        {
          text: 'Integrations',
          items: [
            { text: 'GitHub Actions', link: '/integrations/github-actions' },
            { text: 'VS Code Extension', link: '/integrations/vscode' },
            { text: 'Pre-commit Hooks', link: '/integrations/pre-commit' },
            { text: 'GitLab CI', link: '/integrations/gitlab-ci' },
            { text: 'Docker', link: '/integrations/docker' },
          ],
        },
      ],
    },

    editLink: {
      pattern: 'https://github.com/AryaanSheth/promptlint/edit/main/docs-site/:path',
      text: 'Edit this page on GitHub',
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/AryaanSheth/promptlint' },
    ],

    search: {
      provider: 'local',
    },

    footer: {
      message: 'Released under the Apache 2.0 License.',
      copyright: 'Copyright © 2024-present Aryaan Sheth',
    },

    outline: {
      level: [2, 3],
    },
  },

  markdown: {
    theme: {
      light: 'min-dark',
      dark: 'min-dark',
    },
    lineNumbers: false,
  },
})
