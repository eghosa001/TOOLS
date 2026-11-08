// Read-only identity check for previously configured direct-upload OAuth credentials.
// It neither uploads a video nor changes any channel setting.
const err=msg=>{console.error('::error::'+msg);process.exitCode=1};
const json=process.env.YOUTUBE_OAUTH_CLIENT_JSON;
const refreshToken=process.env.YOUTUBE_REFRESH_TOKEN;
if(!json||!refreshToken) {err('Legacy upload OAuth credentials are missing.');}
else {
 try {
  const raw=JSON.parse(json);
  const c=raw.installed||raw.web||raw;
  if(!c.client_id||!c.client_secret)throw Error('OAuth client JSON lacks client ID or secret.');
  const p=await fetch('https://oauth2.googleapis.com/token',{
   method:'POST',headers:{'content-type':'application/x-www-form-urlencoded'},
   body:new URLSearchParams({
    client_id:c.client_id,client_secret:c.client_secret,
    refresh_token:refreshToken,grant_type:'refresh_token'
   }),signal:AbortSignal.timeout(12000)
  });
  if(!p.ok) throw Error('Existing OAuth token cannot refresh (HTTP '+p.status+').');
  const token=await p.json();
  if(!token.access_token)throw Error('Google returned no access token.');
  console.log('LEGACY_OAUTH_REFRESH: successful.');
  const declared=String(token.scope||'').split(/\s+/).filter(Boolean);
  console.log('OAUTH_SCOPES: '+(declared.length?declared.map(x=>x.split('/').pop()).join(', '):'not provided by Google'));
  const u=new URL('https://www.googleapis.com/youtube/v3/channels');
  u.searchParams.set('part','id,snippet');
  u.searchParams.set('mine','true');
  const r=await fetch(u,{
   headers:{authorization:'Bearer '+token.access_token},
   signal:AbortSignal.timeout(12000)
  });
  if(r.status===401||r.status===403) {
    throw Error('Legacy token refreshed but cannot read channels.mine (HTTP '+r.status+'). Current authorization may be upload-only; channel identity remains unverified. No writes attempted.');
  }
  if(!r.ok)throw Error('YouTube channels.mine read failed (HTTP '+r.status+').');
  const data=await r.json();
  if(!data.items?.length)throw Error('No channel identity returned. Token may not be linked to a YouTube channel.');
  const expectedChannelId=process.env.MYTHVEIL_CHANNEL_ID?.trim();
  if(!expectedChannelId || !/^UC[A-Za-z0-9_-]{22}$/.test(expectedChannelId)) {
    throw Error('BLOCKED: canonical MYTHVEIL_CHANNEL_ID variable is missing or malformed.');
  }
  if(!data.items.some(item=>item.id===expectedChannelId)) {
    throw Error('BLOCKED: OAuth token belongs to another YouTube channel. Single canonical channel is Mythveil Audiobooks (formerly Facts Uncovered).');
  }
  // Name and handle may be stale after rebranding; immutable ID is authoritative.
  const expectedHandle=undefined;
  if(expectedHandle && !data.items.some(item=>String(item.snippet?.customUrl||'').toLowerCase()===expectedHandle)){
    throw Error('BLOCKED: existing OAuth token does not belong to expected YouTube channel '+expectedHandle+'. No upload permitted.');
  }
  for(const item of data.items){
    console.log('AUTHORIZED_YOUTUBE_CHANNEL: '+JSON.stringify({
     channelId:item.id, title:item.snippet?.title||'',
     customUrl:item.snippet?.customUrl||null
    }));
  }
  console.log('No media uploaded, playlist changed or metadata modified.');
 } catch(e){err(String(e?.message||e).slice(0,260));}
}
