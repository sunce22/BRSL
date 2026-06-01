// Cloudflare Worker — feedback proxy for RSL Hero Guide
// Secrets: DISCORD_WEBHOOK_URL (wrangler secret put DISCORD_WEBHOOK_URL)
// KV:      RATE_LIMITS namespace (wrangler kv:namespace create "RATE_LIMITS")

const ALLOWED_ORIGINS = new Set([
  'https://www.twitch.tv',
  'https://twitch.tv',
  'http://localhost:8080',
  'http://localhost',
]);

function getAllowOrigin(origin) {
  if (!origin || origin === 'null') return '*'; // OBS Browser Source / local files
  return ALLOWED_ORIGINS.has(origin) ? origin : null;
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('origin') ?? '';

    if (request.method === 'OPTIONS') {
      const allow = getAllowOrigin(origin);
      if (!allow) return new Response(null, { status: 403 });
      return new Response(null, { status: 204, headers: corsHeaders(allow) });
    }

    if (request.method !== 'POST') return jsonRes(405, { error: 'Method not allowed' }, origin);

    // Rate limit: 5 req / IP / 60s
    const ip = request.headers.get('CF-Connecting-IP') ?? 'unknown';
    const rlKey = `rl:${ip}`;
    const count = parseInt((await env.RATE_LIMITS.get(rlKey)) ?? '0', 10);
    if (count >= 5) return jsonRes(429, { error: 'Too many requests, slow down' }, origin);
    await env.RATE_LIMITS.put(rlKey, String(count + 1), { expirationTtl: 60 });

    let body;
    try { body = await request.json(); }
    catch { return jsonRes(400, { error: 'Invalid JSON' }, origin); }

    const { message, source } = body;

    if (!message || typeof message !== 'string' || !message.trim()) {
      return jsonRes(400, { error: 'message required' }, origin);
    }
    if (message.length > 500) {
      return jsonRes(400, { error: 'message too long (max 500)' }, origin);
    }
    if (source !== undefined && typeof source !== 'string') {
      return jsonRes(400, { error: 'source must be a string' }, origin);
    }

    const label = String(source ?? 'Unknown').slice(0, 20);
    const content = `**[${label}]** ${message.trim()}`;

    const res = await fetch(env.DISCORD_WEBHOOK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content }),
    });

    if (!res.ok) return jsonRes(502, { error: 'Discord error' }, origin);
    return jsonRes(200, { ok: true }, origin);
  },
};

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin':  origin,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

function jsonRes(status, body, origin) {
  const allow = getAllowOrigin(origin);
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      ...corsHeaders(allow ?? '*'),
      'Content-Type': 'application/json',
    },
  });
}
