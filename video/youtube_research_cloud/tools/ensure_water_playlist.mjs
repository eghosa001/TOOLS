import {legacyYouTubeAccessToken,verifySurrealOwner,SURREAL_ASMR_ID} from '../src/auth.mjs';
const API = "https://www.googleapis.com/youtube/v3";
const CHANNEL_ID = SURREAL_ASMR_ID;
const VIDEO_IDS = ["YQByazV5lWU", "fn_pI5rHo6c"];
const PLAYLIST_TITLE = "Water & Rain ASMR";

async function youtube(path, token, { method = "GET", query = {}, body } = {}) {
  const url = new URL(API + "/" + path);
  for (const [key, value] of Object.entries(query)) url.searchParams.set(key, String(value));
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
  if (!response.ok) {
    const reason = data?.error?.errors?.[0]?.reason || data?.error?.status || "request_failed";
    throw new Error("YouTube " + path + " failed (HTTP " + response.status + ", " + reason + ")");
  }
  return data;
}

const token = await legacyYouTubeAccessToken();
await verifySurrealOwner(token);
const owned = await youtube("channels", token, { query: { part: "id,snippet,status", mine: "true" } });
const channel = owned.items?.[0];
if (!channel || channel.id !== CHANNEL_ID || channel.snippet?.title !== "Surreal ASMR") {
  throw new Error("OAuth identity check failed. No playlist changes were made.");
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
  playlist = await youtube("playlists", token, {
    method: "POST",
    query: { part: "snippet,status" },
    body: {
      snippet: { title: PLAYLIST_TITLE, description: "Flowing water and rain ambience from Surreal ASMR." },
      status: { privacyStatus: "public" },
    },
  });
} else if (playlist.status?.privacyStatus !== "public") {
  playlist = await youtube("playlists", token, {
    method: "PUT",
    query: { part: "snippet,status" },
    body: {
      id: playlist.id,
      snippet: {
        title: playlist.snippet.title,
        description: playlist.snippet.description || "Flowing water and rain ambience from Surreal ASMR.",
      },
      status: { privacyStatus: "public" },
    },
  });
}

if (playlist.status?.privacyStatus !== "public") {
  throw new Error("Playlist visibility could not be verified as public; no videos were added.");
}

const current = new Set();
let itemPageToken;
do {
  const page = await youtube("playlistItems", token, {
    query: { part: "snippet,contentDetails", playlistId: playlist.id, maxResults: "50", ...(itemPageToken ? { pageToken: itemPageToken } : {}) },
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
  });
  added.push(videoId);
}

console.log(JSON.stringify({
  channel: channel.snippet.title,
  playlist: { id: playlist.id, title: PLAYLIST_TITLE, privacy: playlist.status.privacyStatus },
  added,
  alreadyPresent: VIDEO_IDS.filter(id => current.has(id)),
  note: "End-screen elements are not editable through the YouTube Data API.",
}, null, 2));
