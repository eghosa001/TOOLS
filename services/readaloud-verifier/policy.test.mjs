import test from 'node:test';
import assert from 'node:assert/strict';
import { verifySubscriptionPolicy as check } from './policy.mjs';
const id='readaloud_premium', now=Date.parse('2026-10-25T00:00:00Z');
const sample=(state,expiry='2026-11-25T00:00:00Z',product=id) =>
    ({subscriptionState:state,lineItems:[{expiryTime:expiry,productId:product}]});
test('active, grace and paid-through cancelled',()=>{
  for (const state of ['SUBSCRIPTION_STATE_ACTIVE','SUBSCRIPTION_STATE_IN_GRACE_PERIOD','SUBSCRIPTION_STATE_CANCELED'])
    assert.equal(check(sample(state),id,now).verified,true);
});
test('hold, paused, expired and unmatched product reject',()=>{
  for(const state of ['SUBSCRIPTION_STATE_ON_HOLD','SUBSCRIPTION_STATE_PAUSED','SUBSCRIPTION_STATE_EXPIRED'])
    assert.equal(check(sample(state),id,now).verified,false);
  assert.equal(check(sample('SUBSCRIPTION_STATE_ACTIVE','2026-09-01T00:00:00Z'),id,now).verified,false);
  assert.equal(check(sample('SUBSCRIPTION_STATE_ACTIVE',undefined,'other'),id,now).verified,false);
});
test('broken publisher payload rejects',()=>{
  for(const input of [null,{}, {lineItems:null}, {subscriptionState:'SUBSCRIPTION_STATE_ACTIVE'}])
    assert.equal(check(input,id,now).verified,false);
});
