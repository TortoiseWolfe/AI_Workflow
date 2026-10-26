// Off-camera setup for the demo: make one account that is still waiting on its confirmation
// email, on the local stack only. The anon key is the public demo key from the app's tracked
// local-supabase env file, mounted read-only at /demo-env.
const fs = require('node:fs');

const ADDRESS = 'reader@example.com';

function anonKey() {
  const text = fs.readFileSync('/demo-env', 'utf8');
  const m = text.match(/^NEXT_PUBLIC_SUPABASE_ANON_KEY=(.*)$/m);
  if (!m) throw new Error('no anon key in /demo-env');
  return m[1].trim().replace(/^"|"$/g, '');
}

exports.setup = async (ctx) => {
  // Start from an empty inbox so the on-screen count is exact.
  await fetch('http://localhost:54324/api/v1/messages', { method: 'DELETE' });
  const key = anonKey();
  const res = await fetch('http://localhost:54321/auth/v1/signup', {
    method: 'POST',
    headers: { apikey: key, 'content-type': 'application/json' },
    body: JSON.stringify({
      email: ADDRESS,
      password: 'demo-only-Passw0rd-' + Date.now(),
      gotrue_meta_security: { captcha_token: 'XXXX.DUMMY.TOKEN.XXXX' },
    }),
  });
  ctx.log('signup status ' + res.status);
  if (!res.ok) throw new Error('signup failed ' + res.status + ' ' + (await res.text()).slice(0, 200));
  // Wait for the first confirmation email to land.
  for (let i = 0; i < 20; i++) {
    const r = await (await fetch('http://localhost:54324/api/v1/messages')).json();
    if (r.total >= 1) return;
    await ctx.sleep(500);
  }
  throw new Error('first email never arrived');
};

// Called right after a page load: the cookie banner would sit over the captions.
exports.accept = async (ctx) => {
  const accept = ctx.page.getByRole('button', { name: 'Accept All' });
  if (await accept.isVisible({ timeout: 3000 }).catch(() => false)) await accept.click();
  await ctx.sleep(300);
};

exports.cleanup = async () => {};
