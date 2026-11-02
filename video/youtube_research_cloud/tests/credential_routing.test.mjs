import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {resolve,dirname} from 'node:path';
import {SURREAL_ASMR_ID,SURREAL_ASMR_TITLE} from '../src/auth.mjs';

const root=resolve(dirname(fileURLToPath(import.meta.url)),'../../..');
const file=path=>readFileSync(resolve(root,path),'utf8');
const ASMR_PAIR=['YOUTUBE_OAUTH_CLIENT_JSON','YOUTUBE_REFRESH_TOKEN'];
const programs=[
 'video/youtube_research_cloud/tools/audit_asmr_channel.mjs',
 'video/youtube_research_cloud/tools/check_asmr_owner_api.mjs',
 'video/youtube_research_cloud/tools/ensure_water_playlist.mjs'
];
const workflows=[
 '.github/workflows/youtube-asmr-channel-audit.yml',
 '.github/workflows/youtube-asmr-api-verify.yml',
 '.github/workflows/youtube-asmr-water-playlist.yml'
];
test('verified ASMR channel identity is permanently pinned',()=>{
 assert.equal(SURREAL_ASMR_ID,'UC9PFLzcnIYHVGy_svH86jyw');
 assert.equal(SURREAL_ASMR_TITLE,'Surreal ASMR');
 assert.match(file('video/youtube_research_cloud/src/auth.mjs'),/OAuth belongs to a different YouTube channel/);
});
test('all ASMR workflows reuse existing verified GitHub secret names',()=>{
 for(const workflow of workflows){
  const body=file(workflow);
  for(const key of ASMR_PAIR) assert.ok(body.includes('secrets.'+key),workflow+' lost '+key);
  for(const obsolete of ['YOUTUBE_ASMR_REFRESH_TOKEN','YOUTUBE_OAUTH_CLIENT_ID','YOUTUBE_OAUTH_CLIENT_SECRET','YOUTUBE_ASMR_CHANNEL_ID']){
   assert.ok(!body.includes(obsolete),workflow+' silently reintroduced missing '+obsolete);
  }
 }
});
test('each authenticated ASMR script verifies owner identity before reading or writing',()=>{
 const audits=file(programs[0]);
 assert.ok(audits.indexOf('verifySurrealOwner(token)')>=0);
 assert.ok(audits.indexOf('verifySurrealOwner(token)')<audits.indexOf('auditPublicChannel('));
 const probe=file(programs[1]);
 assert.match(probe,/verifySurrealOwner\(token\)/);
 const playlist=file(programs[2]);
 assert.ok(playlist.indexOf('verifySurrealOwner(token)')>=0);
 assert.ok(playlist.indexOf('verifySurrealOwner(token)')<playlist.indexOf('method: "POST"'));
});
test('history upload cannot consume the ASMR token without blocking on wrong owner',()=>{
 const workflow=file('.github/workflows/youtube-upload-direct.yml');
 assert.match(workflow,/YOUTUBE_EXPECTED_CHANNEL_HANDLE:\s*["']?@factsuncoveredstories/);
 assert.ok(workflow.indexOf('identify_legacy_oauth.mjs') < workflow.indexOf('gh release download'));
 const inspector=file('video/youtube_research_cloud/tools/identify_legacy_oauth.mjs');
 assert.match(inspector,/expectedHandle/);
 assert.match(inspector,/BLOCKED: existing OAuth token/);
 const uploader=file('video/history_studio/youtube_direct/upload_to_youtube.py');
 assert.match(uploader,/EXPECTED_HISTORY_HANDLE = "@factsuncoveredstories"/);
 assert.ok(uploader.indexOf('verify_history_upload_owner(youtube)\n    video_id')>=0);
 assert.ok(uploader.indexOf('verify_history_upload_owner(youtube)\n    video_id')<uploader.indexOf('video_id = upload('));
});
test('routing instructions identify existing credentials, not new required API keys',()=>{
 const guide=file('video/youtube_research_cloud/AGENTS.md');
 for(const key of ASMR_PAIR)assert.ok(guide.includes(key));
 assert.match(guide,/no extra API key required/);
 assert.match(file('AGENTS.md'),/video\/youtube_research_cloud\/AGENTS\.md/);
 assert.match(file('video/satisfying_studio/AGENTS.md'),/video\/youtube_research_cloud\/AGENTS\.md/);
});
