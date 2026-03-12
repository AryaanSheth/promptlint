require('dotenv').config();
if (!process.env.SUPABASE_URL || !process.env.SUPABASE_ANON_KEY) {
  require('dotenv').config({ path: require('path').join(__dirname, '.config') });
}

const express = require('express');
const path = require('path');
const helmet = require('helmet');
const rateLimit = require('express-rate-limit');
const { Resend } = require('resend');
const { createClient } = require('@supabase/supabase-js');

const app = express();
const PORT = process.env.PORT || 3000;

// Required when behind a proxy (e.g. Vercel) so express-rate-limit can use X-Forwarded-For
app.set('trust proxy', 1);

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_ANON_KEY;
const resendKey = process.env.RESEND_API_KEY;
const fromEmail = process.env.FROM_EMAIL || 'no-reply@promptlint.dev';

if (!supabaseUrl || !supabaseKey) {
  console.error('Missing SUPABASE_URL or SUPABASE_ANON_KEY. Add them to landing/.env or landing/.config (see .env.example).');
  process.exit(1);
}

const sb = createClient(supabaseUrl, supabaseKey);
const resend = resendKey ? new Resend(resendKey) : null;

// CSP disabled because index.html uses inline <script> and <style>.
// Re-enable once those are extracted to separate files.
app.use(helmet({ contentSecurityPolicy: false }));

app.use(express.json({ limit: '2kb' }));

const globalLimiter = rateLimit({
  windowMs: 1 * 60 * 1000,
  max: 300,
  standardHeaders: true,
});
app.use(globalLimiter);

const signupLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: { error: 'Too many signups; try again later.' },
  standardHeaders: true,
});
app.use('/api/signup', signupLimiter);

const readLimiter = rateLimit({
  windowMs: 1 * 60 * 1000,
  max: 60,
  message: { error: 'Too many requests; try again later.' },
  standardHeaders: true,
});
app.use('/api/signup-count', readLimiter);

app.use(express.static(path.join(__dirname), { dotfiles: 'deny' }));

app.get('/api/signup-count', async (req, res) => {
  try {
    const { data } = await sb.rpc('get_signup_count');
    res.json({ count: typeof data === 'number' ? data : 0 });
  } catch (err) {
    console.error('get_signup_count:', err.message);
    res.json({ count: 0 });
  }
});

const EMAIL_MAX_LEN = 254;
const EMAIL_REGEX = /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$/;

app.post('/api/signup', async (req, res) => {
  const raw = req.body?.email;
  const email = typeof raw === 'string' ? raw.trim() : '';
  if (!email || email.length > EMAIL_MAX_LEN || !EMAIL_REGEX.test(email)) {
    return res.status(400).json({ error: 'Invalid email' });
  }
  try {
    const { error } = await sb.from('signups').insert([{ email }]);
    if (error) {
      if (error.code === '23505') return res.status(409).json({ error: 'already_signed_up' });
      console.error('signup insert error:', error.message);
      return res.status(400).json({ error: 'Signup failed' });
    }

    if (resend) {
      resend.emails
        .send({
          from: fromEmail,
          to: email,
          subject: 'You\u2019re on the PromptLint waitlist',
          text: [
            'Thanks for joining the PromptLint waitlist!',
            '',
            'We\u2019ll email you when:',
            '- the VS Code extension is live, and',
            '- the CLI hits v1.',
            '',
            '\u2014 The PromptLint team',
          ].join('\n'),
        })
        .catch((err) => {
          console.error('Resend email error:', err.message);
        });
    }

    const { data: count } = await sb.rpc('get_signup_count');
    res.json({ ok: true, count: count ?? 0 });
  } catch (err) {
    console.error('signup:', err.message);
    res.status(500).json({ error: 'Server error' });
  }
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

app.listen(PORT, () => {
  console.log(`Landing running at http://localhost:${PORT}`);
});
