// Reuse already-configured OAuth pair and verify the exact channel via read-only API calls.
import {legacyYouTubeAccessToken,verifySurrealOwner} from '../src/auth.mjs';
try{
 const token=await legacyYouTubeAccessToken();
 const channel=await verifySurrealOwner(token);
 console.log('ASMR_OWNER_OAUTH_READ_OK: '+channel.title+' ['+channel.id+']');
 console.log('Owner identity verified with existing OAuth pair. No channel changes performed.');
 // Capability probe only: never print, write or save owner analytics in public CI logs.
 // A YouTube Analytics read may require additional Google OAuth scopes.
 const url=new URL('https://youtubeanalytics.googleapis.com/v2/reports');
 url.searchParams.set('ids','channel==MINE');
 url.searchParams.set('startDate','2026-10-31');
 url.searchParams.set('endDate','2026-11-01');
 url.searchParams.set('metrics','views');
 const response=await fetch(url,{headers:{Authorization:'Bearer '+token},signal:AbortSignal.timeout(12000)});
 if(response.ok) console.log('ASMR_ANALYTICS_API: available (results intentionally not logged).');
 else console.log('ASMR_ANALYTICS_API: unavailable (HTTP '+response.status+'); confirm API enablement and OAuth scopes. No analytics data exported.');

}catch(e){console.error('::error::'+String(e?.message||e).slice(0,240));process.exitCode=1}
