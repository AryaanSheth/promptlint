# Deploying to docs.promptlint.dev

## Prerequisites

- Vercel account connected to the `AryaanSheth/promptlint` GitHub repo
- DNS access to `promptlint.dev`

## Steps

### 1. Create Vercel Project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import `AryaanSheth/promptlint`
3. Set **Root Directory** to `docs-site`
4. Framework: **VitePress** (auto-detected via `vercel.json`)
5. Click **Deploy**

### 2. Add Custom Domain

In Vercel → Project Settings → Domains:
- Add `docs.promptlint.dev`

### 3. DNS Record

In your DNS provider, add:

```
Type:  CNAME
Name:  docs
Value: cname.vercel-dns.com
TTL:   3600
```

Or for an apex domain:

```
Type:  A
Name:  docs
Value: 76.76.19.61
```

### 4. Verify

After DNS propagation (up to 24h):
- Visit https://docs.promptlint.dev
- Vercel provides automatic HTTPS

## Continuous Deployment

Vercel automatically redeploys on every push to `main` that changes files under `docs-site/`.

To deploy only on docs changes, add to Vercel project settings:
- **Ignored Build Step:** `git diff --quiet HEAD^ HEAD ./docs-site`

## Local Preview

```bash
cd docs-site
npm install
npm run dev    # dev server at http://localhost:5173
npm run build  # production build
npm run preview  # preview production build
```
