/**
 * PackGuard AI - Vanilla JavaScript Frontend Controller
 * Minimal clean design with no hardcoded results and no emoticons.
 * All findings are rendered dynamically from the backend API.
 */

document.addEventListener('DOMContentLoaded', () => {
  // DOM Elements
  const artworkInput = document.getElementById('artworkInput');
  const artworkDropzone = document.getElementById('artworkDropzone');
  const artworkDropContent = document.getElementById('artworkDropContent');
  const artworkPreview = document.getElementById('artworkPreview');
  const artworkThumbImg = document.getElementById('artworkThumbImg');
  const artworkPdfIcon = document.getElementById('artworkPdfIcon');
  const artworkFileName = document.getElementById('artworkFileName');
  const artworkFileMeta = document.getElementById('artworkFileMeta');
  const artworkTypeBadge = document.getElementById('artworkTypeBadge');
  const removeArtworkBtn = document.getElementById('removeArtworkBtn');

  const rulebookInput = document.getElementById('rulebookInput');
  const rulebookDropzone = document.getElementById('rulebookDropzone');
  const rulebookDropContent = document.getElementById('rulebookDropContent');
  const rulebookPreview = document.getElementById('rulebookPreview');
  const rulebookFileName = document.getElementById('rulebookFileName');
  const rulebookFileMeta = document.getElementById('rulebookFileMeta');
  const rulebookFormatText = document.getElementById('rulebookFormatText');
  const rulebookTypeBadge = document.getElementById('rulebookTypeBadge');
  const removeRulebookBtn = document.getElementById('removeRulebookBtn');

  const analyzeBtn = document.getElementById('analyzeBtn');
  const analyzeBtnText = document.getElementById('analyzeBtnText');
  const loadSampleBtn = document.getElementById('loadSampleBtn');
  const viewSampleDataBtn = document.getElementById('viewSampleDataBtn');
  const validationAlert = document.getElementById('validationAlert');
  const validationAlertText = document.getElementById('validationAlertText');
  const closeAlertBtn = document.getElementById('closeAlertBtn');

  const loadingSection = document.getElementById('loadingSection');
  const loadingStatusText = document.getElementById('loadingStatusText');
  const resultsSection = document.getElementById('resultsSection');

  // Visual Audit Card Elements
  const visualAuditCard = document.getElementById('visualAuditCard');
  const auditLogoBadge = document.getElementById('auditLogoBadge');
  const auditDetails = document.getElementById('auditDetails');

  // Stats Elements
  const scoreNumber = document.getElementById('scoreNumber');
  const scoreFillPath = document.getElementById('scoreFillPath');
  const scoreTag = document.getElementById('scoreTag');
  const scoreDesc = document.getElementById('scoreDesc');
  const issueCountEl = document.getElementById('issueCount');
  const reviewCountEl = document.getElementById('reviewCount');
  const passedCountEl = document.getElementById('passedCount');
  const totalChecksCountEl = document.getElementById('totalChecksCount');
  const criticalHighSub = document.getElementById('criticalHighSub');
  const engineMetaSub = document.getElementById('engineMetaSub');

  // Tab & Filter Elements
  const tabCountAll = document.getElementById('tabCountAll');
  const tabCountIssues = document.getElementById('tabCountIssues');
  const tabCountReview = document.getElementById('tabCountReview');
  const tabCountPassed = document.getElementById('tabCountPassed');
  const filterTabs = document.querySelectorAll('.filter-tab');
  const severityFilter = document.getElementById('severityFilter');
  const searchInput = document.getElementById('searchInput');
  const findingsList = document.getElementById('findingsList');

  // Follow-up Box Elements
  const followupForm = document.getElementById('followupForm');
  const followupInput = document.getElementById('followupInput');
  const sendFollowupBtn = document.getElementById('sendFollowupBtn');
  const qaThread = document.getElementById('qaThread');
  const promptChips = document.querySelectorAll('.chip-btn');

  // Sample Modal Elements
  const sampleModal = document.getElementById('sampleModal');
  const closeSampleModalBtn = document.getElementById('closeSampleModalBtn');
  const sampleModalContent = document.getElementById('sampleModalContent');
  const useThisSampleBtn = document.getElementById('useThisSampleBtn');

  const engineStatusBadge = document.getElementById('engineStatusBadge');
  const engineStatusText = document.getElementById('engineStatusText');

  // State (No hardcoded data)
  let selectedArtworkFile = null;
  let selectedRulebookFile = null;
  let isUsingSamplePreset = false;
  let activePresetKey = 'granola';
  let currentAnalysisData = null;
  let activeStatusFilter = 'all';
  let activeSeverityFilter = 'all';
  let searchQuery = '';

  const PRESET_DEFINITIONS = {
    granola: {
      id: "granola",
      artFile: "DancingFish_Granola_Berry_US_Carton.pdf",
      artMeta: "6.2 MB &bull; Packaging Dieline",
      artBadge: "PDF",
      ruleFile: "DancingFish_Granola_Berry_US_Rules.json",
      ruleMeta: "Master Specification",
      ruleBadge: "JSON"
    },
    peakfuel: {
      id: "peakfuel",
      artFile: "PeakFuel_ProteinBar_Wrapper.pdf",
      artMeta: "10 KB &bull; Flow-Wrap Dieline (Defect Proof)",
      artBadge: "PDF",
      ruleFile: "PeakFuel_Spec.json",
      ruleMeta: "Nutrition Bar Spec",
      ruleBadge: "JSON"
    },
    apex_brew: {
      id: "apex_brew",
      artFile: "ApexBrew_ColdBrew_Can_Artwork.pdf",
      artMeta: "14 KB &bull; Beverage Can Dieline",
      artBadge: "PDF",
      ruleFile: "ApexBrew_Spec.json",
      ruleMeta: "RTD Beverage Master Spec",
      ruleBadge: "JSON"
    },
    littlesprout: {
      id: "littlesprout",
      artFile: "LittleSprout_BabyPuree_Pouch.pdf",
      artMeta: "11 KB &bull; Infant Pouch Dieline",
      artBadge: "PDF",
      ruleFile: "LittleSprout_Spec.json",
      ruleMeta: "Infant Nutrition Master Spec",
      ruleBadge: "JSON"
    }
  };

  const MAX_FILE_SIZE = 32 * 1024 * 1024;

  // Initialize status check
  checkBackendStatus();

  // Setup dropzone listeners
  setupDropzone(artworkDropzone, artworkInput, handleArtworkSelected);
  setupDropzone(rulebookDropzone, rulebookInput, handleRulebookSelected);

  // Preset pill listeners
  document.querySelectorAll('.preset-pill').forEach(pill => {
    pill.addEventListener('click', () => {
      const presetId = pill.dataset.preset || 'granola';
      loadSamplePreset(presetId);
    });
  });

  // File removal handlers
  removeArtworkBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    resetArtworkSelection();
  });

  removeRulebookBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    resetRulebookSelection();
  });

  // Load sample preset handler
  loadSampleBtn.addEventListener('click', () => {
    loadSamplePreset('granola');
  });

  // Sample modal handlers
  viewSampleDataBtn.addEventListener('click', () => {
    openSampleRulesModal();
  });

  closeSampleModalBtn.addEventListener('click', () => {
    sampleModal.classList.add('hidden');
  });

  useThisSampleBtn.addEventListener('click', () => {
    sampleModal.classList.add('hidden');
    loadSamplePreset(activePresetKey || 'granola');
  });

  // Close alert handler
  closeAlertBtn.addEventListener('click', () => {
    validationAlert.classList.add('hidden');
  });

  // Analyze button handler
  analyzeBtn.addEventListener('click', () => {
    executeArtworkAnalysis();
  });

  // Filter tabs handlers
  filterTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      filterTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      activeStatusFilter = tab.getAttribute('data-status');
      filterAndRenderFindings();
    });
  });

  // Severity filter handler
  severityFilter.addEventListener('change', (e) => {
    activeSeverityFilter = e.target.value;
    filterAndRenderFindings();
  });

  // Search input handler
  searchInput.addEventListener('input', (e) => {
    searchQuery = e.target.value.toLowerCase().trim();
    filterAndRenderFindings();
  });

  // Metric cards click-to-filter
  document.querySelectorAll('.metric-card').forEach(card => {
    card.addEventListener('click', () => {
      const filter = card.getAttribute('data-filter');
      activeStatusFilter = filter;
      filterTabs.forEach(t => {
        if (t.getAttribute('data-status') === filter) {
          t.classList.add('active');
        } else {
          t.classList.remove('active');
        }
      });
      filterAndRenderFindings();
    });
  });

  // Prompt chips
  promptChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const query = chip.getAttribute('data-query');
      followupInput.value = query;
      submitFollowupQuestion(query);
    });
  });

  // Follow-up form submit
  followupForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = followupInput.value.trim();
    if (!query) return;
    submitFollowupQuestion(query);
  });

  // Dropzone helper
  function setupDropzone(zone, input, fileHandler) {
    ['dragenter', 'dragover'].forEach(eventName => {
      zone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.add('dragover');
      });
    });

    ['dragleave', 'drop'].forEach(eventName => {
      zone.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
        zone.classList.remove('dragover');
      });
    });

    zone.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        fileHandler(files[0]);
      }
    });

    input.addEventListener('change', () => {
      if (input.files && input.files.length > 0) {
        fileHandler(input.files[0]);
      }
    });
  }

  // Artwork selection handler
  function handleArtworkSelected(file) {
    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      showError(`Artwork file is too large (${formatBytes(file.size)}). Max allowed is 32MB.`);
      return;
    }

    const validExts = ['.png', '.jpg', '.jpeg', '.pdf'];
    const lowerName = file.name.toLowerCase();
    const isValid = validExts.some(ext => lowerName.endsWith(ext));
    if (!isValid) {
      showError('Unsupported artwork format. Please upload PNG, JPG, or PDF.');
      return;
    }

    selectedArtworkFile = file;
    isUsingSamplePreset = false;
    hideError();

    artworkFileName.textContent = file.name;
    artworkFileMeta.textContent = `${formatBytes(file.size)} &bull; ${file.type || 'Document'}`;
    artworkTypeBadge.textContent = getFileExt(file.name).toUpperCase();
    artworkTypeBadge.classList.add('selected');

    artworkDropContent.classList.add('hidden');
    artworkPreview.classList.remove('hidden');

    if (lowerName.endsWith('.pdf')) {
      artworkThumbImg.classList.add('hidden');
      artworkPdfIcon.classList.remove('hidden');
    } else {
      artworkPdfIcon.classList.add('hidden');
      artworkThumbImg.classList.remove('hidden');
      const reader = new FileReader();
      reader.onload = (e) => {
        artworkThumbImg.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
  }

  // Rulebook selection handler
  function handleRulebookSelected(file) {
    if (!file) return;

    if (file.size > MAX_FILE_SIZE) {
      showError(`Rulebook file is too large (${formatBytes(file.size)}). Max allowed is 32MB.`);
      return;
    }

    const validExts = ['.txt', '.json', '.pdf', '.xlsx'];
    const lowerName = file.name.toLowerCase();
    const isValid = validExts.some(ext => lowerName.endsWith(ext));
    if (!isValid) {
      showError('Unsupported rulebook format. Please upload TXT, JSON, or PDF.');
      return;
    }

    selectedRulebookFile = file;
    isUsingSamplePreset = false;
    hideError();

    rulebookFileName.textContent = file.name;
    rulebookFileMeta.textContent = `${formatBytes(file.size)} &bull; Specification`;
    const ext = getFileExt(file.name).toUpperCase();
    rulebookFormatText.textContent = `${ext} RULEBOOK`;
    rulebookTypeBadge.textContent = ext;
    rulebookTypeBadge.classList.add('selected');

    rulebookDropContent.classList.add('hidden');
    rulebookPreview.classList.remove('hidden');
  }

  function resetArtworkSelection() {
    selectedArtworkFile = null;
    isUsingSamplePreset = false;
    document.querySelectorAll('.preset-pill').forEach(p => p.classList.remove('active'));
    artworkInput.value = '';
    artworkDropContent.classList.remove('hidden');
    artworkPreview.classList.add('hidden');
    artworkThumbImg.src = '';
    artworkTypeBadge.textContent = 'Not Selected';
    artworkTypeBadge.classList.remove('selected');
  }

  function resetRulebookSelection() {
    selectedRulebookFile = null;
    isUsingSamplePreset = false;
    document.querySelectorAll('.preset-pill').forEach(p => p.classList.remove('active'));
    rulebookInput.value = '';
    rulebookDropContent.classList.remove('hidden');
    rulebookPreview.classList.add('hidden');
    rulebookTypeBadge.textContent = 'Not Selected';
    rulebookTypeBadge.classList.remove('selected');
  }

  // Load sample preset dynamically from server
  function loadSamplePreset(presetId = 'granola') {
    isUsingSamplePreset = true;
    activePresetKey = presetId;
    selectedArtworkFile = null;
    selectedRulebookFile = null;
    hideError();

    // Highlight active preset button
    document.querySelectorAll('.preset-pill').forEach(pill => {
      pill.classList.toggle('active', pill.dataset.preset === presetId);
    });

    const preset = PRESET_DEFINITIONS[presetId] || PRESET_DEFINITIONS['granola'];

    artworkFileName.textContent = preset.artFile;
    artworkFileMeta.innerHTML = preset.artMeta;
    artworkTypeBadge.textContent = preset.artBadge;
    artworkTypeBadge.classList.add('selected');
    artworkThumbImg.classList.add('hidden');
    artworkPdfIcon.classList.remove('hidden');
    artworkDropContent.classList.add('hidden');
    artworkPreview.classList.remove('hidden');

    rulebookFileName.textContent = preset.ruleFile;
    rulebookFileMeta.innerHTML = preset.ruleMeta;
    rulebookFormatText.textContent = preset.ruleBadge + " SPEC";
    rulebookTypeBadge.textContent = preset.ruleBadge;
    rulebookTypeBadge.classList.add('selected');
    rulebookDropContent.classList.add('hidden');
    rulebookPreview.classList.remove('hidden');

    // Trigger analysis
    executeArtworkAnalysis();
  }

  // View sample rules modal
  async function openSampleRulesModal() {
    sampleModal.classList.remove('hidden');
    const targetPreset = activePresetKey || 'granola';
    sampleModalContent.textContent = `Loading specification for ${targetPreset}...`;
    try {
      const res = await fetch(`/api/sample?preset=${encodeURIComponent(targetPreset)}`);
      if (res.ok) {
        const data = await res.json();
        sampleModalContent.textContent = JSON.stringify(data.sample_rulebook, null, 2);
      } else {
        sampleModalContent.textContent = "Sample rules ready. Click 'Load This Sample Rulebook' to proceed.";
      }
    } catch (e) {
      sampleModalContent.textContent = "Sample rules ready.";
    }
  }

  // Execute artwork analysis via API
  async function executeArtworkAnalysis() {
    if (!isUsingSamplePreset && (!selectedArtworkFile || !selectedRulebookFile)) {
      showError("Please provide both a packaging artwork file (PNG, JPG, PDF) and a rulebook (TXT, JSON, PDF), or click 'Load Sample Files'.");
      return;
    }

    hideError();
    startLoadingAnimation();

    const formData = new FormData();
    if (isUsingSamplePreset) {
      formData.append('use_sample', 'true');
      formData.append('preset', activePresetKey || 'granola');
    } else {
      if (selectedArtworkFile) formData.append('artwork', selectedArtworkFile);
      if (selectedRulebookFile) formData.append('rulebook', selectedRulebookFile);
    }

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (!response.ok || !result.success) {
        const msg = result.error || "Analysis failed. Please check server logs.";
        showError(msg);
        stopLoadingAnimation();
        return;
      }

      currentAnalysisData = result.data;
      stopLoadingAnimation();
      renderAnalysisResults(currentAnalysisData);

      resultsSection.scrollIntoView({ behavior: 'smooth' });

    } catch (err) {
      console.error("Analysis network error:", err);
      showError(`Analysis failed: ${err.message || 'Network connection error'}. Make sure the server is running.`);
      stopLoadingAnimation();
    }
  }

  // Loading animation
  let loadingInterval = null;
  function startLoadingAnimation() {
    loadingSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
    analyzeBtn.disabled = true;
    analyzeBtnText.textContent = "Analyzing Artwork...";

    const stepMsgs = [
      "Extracting text and dieline layers...",
      "Parsing rulebook specifications...",
      "Executing deterministic validation checks...",
      "Executing Stage 1: Multimodal Vision Inspection (Logos, Panels, Layout)...",
      "Executing Stage 2: Regulatory Reasoning & Rule Reconciliation..."
    ];

    let currentStep = 1;
    updateStepUI(1, stepMsgs[0]);

    if (loadingInterval) clearInterval(loadingInterval);
    loadingInterval = setInterval(() => {
      currentStep++;
      if (currentStep <= 5) {
        updateStepUI(currentStep, stepMsgs[currentStep - 1]);
      }
    }, 850);
  }

  function updateStepUI(stepNum, msg) {
    loadingStatusText.textContent = msg;
    for (let i = 1; i <= 5; i++) {
      const el = document.getElementById(`pStep${i}`);
      if (!el) continue;
      if (i < stepNum) {
        el.className = 'step-item done';
      } else if (i === stepNum) {
        el.className = 'step-item active';
      } else {
        el.className = 'step-item';
      }
    }
  }

  function stopLoadingAnimation() {
    if (loadingInterval) {
      clearInterval(loadingInterval);
      loadingInterval = null;
    }
    loadingSection.classList.add('hidden');
    analyzeBtn.disabled = false;
    analyzeBtnText.textContent = "Analyze Artwork";
  }

  // Render analysis results dynamically from API response
  function renderAnalysisResults(data) {
    if (!data) return;
    currentAnalysisData = data;
    resultsSection.classList.remove('hidden');

    const summary = data.summary || {};
    const findings = data.findings || [];

    const issues = findings.filter(f => f.status === 'ISSUE');
    const needsReview = findings.filter(f => f.status === 'NEEDS_REVIEW');
    const passed = findings.filter(f => f.status === 'PASSED');

    const criticalCount = findings.filter(f => f.severity === 'CRITICAL' && f.status === 'ISSUE').length;
    const highCount = findings.filter(f => f.severity === 'HIGH' && f.status === 'ISSUE').length;

    // Update counts
    issueCountEl.textContent = issues.length;
    reviewCountEl.textContent = needsReview.length;
    passedCountEl.textContent = passed.length;
    totalChecksCountEl.textContent = findings.length;

    criticalHighSub.textContent = `${criticalCount} Critical, ${highCount} High`;
    engineMetaSub.textContent = summary.engine || "Dual Engine Verified";

    tabCountAll.textContent = findings.length;
    tabCountIssues.textContent = issues.length;
    tabCountReview.textContent = needsReview.length;
    tabCountPassed.textContent = passed.length;

    // Render Stage 1 Visual Audit Summary if available
    const visualAudit = data.visual_audit || {};
    const logos = visualAudit.detected_logos_and_badges || [];
    const panels = visualAudit.detected_panels || [];

    if (logos.length > 0 || panels.length > 0) {
      visualAuditCard.classList.remove('hidden');
      auditLogoBadge.textContent = `${logos.length} Badges / Logos Identified`;

      let chipsHtml = '';
      panels.forEach(p => {
        const name = p.panel_name || p;
        chipsHtml += `<div class="audit-chip">Panel: <strong>${escapeHtml(name)}</strong></div>`;
      });
      logos.forEach(l => {
        const name = l.name || l;
        const loc = l.location ? ` (${l.location})` : '';
        chipsHtml += `<div class="audit-chip">Badge: <strong>${escapeHtml(name)}</strong>${escapeHtml(loc)}</div>`;
      });
      if (visualAudit.barcode_visual_assessment) {
        chipsHtml += `<div class="audit-chip">Barcode: <strong>${escapeHtml(visualAudit.barcode_visual_assessment)}</strong></div>`;
      }
      auditDetails.innerHTML = chipsHtml;
    } else {
      visualAuditCard.classList.add('hidden');
    }

    // Score
    const score = summary.compliance_score !== undefined ? summary.compliance_score : 100;
    scoreNumber.textContent = `${score}%`;
    scoreFillPath.setAttribute('stroke-dasharray', `${score}, 100`);

    if (score >= 90) {
      scoreFillPath.style.stroke = '#16a34a';
      scoreTag.textContent = 'Ready for Release';
      scoreTag.style.color = '#16a34a';
      scoreDesc.textContent = 'Artwork meets mandatory specifications and guidelines.';
    } else if (score >= 70) {
      scoreFillPath.style.stroke = '#d97706';
      scoreTag.textContent = 'Action Required';
      scoreTag.style.color = '#d97706';
      scoreDesc.textContent = 'Discrepancies identified. Review and correct prior to release.';
    } else {
      scoreFillPath.style.stroke = '#dc2626';
      scoreTag.textContent = 'Major Discrepancies';
      scoreTag.style.color = '#dc2626';
      scoreDesc.textContent = 'Mandatory specification violations detected.';
    }

    filterAndRenderFindings();
  }

  // Filter and render findings
  function filterAndRenderFindings() {
    if (!currentAnalysisData || !currentAnalysisData.findings) return;

    let items = currentAnalysisData.findings;

    if (activeStatusFilter === 'issue') {
      items = items.filter(f => f.status === 'ISSUE');
    } else if (activeStatusFilter === 'needs_review') {
      items = items.filter(f => f.status === 'NEEDS_REVIEW');
    } else if (activeStatusFilter === 'passed') {
      items = items.filter(f => f.status === 'PASSED');
    }

    if (activeSeverityFilter !== 'all') {
      items = items.filter(f => f.severity === activeSeverityFilter);
    }

    if (searchQuery) {
      items = items.filter(f => {
        const text = `${f.title} ${f.applicable_rule} ${f.artwork_evidence} ${f.expected_value} ${f.explanation} ${f.recommendation}`.toLowerCase();
        return text.includes(searchQuery);
      });
    }

    if (items.length === 0) {
      findingsList.innerHTML = `
        <div class="empty-findings card">
          <p>No findings match your current filter criteria.</p>
        </div>
      `;
      return;
    }

    findingsList.innerHTML = items.map(item => createFindingCardHtml(item)).join('');
  }

  // Render a finding card
  function createFindingCardHtml(item) {
    const sev = (item.severity || 'INFO').toUpperCase();
    const status = (item.status || 'ISSUE').toUpperCase();
    const isConfirmed = item.is_confirmed !== undefined ? item.is_confirmed : (status === 'ISSUE');

    let badgeClass = 'badge-info';
    if (status === 'PASSED') badgeClass = 'badge-passed';
    else if (sev === 'CRITICAL') badgeClass = 'badge-critical';
    else if (sev === 'HIGH') badgeClass = 'badge-high';
    else if (sev === 'MEDIUM') badgeClass = 'badge-medium';
    else if (sev === 'LOW') badgeClass = 'badge-low';

    let certaintyBadge = '';
    if (status === 'PASSED') {
      certaintyBadge = `<span class="badge badge-certainty-verified">Passed</span>`;
    } else if (isConfirmed) {
      certaintyBadge = `<span class="badge badge-certainty-confirmed">Confirmed Issue</span>`;
    } else {
      certaintyBadge = `<span class="badge badge-certainty-review">Needs Review</span>`;
    }

    return `
      <div class="finding-card severity-${sev} status-${status}">
        <div class="finding-head">
          <div>
            <div class="finding-badges">
              <span class="badge ${badgeClass}">${sev}</span>
              ${certaintyBadge}
              ${item.id ? `<span class="applicable-rule">[${item.id}]</span>` : ''}
            </div>
            <h4 class="finding-title" style="margin-top: 0.35rem;">${escapeHtml(item.title)}</h4>
            <div class="applicable-rule">
              <span>${escapeHtml(item.applicable_rule || 'Packaging Standard')}</span>
            </div>
          </div>
        </div>

        <div class="comparison-grid">
          <div class="cmp-col evidence">
            <div class="cmp-label">Artwork Evidence</div>
            <div class="cmp-val">${escapeHtml(item.artwork_evidence || 'N/A')}</div>
          </div>

          <div class="cmp-col expected">
            <div class="cmp-label">Expected Value</div>
            <div class="cmp-val">${escapeHtml(item.expected_value || 'N/A')}</div>
          </div>
        </div>

        <p class="finding-explanation">${escapeHtml(item.explanation || '')}</p>

        ${item.recommendation ? `
          <div class="finding-recommendation">
            <span class="rec-label">Recommendation:</span>
            ${escapeHtml(item.recommendation)}
          </div>
        ` : ''}
      </div>
    `;
  }

  // Follow-up question submit
  async function submitFollowupQuestion(query) {
    if (!query) return;

    qaThread.classList.remove('hidden');
    const userBubble = document.createElement('div');
    userBubble.className = 'qa-bubble user';
    userBubble.textContent = query;
    qaThread.appendChild(userBubble);

    const assistantBubble = document.createElement('div');
    assistantBubble.className = 'qa-bubble assistant';
    assistantBubble.textContent = 'Consulting analysis context...';
    qaThread.appendChild(assistantBubble);
    qaThread.scrollTop = qaThread.scrollHeight;

    followupInput.value = '';
    sendFollowupBtn.disabled = true;

    try {
      const response = await fetch('/api/followup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: query,
          context: currentAnalysisData
        })
      });

      const res = await response.json();
      if (response.ok && res.success) {
        assistantBubble.innerHTML = formatAssistantAnswer(res.answer);
      } else {
        assistantBubble.innerHTML = `<span style="color: #b91c1c;">${escapeHtml(res.error || 'Unable to generate answer at this time.')}</span>`;
      }
    } catch (e) {
      assistantBubble.innerHTML = `<span style="color: #b91c1c;">Connection error: ${escapeHtml(e.message)}</span>`;
    } finally {
      sendFollowupBtn.disabled = false;
      qaThread.scrollTop = qaThread.scrollHeight;
    }
  }

  function formatAssistantAnswer(text) {
    if (!text) return '';
    return escapeHtml(text)
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n\n/g, '<br><br>')
      .replace(/\n- /g, '<br>&bull; ')
      .replace(/\n\d+\. /g, '<br>&bull; ');
  }

  // Status check
  async function checkBackendStatus() {
    try {
      const res = await fetch('/api/status');
      if (res.ok) {
        const data = await res.json();
        if (data.gemini_configured) {
          engineStatusText.textContent = "GEMINI API KEY LOADED";
        } else {
          engineStatusText.textContent = "API KEY UNAVAILABLE PLEASE CHECK YOUR ENV ANSWER RETURNED ARE CACHED AND CAN BE INACCURATE.";
        }
      }
    } catch (e) {
      console.warn("Status check error:", e);
    }
  }

  function showError(msg) {
    validationAlertText.textContent = msg;
    validationAlert.classList.remove('hidden');
  }

  function hideError() {
    validationAlert.classList.add('hidden');
  }

  function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  function getFileExt(filename) {
    const parts = filename.split('.');
    return parts.length > 1 ? parts.pop() : '';
  }

  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
});
