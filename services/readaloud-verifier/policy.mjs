export function verifySubscriptionPolicy(data, productId, now = Date.now()) {
  const allowed = new Set(['SUBSCRIPTION_STATE_ACTIVE',
    'SUBSCRIPTION_STATE_IN_GRACE_PERIOD','SUBSCRIPTION_STATE_CANCELED']);
  const expiry = (Array.isArray(data?.lineItems) ? data.lineItems : [])
    .filter(x => x?.productId === productId)
    .map(x => Date.parse(x?.expiryTime || '')).filter(Number.isFinite)
    .reduce((a,b) => Math.max(a,b), 0);
  return { verified: allowed.has(data?.subscriptionState) && expiry > now,
    productId, expiresAtMillis: expiry };
}
