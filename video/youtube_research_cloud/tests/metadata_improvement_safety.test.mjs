import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {dirname,resolve} from 'node:path';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const file=path=>readFileSync(resolve(root,path),'utf8');
test('one-time ASMR metadata write is limited to known user-owned videos',()=>{
 const m=JSON.parse(file('video/youtube_research_cloud/requests/metadata-improvements-2026-11-02.json'));
 assert.equal(m.channelId,'UC9PFLzcnIYHVGy_svH86jyw');
 assert.equal(m.playlistId,'PLcvQlecwMwmo');
 assert.deepEqual(m.videoIds,['FgUS9hMYEbk','YQByazV5lWU','fn_pI5rHo6c']);
 assert.equal(m.userRequestedWorkNow,true);
});
test('YouTube metadata updater avoids status writes and checks owner and readback',()=>{
 const s=file('video/youtube_research_cloud/tools/apply_asmr_metadata_20261102.mjs');
 assert.match(s,/verifySurrealOwner\(token\)/);
 assert.match(s,/part:'snippet',id:/);
 assert.match(s,/method:'PUT',query:\{part:'snippet'\}/);
 assert.match(s,/readVideos\(\[id\]\)/);
 assert.match(s,/after\.privacyStatus===old\.privacyStatus/);
 assert.match(s,/JSON\.stringify\(after\.tags\)===JSON\.stringify\(old\.tags\)/);
 assert.match(s,/SAND_OLD/);
 assert.match(s,/SAND_NEW/);
 assert.match(s,/part:'snippet,status'/);
});
