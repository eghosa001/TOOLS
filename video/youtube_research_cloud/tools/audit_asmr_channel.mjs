// Read-only GitHub Actions entrypoint; runs only on the verified ASMR handle.
import {mkdir,writeFile,appendFile} from 'node:fs/promises';
import {auditPublicChannel,DEFAULT_ASMR_HANDLE,REQUIRED_CHANNEL_NAME} from '../src/channel.mjs';
import {legacyYouTubeAccessToken,verifySurrealOwner,SURREAL_ASMR_ID} from '../src/auth.mjs';
try{
 const canOAuth=!!process.env.YOUTUBE_OAUTH_CLIENT_JSON && !!process.env.YOUTUBE_REFRESH_TOKEN;
 const token=canOAuth?await legacyYouTubeAccessToken():null;
 if(token)await verifySurrealOwner(token);
 const key=token?null:process.env.YOUTUBE_API_KEY;
 if(!token&&!key)throw Error('No existing owner OAuth pair or YOUTUBE_API_KEY available in GitHub Actions.');
 const out=await auditPublicChannel(DEFAULT_ASMR_HANDLE,{apiKey:key,accessToken:token});
 if(!out.found||out.channel.id!==SURREAL_ASMR_ID||out.channel.title.toLowerCase()!==REQUIRED_CHANNEL_NAME.toLowerCase()){
   throw new Error('Channel identity mismatch: refusing to report or modify another channel.');
 }
 await mkdir('audit-output',{recursive:true});
 await writeFile('audit-output/surreal-asmr-public.json',JSON.stringify(out,null,2)+'\n');
 const rows=out.results.map(v=>`| [${v.title.replace(/\|/g,'\\|')}](${v.url}) | ${v.views??'not available'} | ${v.issues.length?v.issues.join('; '):'No mechanical issue'} |`).join('\n');
 const summary=[
 '# Surreal ASMR — public YouTube API audit','',
 'Channel: '+out.channel.title+' ('+out.channel.id+')',
 'Checked: '+out.checkedAt,
 'API calls: '+out.quotaCalls+' (no expensive search.list)',
 'Authentication: '+(token?'existing owner OAuth':'public API key'),
 '',
 '| Video | Public lifetime views | Metadata check |',
 '|---|---:|---|',
 rows||'| No accessible public uploads | — | — |',
 '',
 '**Limits:** no private retention, watch time, CTR, search terms or subscriber conversions; no video edits made.',
 'The complete JSON is attached as a workflow artifact.'
 ].join('\n');
 console.log(summary);
 if(process.env.GITHUB_STEP_SUMMARY) await appendFile(process.env.GITHUB_STEP_SUMMARY,summary+'\n');
}catch(e){console.error('::error::'+String(e?.message||e).slice(0,250));process.exit(1)}
