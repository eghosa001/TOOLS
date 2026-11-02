// Read-only owner OAuth probe. Never prints tokens, OAuth response bodies, or secrets.
// This does not update videos, playlists, end screens, or channel fields.
const REQUIRED_TITLE='Surreal ASMR';
const required=name=>{
 const value=process.env[name]?.trim();
 if(!value)throw Error('Missing GitHub Actions credential or variable: '+name);
 return value;
};
try{
 const clientId=required('YOUTUBE_OAUTH_CLIENT_ID');
 const clientSecret=required('YOUTUBE_OAUTH_CLIENT_SECRET');
 const refreshToken=required('YOUTUBE_ASMR_REFRESH_TOKEN');
 const expectedChannelId=required('YOUTUBE_ASMR_CHANNEL_ID');
 const t=await fetch('https://oauth2.googleapis.com/token',{
   method:'POST',
   headers:{'content-type':'application/x-www-form-urlencoded'},
   body:new URLSearchParams({client_id:clientId,client_secret:clientSecret,refresh_token:refreshToken,grant_type:'refresh_token'}),
   signal:AbortSignal.timeout(12000)
 });
 if(!t.ok)throw Error('OAuth token refresh failed (HTTP '+t.status+'). Check client credentials, refresh token and consent.');
 const response=await t.json();
 if(!response.access_token)throw Error('Google did not return an OAuth access token.');
 const url=new URL('https://www.googleapis.com/youtube/v3/channels');
 url.searchParams.set('part','id,snippet');
 url.searchParams.set('mine','true');
 const ch=await fetch(url,{
  headers:{authorization:'Bearer '+response.access_token},signal:AbortSignal.timeout(12000)
 });
 if(!ch.ok)throw Error('YouTube channels.mine failed (HTTP '+ch.status+'). Check OAuth scope and API access.');
 const data=await ch.json();
 const match=(data.items||[]).find(x=>x.id===expectedChannelId);
 if(!match||match.snippet?.title!==REQUIRED_TITLE)
   throw Error('OAuth identity did not match Surreal ASMR and the configured channel ID. No writes attempted.');
 console.log('ASMR_OWNER_OAUTH_READ_OK: verified Surreal ASMR with channel ID matching repository variable.');
 console.log('This confirms owner token read access, not playlist write scope or permission to change video metadata.');
}catch(e){console.error('::error::'+String(e?.message||e).slice(0,260));process.exitCode=1}
