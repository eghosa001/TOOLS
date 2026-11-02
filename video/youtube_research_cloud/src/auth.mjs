// Reuse the OAuth credentials already configured for the confirmed Surreal ASMR owner.
// Server/CI only. No logging of access tokens, refresh tokens or client JSON.
export const SURREAL_ASMR_ID='UC9PFLzcnIYHVGy_svH86jyw';
export const SURREAL_ASMR_TITLE='Surreal ASMR';

export async function legacyYouTubeAccessToken({env=process.env,fetcher=fetch}={}){
 const raw=env.YOUTUBE_OAUTH_CLIENT_JSON?.trim();
 const refresh=env.YOUTUBE_REFRESH_TOKEN?.trim();
 if(!raw||!refresh)throw Error('Missing existing YOUTUBE_OAUTH_CLIENT_JSON or YOUTUBE_REFRESH_TOKEN GitHub Actions secret.');
 let c;
 try {
  const data=JSON.parse(raw);c=data.installed||data.web||data;
  if(!c.client_id||!c.client_secret)throw Error('Incomplete OAuth client');
 } catch {throw Error('Existing OAuth client JSON is invalid.');}
 const response=await fetcher('https://oauth2.googleapis.com/token',{
  method:'POST',headers:{'content-type':'application/x-www-form-urlencoded'},
  body:new URLSearchParams({client_id:c.client_id,client_secret:c.client_secret,refresh_token:refresh,grant_type:'refresh_token'}),
  signal:AbortSignal.timeout(12000)
 });
 if(!response.ok)throw Error('Existing YouTube OAuth token refresh failed (HTTP '+response.status+').');
 const token=await response.json();
 if(!token.access_token)throw Error('Google OAuth returned no access token.');
 return token.access_token;
}
export async function verifySurrealOwner(accessToken,{fetcher=fetch}={}){
 const url='https://www.googleapis.com/youtube/v3/channels?part=id%2Csnippet&mine=true';
 const response=await fetcher(url,{headers:{Authorization:'Bearer '+accessToken},signal:AbortSignal.timeout(12000)});
 if(!response.ok)throw Error('Cannot verify YouTube OAuth owner channel (HTTP '+response.status+').');
 const payload=await response.json();
 const channel=payload.items?.find(item=>item.id===SURREAL_ASMR_ID);
 if(!channel||channel.snippet?.title!==SURREAL_ASMR_TITLE)
  throw Error('OAuth belongs to a different YouTube channel. ASMR operation blocked.');
 return {id:channel.id,title:channel.snippet.title,handle:channel.snippet?.customUrl||null};
}
