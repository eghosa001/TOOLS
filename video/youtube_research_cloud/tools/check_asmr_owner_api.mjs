// Reuse already-configured OAuth pair and verify the exact channel via read-only API calls.
import {legacyYouTubeAccessToken,verifySurrealOwner} from '../src/auth.mjs';
try{
 const token=await legacyYouTubeAccessToken();
 const channel=await verifySurrealOwner(token);
 console.log('ASMR_OWNER_OAUTH_READ_OK: '+channel.title+' ['+channel.id+']');
 console.log('Owner identity verified with existing OAuth pair. No channel changes performed.');
}catch(e){console.error('::error::'+String(e?.message||e).slice(0,240));process.exitCode=1}
