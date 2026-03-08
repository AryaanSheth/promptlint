# PromptLint Landing Page

Static landing page with waitlist signup and live signup count. **Supabase URL and key live only in a server-side config file** (never in the frontend).

## Setup

1. **Supabase:** In your project → **SQL Editor**, run the contents of `supabase-setup.sql` (creates `signups` table and `get_signup_count()`).

2. **Config (gitignored):** In the `landing/` folder, copy `.env.example` to `.env` (or create a file named `.config`). Add your Supabase values:
   ```bash
   SUPABASE_URL=https://YOUR_PROJECT_REF.supabase.co
   SUPABASE_ANON_KEY=your_publishable_key_here
   ```
   Get these from Supabase → **Settings → API** (Project URL and Publishable key). Do not commit `.env` or `.config`.

3. **Run the server:**
   ```bash
   cd landing && npm install && npm start
   ```
   Open http://localhost:3000 — the page is served by the same server that talks to Supabase, so no keys are exposed in the browser.
