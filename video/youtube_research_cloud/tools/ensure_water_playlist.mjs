import {legacyYouTubeAccessToken,verifySurrealOwner,SURREAL_ASMR_ID} from '../src/auth.mjs';
const API = "https://www.googleapis.com/youtube/v3";
const CHANNEL_ID = SURREAL_ASMR_ID;
const VIDEO_IDS = ["YQByazV5lWU", "fn_pI5rHo6c"];
const PLAYLIST_TITLE = "Water & Rain ASMR";
const PLAYLIST_DESCRIPTION = "Gentle streams, waterfalls, raindrops on glass and soft nighttime rain. Relaxing water sounds from Surreal ASMR, with no talking or music.";

const delay = ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function youtube(path, token, { method = "GET", query = {}, body, retryNotFound = 0 } = {}) {
  const url = new URL(API + "/" + path);
  for (const [key, value] of Object.entries(query)) url.searchParams.set(key, String(value));
  for (let attempt=0; ; attempt++) {
    const response = await fetch(url, {
      method,
      headers: {
        authorization: "Bearer " + token,
        ...(body ? { "content-type": "application/json" } : {}),
      },
      ...(body ? { body: JSON.stringify(body) } : {}),
      signal: AbortSignal.timeout(15000),
    });
    const data = await response.json().catch(() => ({}));
    if (response.ok) return data;
    const reason = data?.error?.errors?.[0]?.reason || data?.error?.status || "request_failed";
    if(response.status===404 && reason==="playlistNotFound" && attempt<retryNotFound){
      await delay(1200*(attempt+1));
      continue;
    }
    throw new Error("YouTube " + path + " failed (HTTP " + response.status + ", " + reason + ")");
  }
}

const token = await legacyYouTubeAccessToken();
await verifySurrealOwner(token);
const owned = await youtube("channels", token, { query: { part: "id,snippet,status", mine: "true" } });
const channel = owned.items?.[0];
if (!channel || channel.id !== CHANNEL_ID || channel.snippet?.title !== "Surreal ASMR") {
  throw new Error("OAuth identity check failed. No playlist changes were made.");
}
const sourceVideoList = await youtube("videos", token, { query: {part:"snippet",id:VIDEO_IDS.join(",")} });
const videoOwnerIds = new Map((sourceVideoList.items||[]).map(item=>[item.id,item.snippet?.channelId]));
if (VIDEO_IDS.some(id=>videoOwnerIds.get(id)!==CHANNEL_ID)) {
  throw new Error("Playlist update blocked: a selected video is missing or owned by a different channel.");
}


let playlist;
let pageToken;
do {
  const page = await youtube("playlists", token, {
    query: { part: "id,snippet,status", mine: "true", maxResults: "50", ...(pageToken ? { pageToken } : {}) },
  });
  playlist = page.items?.find(item => item.snippet?.title === PLAYLIST_TITLE);
  pageToken = playlist ? undefined : page.nextPageToken;
} while (pageToken);

if (!playlist) {
  if(process.env.ASMR_REQUIRE_EXISTING_PLAYLIST==="true"){
    throw new Error("Previously created Water & Rain ASMR playlist not found; refusing to create a duplicate.");
  }
  playlist = await youtube("playlists", token, {
    method: "POST",
    query: { part: "snippet,status" },
    body: {
      snippet: { title: PLAYLIST_TITLE, description: PLAYLIST_DESCRIPTION },
      status: { privacyStatus: "public" },
    },
  });
} else if (playlist.status?.privacyStatus !== "public") {
  throw new Error("Existing playlist is not public. Refusing to expose or change its privacy without separate approval.");
}

if (playlist.status?.privacyStatus !== "public") {
  throw new Error("Playlist visibility could not be verified as public; no videos were added.");
}

const current = new Set();
let itemPageToken;
do {
  const page = await youtube("playlistItems", token, {
    query: { part: "snippet,contentDetails", playlistId: playlist.id, maxResults: "50", ...(itemPageToken ? { pageToken: itemPageToken } : {}) },
    retryNotFound: 5,
  });
  for (const item of page.items || []) current.add(item.contentDetails?.videoId);
  itemPageToken = page.nextPageToken;
} while (itemPageToken);

const added = [];
for (const videoId of VIDEO_IDS) {
  if (current.has(videoId)) continue;
  await youtube("playlistItems", token, {
    method: "POST",
    query: { part: "snippet" },
    body: { snippet: { playlistId: playlist.id, resourceId: { kind: "youtube#video", videoId } } },
    retryNotFound: 5,
  });
  added.push(videoId);
}

let confirmed = new Set();
for(let check=0; check<5; check++){
  confirmed = new Set();
  let verifyPage;
  do {
    const page = await youtube("playlistItems", token, {
      query: { part: "contentDetails", playlistId: playlist.id, maxResults: "50", ...(verifyPage ? { pageToken: verifyPage } : {}) },
      retryNotFound: 5,
    });
    for (const item of page.items || []) confirmed.add(item.contentDetails?.videoId);
    verifyPage = page.nextPageToken;
  } while (verifyPage);
  if(VIDEO_IDS.every(id=>confirmed.has(id)))break;
  if(check<4)await delay(1500*(check+1));
}
if (VIDEO_IDS.some(id=>!confirmed.has(id))) {
  throw new Error("Playlist items could not be confirmed by YouTube after changes. Check playlist manually.");
}
console.log("YOUTUBE_ASMR_PLAYLIST_VERIFIED",playlist.id,VIDEO_IDS.join(","));
console.log(JSON.stringify({
  channel: channel.snippet.title,
  playlist: { id: playlist.id, title: PLAYLIST_TITLE, privacy: playlist.status.privacyStatus },
  added,
  alreadyPresent: VIDEO_IDS.filter(id => current.has(id)),
  note: "End-screen elements are not editable through the YouTube Data API.",
}, null, 2));
