/**
 * Image-only Cloudflare -> private Google Drive pilot.
 * No notebooks or local GPUs. This is a PILOT: do not schedule bulk work
 * until testOneImage() has created and verified a real image on Drive.
 *
 * In Apps Script > Project Settings > Script properties set:
 *   CF_ACCOUNT_ID (Cloudflare account ID)
 *   CF_API_TOKEN (token allowed to run Workers AI)
 *
 * Images go into the existing, owner-private Eternal Dao illustration library.
 * Credentials never belong in GitHub, prompts, logs, or Drive files.
 */
const IMAGE_MODEL = '@cf/black-forest-labs/flux-2-klein-4b';
const IMAGE_FOLDER_ID = '1_S2h88iwP5YxpNUWNpUl4gQYxiPsbhIC';
const IMAGE_WIDTH = 1024;
const IMAGE_HEIGHT = 576;

function testOneImage() {
  const prompt = 'One original 2D Chinese manhua illustration, 16:9 composition. A rain-darkened brick courtyard with copper piping, hanging industrial lanterns, weathered workshop tools, dense ink linework, atmospheric cinematic lighting, elegant hand-painted color, clear architecture, no humans, no letters, no watermark, one scene.';
  const result = generateAndSave_('pilot-industrial-courtyard', prompt, 171108);
  Logger.log(JSON.stringify(result));
  return result;
}

/**
 * Optional bulk use only AFTER a successful live pilot and visual review.
 * Place a private SCENE_PROMPTS.json file in the Drive folder:
 * [{"id":"scene-0001","prompt":"A short, scene-specific description","seed":12345}]
 * Runs at most 3 images per invocation to respect Apps Script execution time.
 * Re-run manually to resume: existing name+prompt-hash files are skipped.
 */
function runNextThreeImages() {
  const folder = DriveApp.getFolderById(IMAGE_FOLDER_ID);
  const files = folder.getFilesByName('SCENE_PROMPTS.json');
  if (!files.hasNext()) throw new Error('Missing private SCENE_PROMPTS.json in target Drive folder.');
  const queue = JSON.parse(files.next().getBlob().getDataAsString('UTF-8'));
  if (!Array.isArray(queue) || !queue.length) throw new Error('Scene queue must be a nonempty JSON array.');
  let completed = 0;
  for (const scene of queue) {
    if (completed >= 3) break;
    if (!scene || !/^[a-zA-Z0-9_-]{1,70}$/.test(scene.id || '')) throw new Error('Unsafe or missing scene id');
    const prompt = String(scene.prompt || '').trim();
    if (!prompt || prompt.length > 2048) throw new Error('Prompt is empty or exceeds model limit for ' + scene.id);
    const existing = existingImage_(folder, scene.id, prompt);
    if (existing) continue;
    const seed = Number.isSafeInteger(scene.seed) && scene.seed >= 0 ? scene.seed : 100000 + queue.indexOf(scene);
    generateAndSave_(scene.id, prompt, seed);
    completed += 1;
  }
  Logger.log('New images saved this run: ' + completed);
  return completed;
}

function existingImage_(folder, id, prompt) {
  const prefix = id + '-' + sha16_(prompt);
  for (const ext of ['jpg', 'png']) {
    const iter = folder.getFilesByName(prefix + '.' + ext);
    if (iter.hasNext() && iter.next().getSize() > 12000) return true;
  }
  return false;
}

function generateAndSave_(id, prompt, seed) {
  if (!/^[a-zA-Z0-9_-]{1,70}$/.test(id)) throw new Error('Invalid image id');
  prompt = String(prompt || '').trim();
  if (!prompt || prompt.length > 2048) throw new Error('Prompt is empty or too long');
  const props = PropertiesService.getScriptProperties();
  const accountId = String(props.getProperty('CF_ACCOUNT_ID') || '').trim();
  const token = String(props.getProperty('CF_API_TOKEN') || '').trim();
  if (!accountId || !token) throw new Error('Set CF_ACCOUNT_ID and CF_API_TOKEN in private Script Properties first.');
  const folder = DriveApp.getFolderById(IMAGE_FOLDER_ID);
  if (existingImage_(folder, id, prompt)) return { status: 'already_saved', id: id };

  // FLUX.2 klein requires multipart/form-data, even for text-only prompts.
  const boundary = '----StudioImage' + new Date().getTime();
  const form = multipartText_({ prompt: prompt, width: IMAGE_WIDTH, height: IMAGE_HEIGHT, seed: seed }, boundary);
  const endpoint = 'https://api.cloudflare.com/client/v4/accounts/' +
    encodeURIComponent(accountId) + '/ai/run/' + IMAGE_MODEL;
  const response = UrlFetchApp.fetch(endpoint, {
    method: 'post',
    contentType: 'multipart/form-data; boundary=' + boundary,
    headers: { Authorization: 'Bearer ' + token },
    payload: form,
    muteHttpExceptions: true,
    followRedirects: false
  });
  const status = response.getResponseCode();
  if (status !== 200) {
    // Never put credentials or full private prompts in errors/logs.
    const hint = status === 429 ? 'Rate limited: stop and retry later.' :
      status === 401 || status === 403 ? 'Token lacks image inference access.' :
      status === 402 ? 'Model or account billing access required.' :
      'See Cloudflare Workers AI errors/dashboard.';
    throw new Error('Workers AI failed, HTTP ' + status + '. ' + hint);
  }
  let parsed;
  try { parsed = JSON.parse(response.getContentText()); }
  catch (err) { throw new Error('Workers AI did not return JSON. No file saved.'); }
  const base64 = parsed && parsed.result && parsed.result.image;
  if (!parsed.success || !base64 || typeof base64 !== 'string') {
    throw new Error('Workers AI returned no image. No file saved.');
  }
  const bytes = Utilities.base64Decode(base64);
  if (bytes.length < 12000) throw new Error('Returned image too small. No file saved.');
  const b = i => bytes[i] & 255;
  const isJpeg = b(0) === 255 && b(1) === 216 && b(2) === 255;
  const isPng = b(0) === 137 && b(1) === 80 && b(2) === 78 && b(3) === 71;
  if (!isJpeg && !isPng) throw new Error('Returned bytes are not PNG/JPEG. No file saved.');
  const extension = isPng ? 'png' : 'jpg';
  const filename = id + '-' + sha16_(prompt) + '.' + extension;
  const mime = isPng ? 'image/png' : 'image/jpeg';
  const file = folder.createFile(Utilities.newBlob(bytes, mime, filename));
  if (file.getSize() < 12000) {
    file.setTrashed(true);
    throw new Error('Drive saved an invalid-sized image.');
  }
  file.setDescription('Image-only pilot; model=' + IMAGE_MODEL + '; prompt_sha256=' + sha16_(prompt));
  return { status: 'saved', id: id, filename: filename, bytes: file.getSize(), url: file.getUrl() };
}

function multipartText_(fields, boundary) {
  let out = '';
  for (const [name, value] of Object.entries(fields)) {
    out += '--' + boundary + '\r\n' +
      'Content-Disposition: form-data; name="' + name + '"\r\n\r\n' +
      String(value) + '\r\n';
  }
  return out + '--' + boundary + '--\r\n';
}

function sha16_(input) {
  const digest = Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256, input, Utilities.Charset.UTF_8);
  return digest.map(x => ('0' + ((x + 256) % 256).toString(16)).slice(-2)).join('').slice(0, 16);
}
