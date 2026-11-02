import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const source=readFileSync(resolve(root,'video/youtube_research_cloud/tools/ensure_water_playlist.mjs'),'utf8');
test('playlist refuses mismatched video ownership and nonpublic existing playlist',()=>{
 assert.match(source,/videoOwnerIds\.get\(id\)!==CHANNEL_ID/);
 assert.match(source,/Refusing to expose or change its privacy/);
 assert.doesNotMatch(source,/method:\s*["']PUT["']/);
});
test('playlist verifies actual YouTube playlist contents after each write',()=>{
 assert.match(source,/YOUTUBE_ASMR_PLAYLIST_VERIFIED/);
 assert.match(source,/VIDEO_IDS\.some\(id=>!confirmed\.has\(id\)\)/);
});
test('one-time dispatch manifest authorizes only the verified two ASMR uploads',()=>{
 const m=JSON.parse(readFileSync(resolve(root,'video/youtube_research_cloud/requests/water-playlist-2026-11-02.json'),'utf8'));
 assert.equal(m.channelId,'UC9PFLzcnIYHVGy_svH86jyw');
 assert.deepEqual(m.videoIds,['YQByazV5lWU','fn_pI5rHo6c']);
 assert.equal(m.playlistTitle,'Water & Rain ASMR');
 const workflow=readFileSync(resolve(root,'.github/workflows/youtube-asmr-water-playlist.yml'),'utf8');
 assert.match(workflow,/confirm:/);
 assert.match(workflow,/default: "no"/);
});

test('manual playlist confirmation uses literal YAML yes/no, not parsed booleans',()=>{
 const workflow=readFileSync(resolve(root,'.github/workflows/youtube-asmr-water-playlist.yml'),'utf8');
 assert.match(workflow,/\- "yes"/);
 assert.match(workflow,/\- "no"/);
 assert.match(workflow,/default: "no"/);
});

test('recovery is bounded and cannot create a duplicate playlist',()=>{
  assert.match(source,/ASMR_REQUIRE_EXISTING_PLAYLIST/);
  assert.match(source,/retryNotFound: 5/);
  assert.match(source,/check<5/);
  const workflow=readFileSync(resolve(root,'.github/workflows/youtube-asmr-water-playlist.yml'),'utf8');
  assert.match(workflow,/require_existing:/);
});

test('scheduled public audit remains low-cost, read-only and retains 14-day public snapshots',()=>{
 const workflow=readFileSync(resolve(root,'.github/workflows/youtube-asmr-channel-audit.yml'),'utf8');
 assert.match(workflow,/cron: "17 6 \* \* \*"/);
 assert.match(workflow,/retention-days: 14/);
 assert.match(workflow,/audit_asmr_channel\.mjs/);
 assert.doesNotMatch(workflow,/videos\.update|playlistItems\.insert/);
});
