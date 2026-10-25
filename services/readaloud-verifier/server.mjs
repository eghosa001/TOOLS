import http from 'node:http';
import { GoogleAuth } from 'google-auth-library';
import { verifySubscriptionPolicy } from './policy.mjs';

/**
 * Server-only Google Play subscription verification (Android Publisher API v3).
 * GOOGLE_APPLICATION_CREDENTIALS points to a service account accessible only on
 * the server. NEVER put credentials or Google API keys inside the Android app.
 */
const port = Number(process.env.PORT || 3000);
const packageName = process.env.READALOUD_ANDROID_PACKAGE || 'com.eghosa.tools.readaloud';
const productId = 'readaloud_premium';
const auth = new GoogleAuth({
  scopes: ['https://www.googleapis.com/auth/androidpublisher'],
});
const limiter = new Map();
function throttle(address) {
  const now = Date.now(), old = limiter.get(address) || { time: now, count: 0 };
  if (now - old.time > 60_000) { old.time = now; old.count = 0; }
  old.count++;
  limiter.set(address, old);
  if (limiter.size > 10_000) limiter.clear();
  return old.count <= 30;
}

async function verifyPurchase(token) {
  const client = await auth.getClient();
  const url = 'https://androidpublisher.googleapis.com/androidpublisher/v3/applications/' +
    encodeURIComponent(packageName) + '/purchases/subscriptionsv2/tokens/' +
    encodeURIComponent(token);
  const result = await client.request({ url, method: 'GET', timeout: 12000 });
  const data = result.data || {};
  return verifySubscriptionPolicy(data, productId);
}

http.createServer(async (req, res) => {
  res.setHeader('Cache-Control', 'no-store');
  res.setHeader('Content-Type', 'application/json');
  if (req.method !== 'POST' || req.url !== '/verify') {
    res.writeHead(404).end(JSON.stringify({ error: 'Not found' })); return;
  }
  if (!throttle(req.socket.remoteAddress || 'unknown')) {
    res.writeHead(429).end(JSON.stringify({ error: 'Try again later' })); return;
  }
  let raw = '';
  try {
    for await (const chunk of req) {
      raw += chunk;
      if (raw.length > 8192) throw new Error('too_large');
    }
    const data = JSON.parse(raw);
    if (data.packageName !== packageName || data.productId !== productId ||
        typeof data.purchaseToken !== 'string' ||
        !/^[A-Za-z0-9._:-]{20,4096}$/.test(data.purchaseToken)) {
      res.writeHead(400).end(JSON.stringify({ error: 'Bad request' })); return;
    }
    const verdict = await verifyPurchase(data.purchaseToken);
    res.writeHead(200).end(JSON.stringify(verdict));
  } catch (error) {
    const status = error?.message === 'too_large' ? 413 : 503;
    console.error('Play verification failed', error?.response?.status || error?.code || status);
    res.writeHead(status).end(JSON.stringify({ verified: false, productId,
      expiresAtMillis: 0 }));
  }
}).listen(port, '0.0.0.0', () => console.log('ReadAloud verifier ready on', port));
