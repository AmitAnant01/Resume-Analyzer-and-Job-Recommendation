const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const analyzeBtn = document.getElementById('analyzeBtn');
const fileInfo = document.getElementById('fileInfo');
const fileName = document.getElementById('fileName');
const clearFile = document.getElementById('clearFile');
const spinner = document.getElementById('spinner');
const errorMsg = document.getElementById('errorMsg');
const results = document.getElementById('results');
const reAnalyzeBtn = document.getElementById('reAnalyzeBtn');

let selectedFile = null;

// Drag & Drop
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', () => { if (fileInput.files[0]) setFile(fileInput.files[0]); });

function setFile(file) {
  selectedFile = file;
  fileName.textContent = file.name;
  fileInfo.classList.remove('hidden');
  analyzeBtn.disabled = false;
  hideError();
}

clearFile.addEventListener('click', () => {
  selectedFile = null;
  fileInput.value = '';
  fileInfo.classList.add('hidden');
  analyzeBtn.disabled = true;
});

reAnalyzeBtn.addEventListener('click', () => {
  results.classList.add('hidden');
  document.getElementById('uploadSection').classList.remove('hidden');
  selectedFile = null;
  fileInput.value = '';
  fileInfo.classList.add('hidden');
  analyzeBtn.disabled = true;
});

analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) return;

  const formData = new FormData();
  formData.append('resume', selectedFile);

  analyzeBtn.classList.add('hidden');
  spinner.classList.remove('hidden');
  hideError();
  results.classList.add('hidden');

  try {
    const res = await fetch('/analyze', { method: 'POST', body: formData });
    const data = await res.json();

    if (!res.ok || data.error) {
      showError(data.error || 'Analysis failed. Please try again.');
      return;
    }

    renderResults(data);
    document.getElementById('uploadSection').classList.add('hidden');
    results.classList.remove('hidden');
    results.scrollIntoView({ behavior: 'smooth' });

  } catch (err) {
    showError('Network error. Make sure the server is running.');
  } finally {
    spinner.classList.add('hidden');
    analyzeBtn.classList.remove('hidden');
  }
});

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.classList.remove('hidden');
}
function hideError() { errorMsg.classList.add('hidden'); }

function renderResults(data) {
  // Profile
  document.getElementById('rName').textContent = data.name || '—';
  document.getElementById('rEmail').textContent = data.email || '—';
  document.getElementById('rPhone').textContent = data.phone || '—';
  document.getElementById('rWords').textContent = data.word_count || '—';

  // Sections
  const sectionsEl = document.getElementById('sectionsCheck');
  sectionsEl.innerHTML = '';
  const sectionNames = { education: 'Education', experience: 'Experience', skills: 'Skills', contact: 'Contact', summary: 'Summary', projects: 'Projects', certifications: 'Certifications' };
  for (const [key, label] of Object.entries(sectionNames)) {
    const pill = document.createElement('span');
    pill.className = `section-pill ${data.sections[key] ? 'found' : 'missing'}`;
    pill.textContent = (data.sections[key] ? '✓ ' : '✗ ') + label;
    sectionsEl.appendChild(pill);
  }

  // Score ring
  const score = data.score;
  const circumference = 314;
  const offset = circumference - (score / 100) * circumference;
  const ring = document.getElementById('ringFill');
  setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);

  // Ring color
  if (score >= 75) ring.style.stroke = '#22c55e';
  else if (score >= 50) ring.style.stroke = '#f59e0b';
  else ring.style.stroke = '#ef4444';

  // Score number animation
  const scoreEl = document.getElementById('scoreNum');
  let cur = 0;
  const interval = setInterval(() => {
    cur += 2;
    if (cur >= score) { cur = score; clearInterval(interval); }
    scoreEl.textContent = cur;
  }, 20);

  // Grade
  const gradeEl = document.getElementById('scoreGrade');
  if (score >= 80) { gradeEl.textContent = 'Excellent'; gradeEl.style.color = '#4ade80'; }
  else if (score >= 65) { gradeEl.textContent = 'Good'; gradeEl.style.color = '#fbbf24'; }
  else if (score >= 45) { gradeEl.textContent = 'Average'; gradeEl.style.color = '#f97316'; }
  else { gradeEl.textContent = 'Needs Work'; gradeEl.style.color = '#f87171'; }

  // Breakdown
  const bdEl = document.getElementById('breakdown');
  bdEl.innerHTML = Object.entries(data.score_breakdown).map(([k, v]) =>
    `<div class="breakdown-row"><span>${k}</span><span>${v}</span></div>`
  ).join('');

  // Skills
  document.getElementById('skillCount').textContent = data.skill_count;
  const skillsEl = document.getElementById('skillsWrap');
  if (data.skills.length) {
    skillsEl.innerHTML = data.skills.map(s =>
      `<span class="skill-tag">${s}</span>`
    ).join('');
  } else {
    skillsEl.innerHTML = '<p style="color:var(--text-muted);font-size:0.88rem">No recognizable skills found. Try a cleaner format.</p>';
  }

  // Tips
  const tipsEl = document.getElementById('tipsList');
  tipsEl.innerHTML = data.suggestions.length
    ? data.suggestions.map(t => `<li>${t}</li>`).join('')
    : '<li>Your resume looks solid! Minor tweaks may still help.</li>';

  // Jobs
  const jobsEl = document.getElementById('jobsGrid');
  if (data.jobs.length) {
    jobsEl.innerHTML = data.jobs.map(job => {
      const pct = job.match_percent;
      const cls = pct >= 70 ? 'match-high' : pct >= 40 ? 'match-mid' : 'match-low';
      const applyBtn = job.link && job.link !== '#'
        ? `<a href="${job.link}" target="_blank" class="apply-btn">Apply Now →</a>`
        : '';
      const realBadge = job.is_real ? `<span class="real-badge">🌐 Live Job</span>` : '';
      return `
        <div class="job-card">
          <div class="job-header">
            <span class="job-title">${job.title}</span>
            <span class="match-badge ${cls}">${pct}% match</span>
          </div>
          <div class="job-company">${job.company} ${realBadge}</div>
          <div class="job-loc">${job.location}</div>
          <div class="job-desc">${job.description}</div>
          <div class="job-matched">
            ${job.matched_skills.map(s => `<span class="matched-tag">${s}</span>`).join('')}
          </div>
          ${applyBtn}
        </div>`;
    }).join('');
  } else {
    jobsEl.innerHTML = '<p style="color:var(--text-muted);font-size:0.88rem">No strong job matches found. Add more technical skills to your resume.</p>';
  }
}