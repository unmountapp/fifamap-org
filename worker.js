/**
 * FIFAMap.org — Cloudflare Worker Proxy for OpenAI API
 * =====================================================
 * Keeps the OpenAI API key server-side (secure).
 * Streams responses back to the frontend.
 * Free tier: 100,000 requests/day.
 *
 * SETUP:
 * 1. Go to https://dash.cloudflare.com → Workers & Pages → Create
 * 2. Name it "fifamap-ai" (or anything you like)
 * 3. Paste this entire file as the worker code
 * 4. Go to Settings → Variables → add:
 *      OPENAI_API_KEY = sk-your-key-here  (encrypt it)
 * 5. Deploy — you'll get a URL like: https://fifamap-ai.your-subdomain.workers.dev
 * 6. Put that URL in index.html as WORKER_URL
 *
 * OPTIONAL: Add a custom domain in the worker's settings for a cleaner URL.
 */

const ALLOWED_ORIGINS = [
  'https://fifamap.org',
  'https://www.fifamap.org',
  'http://localhost',        // for local dev
  'http://127.0.0.1',
];

// Simple in-memory rate limiter (per-IP, resets on worker cold start)
const rateLimitMap = new Map();
const RATE_LIMIT = 30;        // max requests per window
const RATE_WINDOW_MS = 60000; // 1 minute

function isRateLimited(ip) {
  const now = Date.now();
  const entry = rateLimitMap.get(ip);
  if (!entry || now - entry.windowStart > RATE_WINDOW_MS) {
    rateLimitMap.set(ip, { windowStart: now, count: 1 });
    return false;
  }
  entry.count++;
  if (entry.count > RATE_LIMIT) return true;
  return false;
}

function corsHeaders(origin) {
  return {
    'Access-Control-Allow-Origin': origin || ALLOWED_ORIGINS[0],
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';
    const isAllowed = ALLOWED_ORIGINS.some(o => origin.startsWith(o));
    const cors = corsHeaders(isAllowed ? origin : ALLOWED_ORIGINS[0]);

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: cors });
    }

    // Only POST allowed
    if (request.method !== 'POST') {
      return new Response(JSON.stringify({ error: 'Method not allowed' }), {
        status: 405,
        headers: { ...cors, 'Content-Type': 'application/json' },
      });
    }

    // Origin check
    if (!isAllowed) {
      return new Response(JSON.stringify({ error: 'Origin not allowed' }), {
        status: 403,
        headers: { ...cors, 'Content-Type': 'application/json' },
      });
    }

    // Rate limiting
    const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
    if (isRateLimited(clientIP)) {
      return new Response(JSON.stringify({ error: 'Rate limited. Please wait a moment.' }), {
        status: 429,
        headers: { ...cors, 'Content-Type': 'application/json' },
      });
    }

    // Check for API key
    const apiKey = env.OPENAI_API_KEY;
    if (!apiKey) {
      return new Response(JSON.stringify({ error: 'API key not configured on server' }), {
        status: 500,
        headers: { ...cors, 'Content-Type': 'application/json' },
      });
    }

    try {
      // Parse the incoming request body
      const body = await request.json();

      // Safety: enforce model and prevent abuse
      body.model = body.model || 'gpt-4o';
      // Cap max_tokens to prevent huge bills
      body.max_tokens = Math.min(body.max_tokens || 2048, 4096);
      // Ensure web search tool is available
      if (!body.tools) {
        body.tools = [{ type: 'web_search_preview' }];
      }

      // Forward to OpenAI
      const openaiResponse = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify(body),
      });

      // If not streaming, return the JSON directly
      if (!body.stream) {
        const data = await openaiResponse.json();
        return new Response(JSON.stringify(data), {
          status: openaiResponse.status,
          headers: { ...cors, 'Content-Type': 'application/json' },
        });
      }

      // Streaming: pipe the response through
      if (!openaiResponse.ok) {
        const errText = await openaiResponse.text();
        return new Response(errText, {
          status: openaiResponse.status,
          headers: { ...cors, 'Content-Type': 'application/json' },
        });
      }

      // Create a TransformStream to pass through the SSE data
      const { readable, writable } = new TransformStream();
      openaiResponse.body.pipeTo(writable);

      return new Response(readable, {
        status: 200,
        headers: {
          ...cors,
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });

    } catch (err) {
      return new Response(JSON.stringify({ error: 'Proxy error: ' + err.message }), {
        status: 500,
        headers: { ...cors, 'Content-Type': 'application/json' },
      });
    }
  },
};
