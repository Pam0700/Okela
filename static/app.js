const form = document.getElementById('studioForm');
const submitBtn = document.getElementById('submitBtn');
const progress = document.getElementById('progress');
const result = document.getElementById('result');

document.getElementById('video').addEventListener('change', e => {
  document.getElementById('videoName').textContent = e.target.files[0]?.name || 'MP4, MOV, MKV, AVI, WEBM';
});
document.getElementById('music').addEventListener('change', e => {
  document.getElementById('musicName').textContent = e.target.files[0]?.name || 'MP3, WAV, M4A, AAC';
});

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  submitBtn.disabled = true;
  progress.classList.remove('hidden');
  result.className = 'result hidden';
  const data = new FormData(form);
  for (const name of ['add_subtitles','flip','mute_original']) {
    if (!form.elements[name]?.checked) data.set(name, 'false');
  }
  try {
    const res = await fetch('/process', { method: 'POST', body: data });
    const payload = await res.json();
    if (!payload.ok) throw new Error(payload.error || 'Có lỗi xảy ra.');
    result.className = 'result success';
    result.innerHTML = `<strong>Đã tạo video thành công.</strong><br>
      <a href="${payload.video_url}">Tải video</a>
      ${payload.subtitle_url ? `<a href="${payload.subtitle_url}">Tải file SRT</a>` : ''}`;
  } catch (err) {
    result.className = 'result error';
    result.textContent = err.message;
  } finally {
    progress.classList.add('hidden');
    result.classList.remove('hidden');
    submitBtn.disabled = false;
  }
});
