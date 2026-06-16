/* ===== Assnani Dental Chatbot — Conversation Engine ===== */

const Chatbot = (() => {
  // --- State ---
  let state = 'WELCOME';
  let symptoms = {
    has_pain: false, pain_location: '', pain_type: '', pain_intensity: 0,
    pain_duration: '', pain_triggers: [], has_swelling: false,
    swelling_severity: '', has_fever: false, difficulty_opening: false,
    has_trauma: false, has_broken_tooth: false, previous_root_canal: false,
    last_visit: '', recent_extraction: false
  };
  let detectionData = null;
  let analysisResult = null;
  let geminiReport = null;
  let uploadedFiles = [];
  let imageDimensions = { width: 0, height: 0 };

  // --- DOM refs ---
  const msgContainer = document.getElementById('messages-container');
  const typingIndicator = document.getElementById('typing-indicator');
  const quickReplies = document.getElementById('quick-replies-area');
  const uploadArea = document.getElementById('upload-area');
  const inputArea = document.getElementById('input-area');
  const userInput = document.getElementById('user-input');
  const btnSend = document.getElementById('btn-send');
  const sidePanel = document.getElementById('side-panel');
  const btnTogglePanel = document.getElementById('btn-toggle-panel');
  const btnClosePanel = document.getElementById('btn-close-panel');
  const reportOverlay = document.getElementById('report-overlay');
  const reportBody = document.getElementById('report-body');
  const uploadDropzone = document.getElementById('upload-dropzone');
  const fileInput = document.getElementById('xray-file-input');
  const uploadPreview = document.getElementById('upload-preview');
  const previewGrid = document.getElementById('upload-preview-grid');
  const btnUploadAdd = document.getElementById('btn-upload-add');
  const btnUploadSubmit = document.getElementById('btn-upload-submit');
  const btnUploadCancel = document.getElementById('btn-upload-cancel');

  // --- Helpers ---
  function scrollToBottom() {
    setTimeout(() => { msgContainer.scrollTop = msgContainer.scrollHeight; }, 50);
  }

  function addMessage(text, type = 'bot', html = false) {
    const msg = document.createElement('div');
    msg.className = `message message-${type}`;
    const avatar = type === 'bot' ? '🤖' : '👤';
    msg.innerHTML = `
      <div class="message-avatar">${avatar}</div>
      <div class="message-bubble">${html ? text : escapeHtml(text)}</div>
    `;
    msgContainer.appendChild(msg);
    scrollToBottom();
  }

  function escapeHtml(t) {
    const d = document.createElement('div'); d.textContent = t; return d.innerHTML;
  }

  function showTyping() { typingIndicator.style.display = 'flex'; scrollToBottom(); }
  function hideTyping() { typingIndicator.style.display = 'none'; }

  function botSay(text, html = false, delay = 800) {
    return new Promise(resolve => {
      showTyping();
      setTimeout(() => { hideTyping(); addMessage(text, 'bot', html); resolve(); }, delay);
    });
  }

  function showQuickReplies(options) {
    quickReplies.innerHTML = '';
    options.forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'quick-reply-btn';
      btn.textContent = typeof opt === 'string' ? opt : opt.label;
      btn.addEventListener('click', () => {
        const val = typeof opt === 'string' ? opt : opt.value;
        addMessage(typeof opt === 'string' ? opt : opt.label, 'user');
        hideQuickReplies();
        handleInput(val);
      });
      quickReplies.appendChild(btn);
    });
    quickReplies.style.display = 'flex';
    scrollToBottom();
  }

  function hideQuickReplies() { quickReplies.style.display = 'none'; quickReplies.innerHTML = ''; }
  function showUpload() { uploadArea.style.display = 'block'; scrollToBottom(); }
  function hideUpload() { uploadArea.style.display = 'none'; uploadPreview.style.display = 'none'; uploadDropzone.style.display = 'flex'; if(previewGrid) previewGrid.innerHTML = ''; }
  function showInput(placeholder) { inputArea.style.display = 'block'; userInput.placeholder = placeholder || 'Type your message...'; userInput.focus(); }
  function hideInput() { inputArea.style.display = 'none'; }

  // --- State Machine ---
  async function transition(nextState, data) {
    state = nextState;
    switch(state) {
      case 'WELCOME':
        await botSay("Hello! 👋 I'm <strong>Assnani AI</strong>, your dental symptom assistant.", true, 600);
        await botSay("I'll ask you a few questions about your dental health to assess your situation and recommend whether an X-ray examination might be needed.", false, 1000);
        await botSay("Let's start — are you currently experiencing any <strong>dental pain</strong>?", true, 800);
        showQuickReplies(['Yes, I have pain', 'No pain']);
        break;

      case 'PAIN_LOCATION':
        symptoms.has_pain = true;
        await botSay("I'm sorry to hear that. Let me help figure out what's going on.", false, 600);
        await botSay("Where exactly do you feel the pain? Please select the area:", false, 800);
        // Render tooth chart
        hideQuickReplies();
        quickReplies.style.display = 'flex';
        ToothChart.render(quickReplies, (key, label) => {
          symptoms.pain_location = key;
          addMessage(label, 'user');
          hideQuickReplies();
          transition('PAIN_TYPE');
        });
        scrollToBottom();
        break;

      case 'PAIN_TYPE':
        await botSay("How would you describe the pain?", false, 600);
        showQuickReplies([
          { label: '⚡ Sharp', value: 'sharp' },
          { label: '😣 Dull / Aching', value: 'dull' },
          { label: '💓 Throbbing', value: 'throbbing' },
          { label: '🧊 Sensitivity (hot/cold)', value: 'sensitivity' }
        ]);
        break;

      case 'PAIN_INTENSITY':
        symptoms.pain_type = data;
        await botSay("On a scale of <strong>1 to 10</strong>, how intense is the pain?", true, 600);
        showQuickReplies(
          [1,2,3,4,5,6,7,8,9,10].map(n => ({
            label: `${n <= 3 ? '😊' : n <= 6 ? '😐' : n <= 8 ? '😣' : '😫'} ${n}`,
            value: String(n)
          }))
        );
        break;

      case 'PAIN_DURATION':
        symptoms.pain_intensity = parseInt(data);
        await botSay("How long have you been experiencing this pain?", false, 600);
        showQuickReplies([
          { label: '📅 Just today', value: 'today' },
          { label: '📅 1-3 days', value: '1-3 days' },
          { label: '📅 3-7 days', value: '3-7 days' },
          { label: '📅 More than a week', value: '1+ week' }
        ]);
        break;

      case 'PAIN_TRIGGERS':
        symptoms.pain_duration = data;
        await botSay("What triggers or worsens the pain? (Select all that apply, then tap <strong>Done</strong>)", true, 600);
        renderMultiSelect([
          { label: '🔥 Hot food/drinks', value: 'hot' },
          { label: '🧊 Cold food/drinks', value: 'cold' },
          { label: '🦷 Biting / Chewing', value: 'biting' },
          { label: '💥 Spontaneous (no trigger)', value: 'spontaneous' },
          { label: '🍬 Sweet foods', value: 'sweet' }
        ], (selected) => {
          symptoms.pain_triggers = selected;
          transition('SWELLING_ASK');
        });
        break;

      case 'NO_PAIN':
        symptoms.has_pain = false;
        await botSay("That's good! Let me ask a few more questions to be thorough.", false, 700);
        transition('SWELLING_ASK');
        break;

      case 'SWELLING_ASK':
        await botSay("Do you have any <strong>swelling</strong> in your mouth, jaw, or face?", true, 700);
        showQuickReplies(['Yes, I have swelling', 'No swelling']);
        break;

      case 'SWELLING_DETAILS':
        symptoms.has_swelling = true;
        await botSay("How severe is the swelling?", false, 600);
        showQuickReplies([
          { label: '🟡 Mild', value: 'mild' },
          { label: '🟠 Moderate', value: 'moderate' },
          { label: '🔴 Severe', value: 'severe' }
        ]);
        break;

      case 'FEVER_ASK':
        symptoms.swelling_severity = data;
        await botSay("Do you have a <strong>fever</strong> or difficulty opening your mouth?", true, 600);
        showQuickReplies([
          { label: '🤒 Yes, fever', value: 'fever' },
          { label: '😮 Difficulty opening mouth', value: 'trismus' },
          { label: '🤒😮 Both', value: 'both' },
          { label: 'Neither', value: 'neither' }
        ]);
        break;

      case 'HISTORY':
        if (data === 'fever') { symptoms.has_fever = true; }
        else if (data === 'trismus') { symptoms.difficulty_opening = true; }
        else if (data === 'both') { symptoms.has_fever = true; symptoms.difficulty_opening = true; }
        await botSay("A few questions about your <strong>dental history</strong>:", true, 700);
        await botSay("When was your last dental visit?", false, 600);
        showQuickReplies([
          { label: '< 6 months ago', value: '< 6 months' },
          { label: '6-12 months ago', value: '6-12 months' },
          { label: 'Over a year ago', value: '1+ year' },
          { label: 'Never / Can\'t remember', value: 'never' }
        ]);
        break;

      case 'HISTORY_TRAUMA':
        symptoms.last_visit = data;
        await botSay("Have you experienced any of the following?", false, 600);
        showQuickReplies([
          { label: '💥 Recent trauma / injury', value: 'trauma' },
          { label: '🔧 Previous root canal (same area)', value: 'root_canal' },
          { label: '💔 Broken / chipped tooth', value: 'broken' },
          { label: 'None of the above', value: 'none' }
        ]);
        break;

      case 'ANALYSIS':
        if (data === 'trauma') symptoms.has_trauma = true;
        else if (data === 'root_canal') symptoms.previous_root_canal = true;
        else if (data === 'broken') symptoms.has_broken_tooth = true;

        await botSay("Thank you for answering all the questions! Let me analyze your symptoms... 🔍", false, 600);
        await performAnalysis();
        break;

      case 'XRAY_ASK':
        await botSay("Would you like to upload a dental <strong>X-ray</strong> for AI analysis? I can correlate your symptoms with the X-ray findings.", true, 800);
        showQuickReplies([
          { label: '📤 Upload X-ray', value: 'upload' },
          { label: '⏭️ Skip — Show report', value: 'skip' }
        ]);
        break;

      case 'XRAY_UPLOAD':
        await botSay("Please upload your dental X-ray image(s) below. You can upload <strong>multiple files</strong> — supported formats: <strong>PNG, JPG, PDF</strong>.", true, 600);
        showUpload();
        break;

      case 'XRAY_ANALYZING': {
        const filesToAnalyze = [...uploadedFiles]; // capture BEFORE hideUpload clears the array
        hideUpload();
        const fileCount = filesToAnalyze.length;
        await botSay(`<span class="loader-ring">Sending ${fileCount} file${fileCount>1?'s':''} to AI detection model... This may take a moment.</span>`, true, 400);
        await analyzeXray(filesToAnalyze);
        break;
      }

      case 'CORRELATION':
        await performCorrelation();
        break;

      case 'REPORT':
        await generateReport();
        break;
    }
  }

  // --- Multi-Select Helper ---
  function renderMultiSelect(options, onDone) {
    quickReplies.innerHTML = '';
    const selected = new Set();
    options.forEach(opt => {
      const btn = document.createElement('button');
      btn.className = 'quick-reply-btn';
      btn.textContent = opt.label;
      btn.addEventListener('click', () => {
        if (selected.has(opt.value)) { selected.delete(opt.value); btn.classList.remove('selected'); }
        else { selected.add(opt.value); btn.classList.add('selected'); }
      });
      quickReplies.appendChild(btn);
    });
    const doneBtn = document.createElement('button');
    doneBtn.className = 'quick-reply-btn';
    doneBtn.style.cssText = 'background:var(--accent);color:var(--bg-primary);font-weight:700;border-color:var(--accent);';
    doneBtn.textContent = '✓ Done';
    doneBtn.addEventListener('click', () => {
      const sel = Array.from(selected);
      addMessage(sel.length ? sel.join(', ') : 'No specific trigger', 'user');
      hideQuickReplies();
      onDone(sel);
    });
    quickReplies.appendChild(doneBtn);
    quickReplies.style.display = 'flex';
    scrollToBottom();
  }

  // --- Input Handler ---
  function handleInput(value) {
    const v = value.toLowerCase().trim();
    switch(state) {
      case 'WELCOME':
        if (v.includes('yes') || v.includes('pain')) transition('PAIN_LOCATION');
        else transition('NO_PAIN');
        break;
      case 'PAIN_TYPE':
        transition('PAIN_INTENSITY', v); break;
      case 'PAIN_INTENSITY':
        transition('PAIN_DURATION', v); break;
      case 'PAIN_DURATION':
        transition('PAIN_TRIGGERS', v); break;
      case 'SWELLING_ASK':
        if (v.includes('yes') || v.includes('swelling')) transition('SWELLING_DETAILS');
        else { symptoms.has_swelling = false; transition('HISTORY'); }
        break;
      case 'SWELLING_DETAILS':
        transition('FEVER_ASK', v); break;
      case 'FEVER_ASK':
        transition('HISTORY', v); break;
      case 'HISTORY':
        transition('HISTORY_TRAUMA', v); break;
      case 'HISTORY_TRAUMA':
        transition('ANALYSIS', v); break;
      case 'XRAY_ASK':
        if (v.includes('upload')) transition('XRAY_UPLOAD');
        else transition('REPORT');
        break;
    }
  }

  // --- API Calls ---
  async function performAnalysis() {
    try {
      const resp = await fetch('/api/analyze-symptoms', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(symptoms)
      });
      analysisResult = await resp.json();

      const { risk_level, risk_emoji, score, recommendation, factors, home_care, xray_recommended } = analysisResult;
      const badge = `<span class="severity-badge severity-${risk_level}">${risk_emoji} ${risk_level.toUpperCase()} RISK</span>`;

      let factorsHtml = factors.slice(0, 5).map(f => `• ${f[0]} (+${f[1]})`).join('<br>');
      await botSay(`<strong>Assessment Result:</strong> ${badge} (Score: ${score})<br><br>${factorsHtml}`, true, 1200);
      await botSay(recommendation, false, 800);

      if (home_care && home_care.length) {
        const tipsHtml = home_care.map(t => `• ${t}`).join('<br>');
        await botSay(`<strong>💡 Home Care Tips:</strong><br>${tipsHtml}`, true, 600);
      }

      if (xray_recommended) {
        transition('XRAY_ASK');
      } else {
        transition('XRAY_ASK'); // Still offer the option
      }
    } catch (err) {
      await botSay("Sorry, there was an error analyzing your symptoms. Please try again.", false, 500);
      console.error(err);
    }
  }

  async function analyzeXray(files) {
    try {
      const formData = new FormData();
      files.forEach(f => formData.append('images', f));

      const resp = await fetch('/api/detect-xray', { method: 'POST', body: formData });
      if (!resp.ok) {
        const errData = await resp.json();
        throw new Error(errData.error || 'Detection failed');
      }
      detectionData = await resp.json();

      if (!detectionData.success) throw new Error('Detection API returned unsuccessful');

      // Aggregate all detections across results
      const allDets = [];
      const allAnnotated = [];
      for (const result of detectionData.results) {
        const dets = result.detections || [];
        allDets.push(...dets);
        const b64 = result.annotated_image_b64 || result.result_image_b64;
        if (b64) allAnnotated.push({ b64, filename: result.filename || '' });
      }

      const total = detectionData.total_detections || allDets.length;

      // Show annotated images in side panel
      if (allAnnotated.length) showSidePanel(allDets, allAnnotated);

      // Summary message
      const counts = {};
      allDets.forEach(d => { const c = d.class_name; counts[c] = (counts[c]||0) + 1; });
      const summaryParts = Object.entries(counts).map(([k,v]) => `<strong>${v}</strong> ${k}${v>1?'s':''}`);
      const summaryText = summaryParts.length
        ? `AI detected <strong>${total}</strong> finding${total>1?'s':''}: ${summaryParts.join(', ')}.`
        : 'No dental conditions were detected in the X-ray.';

      await botSay(`🔍 <strong>X-ray Analysis Complete!</strong><br>${summaryText}`, true, 800);

      if (allDets.length > 0) {
        await botSay("Now let me correlate these findings with your symptoms...", false, 600);
        transition('CORRELATION');
      } else {
        await botSay("No abnormalities detected. Your X-ray appears normal! However, a clinical examination is still recommended.", false, 800);
        transition('REPORT');
      }
    } catch (err) {
      await botSay(`❌ Error analyzing X-ray: ${err.message}. Please try again.`, false, 500);
      transition('XRAY_ASK');
      console.error(err);
    }
  }

  async function performCorrelation() {
    try {
      const allDets = detectionData.results.flatMap(r => r.detections || []);
      const resp = await fetch('/api/correlate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptoms, detections: allDets, image_width: imageDimensions.width, image_height: imageDimensions.height })
      });
      const corrResult = await resp.json();

      if (corrResult.correlations && corrResult.correlations.length) {
        await botSay("<strong>📋 Symptom ↔ X-ray Correlation:</strong>", true, 600);
        for (const corr of corrResult.correlations) {
          const badge = `<span class="severity-badge severity-${corr.severity}">${corr.severity.toUpperCase()}</span>`;
          await botSay(
            `${badge} <strong>${corr.clinical_name}</strong> (${corr.confidence_label})<br>${corr.explanation}<br><em>→ ${corr.urgency}</em>`,
            true, 1000
          );
        }
      }

      if (corrResult.unmatched_symptoms && corrResult.unmatched_symptoms.length) {
        for (const us of corrResult.unmatched_symptoms) {
          await botSay(`ℹ️ ${us}`, false, 600);
        }
      }

      transition('REPORT');
    } catch (err) {
      await botSay("Error correlating findings. Generating report anyway...", false, 500);
      transition('REPORT');
      console.error(err);
    }
  }

  async function generateReport() {
    await botSay("Generating your complete dental assessment report... 📋", false, 800);

    // Get treatment plan if detections exist
    let treatmentPlan = null;
    if (detectionData && detectionData.results) {
      try {
        const resp = await fetch('/api/treatment-plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_response: detectionData })
        });
        treatmentPlan = await resp.json();
      } catch(e) { console.error(e); }
    }

    // Get Gemini AI-generated report if X-ray was uploaded
    if (uploadedFiles.length) {
      try {
        await botSay('<span class="loader-ring">Generating AI clinical report powered by Gemini... This may take a moment.</span>', true, 400);

        const formData = new FormData();
        uploadedFiles.forEach(f => formData.append('images', f));
        const resp = await fetch('/api/ai-report', { method: 'POST', body: formData });
        if (resp.ok) {
          const aiData = await resp.json();
          if (aiData.results) {
            const firstKey = Object.keys(aiData.results)[0];
            if (firstKey) {
              geminiReport = aiData.results[firstKey];
            }
          }
        }

        // Show AI report as a chat message NOW, before "report ready"
        if (geminiReport && geminiReport.report) {
          let classSummaryHtml = '';
          if (geminiReport.by_class) {
            classSummaryHtml = Object.entries(geminiReport.by_class)
              .map(([cls, count]) => `<span class="severity-badge severity-moderate" style="margin:2px 2px 4px;">${cls}: ${count}</span>`)
              .join(' ');
          }

          const reportChatHtml = `
            <div style="font-size:12px;line-height:1.7;max-height:420px;overflow-y:auto;padding-right:4px;">
              <div style="font-weight:700;font-size:13px;color:var(--accent);border-bottom:1px solid var(--border);padding-bottom:6px;margin-bottom:10px;">
                🤖 AI Clinical Report
                <span style="font-size:10px;color:var(--text-muted);font-weight:400;margin-left:6px;">powered by Gemini</span>
              </div>
              ${classSummaryHtml ? `<div style="margin-bottom:10px;display:flex;flex-wrap:wrap;gap:2px;align-items:center;"><strong style="margin-right:6px;font-size:11px;">Detections:</strong>${classSummaryHtml}<span style="color:var(--text-muted);font-size:11px;margin-left:6px;">(${geminiReport.total || 0} total)</span></div>` : ''}
              <div>${geminiReport.report}</div>
            </div>`;

          addMessage(reportChatHtml, 'bot', true);

          // PDF download button as a follow-up bot message
          window._geminiReportHtml = geminiReport.report;
          window._geminiByClass = geminiReport.by_class || {};
          window._geminiTotal = geminiReport.total || 0;
          const pdfBtnHtml = `<button onclick="window._downloadGeminiPDF()" style="
            display:inline-flex;align-items:center;gap:6px;
            padding:8px 16px;border-radius:8px;border:none;cursor:pointer;
            background:var(--accent);color:#fff;font-weight:600;font-size:13px;
            box-shadow:0 2px 8px rgba(0,0,0,.25);transition:opacity .2s;
          " onmouseover="this.style.opacity='.85'" onmouseout="this.style.opacity='1'">
            📥 Download Report as PDF
          </button>`;
          addMessage(pdfBtnHtml, 'bot', true);

          // Also inject PDF button at the bottom of the X-ray side panel
          const existingPanelBtn = document.getElementById('panel-pdf-section');
          if (existingPanelBtn) existingPanelBtn.remove();
          const panelPdfSection = document.createElement('div');
          panelPdfSection.id = 'panel-pdf-section';
          panelPdfSection.style.cssText = 'padding:12px 16px;border-top:1px solid var(--border);flex-shrink:0;';
          panelPdfSection.innerHTML = `
            <div style="font-size:11px;color:var(--text-muted);margin-bottom:8px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;">AI Clinical Report</div>
            <button onclick="window._downloadGeminiPDF()" style="
              width:100%;display:flex;align-items:center;justify-content:center;gap:8px;
              padding:10px 0;border-radius:8px;border:none;cursor:pointer;
              background:var(--accent);color:#fff;font-weight:600;font-size:13px;
              box-shadow:0 2px 8px rgba(0,0,0,.2);transition:opacity .2s;
            " onmouseover="this.style.opacity='.85'" onmouseout="this.style.opacity='1'">
              📥 Download AI Report PDF
            </button>`;
          sidePanel.appendChild(panelPdfSection);

        } else if (geminiReport && geminiReport.error) {
          await botSay(`⚠️ AI report note: ${geminiReport.error}`, false, 400);
        }

      } catch(e) { console.error('Gemini report error:', e); }
    }

    // Build report HTML
    let reportHtml = '';

    // Risk Assessment Section
    if (analysisResult) {
      const badge = `<span class="severity-badge severity-${analysisResult.risk_level}">${analysisResult.risk_emoji} ${analysisResult.risk_level.toUpperCase()}</span>`;
      reportHtml += `
        <div class="report-section">
          <div class="report-section-title">🩺 Risk Assessment</div>
          <div class="report-item">
            Risk Level: ${badge} &nbsp; Score: <strong>${analysisResult.score}</strong><br>
            ${analysisResult.recommendation}
          </div>
        </div>`;
    }

    // Symptoms Summary
    reportHtml += `
      <div class="report-section">
        <div class="report-section-title">📝 Reported Symptoms</div>
        <div class="report-item">
          ${symptoms.has_pain ? `<strong>Pain:</strong> ${symptoms.pain_type} pain in ${symptoms.pain_location}, intensity ${symptoms.pain_intensity}/10, duration: ${symptoms.pain_duration}<br>` : '<strong>Pain:</strong> None reported<br>'}
          ${symptoms.has_swelling ? `<strong>Swelling:</strong> ${symptoms.swelling_severity}${symptoms.has_fever ? ' with fever' : ''}<br>` : '<strong>Swelling:</strong> None<br>'}
          <strong>Last dental visit:</strong> ${symptoms.last_visit || 'Not specified'}
        </div>
      </div>`;

    // Gemini AI Clinical Report (if available)
    if (geminiReport && geminiReport.report) {
      // Convert markdown-style formatting to HTML
      let reportText = geminiReport.report
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/^### (.*$)/gm, '<h4 style="color:var(--accent);margin:10px 0 4px;font-size:13px;">$1</h4>')
        .replace(/^## (.*$)/gm, '<h3 style="color:var(--accent);margin:12px 0 6px;font-size:14px;">$1</h3>')
        .replace(/^# (.*$)/gm, '<h3 style="color:var(--accent);margin:12px 0 6px;font-size:15px;">$1</h3>')
        .replace(/^- (.*$)/gm, '• $1')
        .replace(/\n/g, '<br>');

      let classSummary = '';
      if (geminiReport.by_class) {
        classSummary = Object.entries(geminiReport.by_class)
          .map(([cls, count]) => `<span class="severity-badge severity-moderate" style="margin:2px;">${cls}: ${count}</span>`)
          .join(' ');
      }

      reportHtml += `
        <div class="report-section">
          <div class="report-section-title">🤖 AI Clinical Report <span style="font-size:10px;color:var(--text-muted);text-transform:none;font-weight:400;">powered by Gemini</span></div>
          ${classSummary ? `<div class="report-item" style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;"><strong style="margin-right:8px;">Detections:</strong> ${classSummary} <span style="color:var(--text-muted);font-size:11px;margin-left:8px;">(${geminiReport.total || 0} total)</span></div>` : ''}
          <div class="report-item" style="max-height:400px;overflow-y:auto;">${reportText}</div>
        </div>`;
    }

    // X-ray Findings (rule-based)
    if (treatmentPlan && treatmentPlan.recommendations) {
      let recsHtml = treatmentPlan.recommendations.map(r =>
        `<div class="report-item">
          ${r.icon} <strong>${r.finding}</strong> <span class="severity-badge severity-${r.severity}">${r.severity.toUpperCase()}</span><br>
          ${r.treatment}<br>
          <em>Specialist: ${r.specialist}</em>
        </div>`
      ).join('');
      reportHtml += `
        <div class="report-section">
          <div class="report-section-title">🔬 Detection Findings & Treatment Plan</div>
          ${recsHtml}
        </div>`;

      if (treatmentPlan.specialists && treatmentPlan.specialists.length) {
        reportHtml += `
          <div class="report-section">
            <div class="report-section-title">👨‍⚕️ Recommended Specialists</div>
            <div class="report-item">${treatmentPlan.specialists.map(s => `• ${s}`).join('<br>')}</div>
          </div>`;
      }
    }

    // Home Care
    if (analysisResult && analysisResult.home_care) {
      reportHtml += `
        <div class="report-section">
          <div class="report-section-title">💡 Home Care Advice</div>
          <div class="report-item">${analysisResult.home_care.map(t => `• ${t}`).join('<br>')}</div>
        </div>`;
    }

    reportBody.innerHTML = reportHtml;
    reportOverlay.style.display = 'flex';
    await botSay("Your assessment report is ready! 📋 Review it in the popup window.", false, 400);
  }

  // --- Side Panel ---
  function showSidePanel(detections, annotatedImages) {
    // Render annotated images
    const panelXray = document.getElementById('panel-xray');
    panelXray.innerHTML = '';
    if (annotatedImages && annotatedImages.length) {
      annotatedImages.forEach(({ b64, filename }) => {
        const img = document.createElement('img');
        img.src = `data:image/png;base64,${b64}`;
        img.alt = filename || 'Annotated X-ray';
        panelXray.appendChild(img);
        if (filename) {
          const label = document.createElement('div');
          label.className = 'panel-xray-label';
          label.textContent = filename;
          panelXray.appendChild(label);
        }
      });
    }

    // Render detection cards
    const panelDets = document.getElementById('panel-detections');
    panelDets.innerHTML = detections.map(d => `
      <div class="detection-card">
        <div class="detection-card-header">
          <span class="detection-card-class">${d.class_name}</span>
          <span class="detection-card-conf">${(d.confidence*100).toFixed(1)}%</span>
        </div>
        <div class="detection-card-detail">Size: ${d.width}×${d.height}px &bull; Position: (${d.x}, ${d.y})</div>
      </div>
    `).join('');
    sidePanel.style.display = 'flex';
    btnTogglePanel.style.display = 'flex';
  }

  // --- PDF Download ---
  window._downloadGeminiPDF = function() {
    const reportHtml = window._geminiReportHtml || '';
    const byClass = window._geminiByClass || {};
    const total = window._geminiTotal || 0;

    const classBadges = Object.entries(byClass)
      .map(([cls, count]) => `<span style="display:inline-block;padding:2px 8px;border-radius:12px;border:1px solid #0d9488;color:#0d9488;font-size:11px;font-weight:600;margin:2px;">${cls}: ${count}</span>`)
      .join(' ');

    const printWin = window.open('', '_blank', 'width=850,height=1000');
    if (!printWin) { alert('Please allow popups to download the PDF.'); return; }

    printWin.document.write(`<!DOCTYPE html><html><head>
      <meta charset="utf-8">
      <title>AI Clinical Report — Assnani Dental</title>
      <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
      <style>
        *{margin:0;padding:0;box-sizing:border-box}
        body{font-family:'Inter',sans-serif;padding:40px;color:#1e293b;font-size:13px;line-height:1.7;background:#fff}
        .header{border-bottom:3px solid #0d9488;padding-bottom:16px;margin-bottom:24px}
        .header h1{font-size:22px;color:#0d9488;margin-bottom:4px}
        .header p{color:#64748b;font-size:12px}
        .detections{margin-bottom:20px;padding:12px;background:#f0fdfa;border-radius:8px;border:1px solid #99f6e4}
        .detections strong{font-size:12px;margin-right:8px}
        .report-content{font-size:13px;line-height:1.8}
        .report-content h1,.report-content h2,.report-content h3{color:#0d9488;margin:16px 0 6px}
        .report-content h1{font-size:16px} .report-content h2{font-size:15px} .report-content h3{font-size:14px}
        .report-content strong{color:#0f172a}
        .report-content table{width:100%;border-collapse:collapse;margin:12px 0}
        .report-content th{background:#f0fdfa;color:#0d9488;padding:8px;border:1px solid #99f6e4;font-size:12px}
        .report-content td{padding:7px 8px;border:1px solid #e2e8f0;font-size:12px}
        .report-content tr:nth-child(even) td{background:#f8fafc}
        .disclaimer{margin-top:32px;padding:12px;border:1px solid #e2e8f0;border-radius:8px;font-size:11px;color:#64748b;text-align:center}
        @media print{
          body{padding:20px}
          .no-print{display:none}
          @page{margin:1cm;size:A4}
        }
      </style>
    </head><body>
      <div class="header">
        <h1>🦷 AI Clinical Dental Report</h1>
        <p>Generated by Assnani AI &nbsp;•&nbsp; ${new Date().toLocaleDateString('en-US',{year:'numeric',month:'long',day:'numeric'})} &nbsp;•&nbsp; Powered by Gemini</p>
      </div>
      ${classBadges ? `<div class="detections"><strong>Findings (${total} total):</strong>${classBadges}</div>` : ''}
      <div class="report-content">${reportHtml}</div>
      <div class="disclaimer">⚠️ This is an AI-assisted preliminary analysis. Final diagnosis must be verified by a licensed dental professional.</div>
      <div class="no-print" style="margin-top:24px;text-align:center">
        <button onclick="window.print()" style="padding:10px 28px;background:#0d9488;color:#fff;border:none;border-radius:8px;font-size:14px;font-weight:600;cursor:pointer;">🖨️ Save as PDF / Print</button>
      </div>
    </body></html>`);
    printWin.document.close();
    printWin.onload = () => { setTimeout(() => printWin.print(), 300); };
  };

  // --- Event Listeners ---
  function init() {
    // Text input
    btnSend.addEventListener('click', () => submitTextInput());
    userInput.addEventListener('keydown', e => { if (e.key === 'Enter') submitTextInput(); });

    function submitTextInput() {
      const val = userInput.value.trim();
      if (!val) return;
      addMessage(val, 'user');
      userInput.value = '';
      handleInput(val);
    }

    // File upload — multi-file support
    const ALLOWED_TYPES = /^(image\/(png|jpeg|jpg)|application\/pdf)$/;
    const ALLOWED_EXT = /\.(png|jpe?g|pdf)$/i;

    uploadDropzone.addEventListener('click', () => fileInput.click());
    uploadDropzone.addEventListener('dragover', e => { e.preventDefault(); uploadDropzone.classList.add('drag-over'); });
    uploadDropzone.addEventListener('dragleave', () => uploadDropzone.classList.remove('drag-over'));
    uploadDropzone.addEventListener('drop', e => {
      e.preventDefault();
      uploadDropzone.classList.remove('drag-over');
      if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
    });
    fileInput.addEventListener('change', () => { if (fileInput.files.length) handleFiles(fileInput.files); fileInput.value = ''; });

    function handleFiles(fileList) {
      for (const file of fileList) {
        const typeOk = ALLOWED_TYPES.test(file.type) || ALLOWED_EXT.test(file.name);
        if (!typeOk) { alert(`Unsupported file: ${file.name}. Use PNG, JPG, or PDF.`); continue; }
        uploadedFiles.push(file);
      }
      if (uploadedFiles.length) {
        renderPreviewGrid();
        extractFirstImageDimensions();
      }
    }

    function renderPreviewGrid() {
      previewGrid.innerHTML = '';
      uploadedFiles.forEach((file, idx) => {
        const item = document.createElement('div');
        item.className = 'preview-item';
        const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
        if (isPdf) {
          item.innerHTML = `<span class="pdf-icon">📄</span>`;
        } else {
          const img = document.createElement('img');
          img.src = URL.createObjectURL(file);
          img.alt = file.name;
          item.appendChild(img);
        }
        const nameLabel = document.createElement('span');
        nameLabel.className = 'preview-name';
        nameLabel.textContent = file.name;
        item.appendChild(nameLabel);
        const removeBtn = document.createElement('button');
        removeBtn.className = 'preview-remove';
        removeBtn.innerHTML = '×';
        removeBtn.title = 'Remove';
        removeBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          uploadedFiles.splice(idx, 1);
          if (uploadedFiles.length === 0) {
            uploadDropzone.style.display = 'flex';
            uploadPreview.style.display = 'none';
          } else {
            renderPreviewGrid();
          }
        });
        item.appendChild(removeBtn);
        previewGrid.appendChild(item);
      });
      uploadDropzone.style.display = 'none';
      uploadPreview.style.display = 'flex';
    }

    function extractFirstImageDimensions() {
      const firstImage = uploadedFiles.find(f => f.type.startsWith('image/'));
      if (!firstImage) return;
      const img = new window.Image();
      img.onload = () => {
        imageDimensions = { width: img.naturalWidth, height: img.naturalHeight };
        URL.revokeObjectURL(img.src);
      };
      img.src = URL.createObjectURL(firstImage);
    }

    // Add More button
    btnUploadAdd.addEventListener('click', () => fileInput.click());

    btnUploadSubmit.addEventListener('click', () => {
      if (!uploadedFiles.length) return;
      const names = uploadedFiles.map(f => f.name).join(', ');
      addMessage(`📎 Uploaded ${uploadedFiles.length} file${uploadedFiles.length > 1 ? 's' : ''}: ${names}`, 'user');
      transition('XRAY_ANALYZING');
    });

    btnUploadCancel.addEventListener('click', () => {
      uploadedFiles = [];
      imageDimensions = { width: 0, height: 0 };
      uploadDropzone.style.display = 'flex';
      uploadPreview.style.display = 'none';
      previewGrid.innerHTML = '';
      fileInput.value = '';
    });

    // Side panel
    btnTogglePanel.addEventListener('click', () => {
      sidePanel.style.display = sidePanel.style.display === 'none' ? 'flex' : 'none';
    });
    btnClosePanel.addEventListener('click', () => { sidePanel.style.display = 'none'; });

    // Report modal
    document.getElementById('btn-report-close').addEventListener('click', () => { reportOverlay.style.display = 'none'; });
    document.getElementById('btn-report-new').addEventListener('click', () => resetChat());

    // Print report
    document.getElementById('btn-report-print').addEventListener('click', () => {
      const printWin = window.open('', '_blank', 'width=800,height=900');
      if (!printWin) { alert('Please allow popups to print the report.'); return; }
      printWin.document.write(`<!DOCTYPE html><html><head><title>Dental Assessment Report — Assnani AI</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
          *{margin:0;padding:0;box-sizing:border-box}
          body{font-family:'Inter',sans-serif;padding:32px;color:#1e293b;font-size:13px;line-height:1.6}
          h1{font-size:20px;margin-bottom:4px} h2{font-size:12px;color:#64748b;margin-bottom:20px;font-weight:400}
          .section{margin-bottom:18px}
          .section-title{font-size:13px;font-weight:700;color:#0f766e;text-transform:uppercase;letter-spacing:.5px;border-bottom:2px solid #0f766e;padding-bottom:4px;margin-bottom:8px}
          .item{padding:10px;border:1px solid #e2e8f0;border-radius:6px;margin-bottom:6px;font-size:12px}
          .item strong{color:#0f172a}
          .severity-badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600}
          .severity-high{color:#dc2626;border:1px solid #dc2626}
          .severity-moderate{color:#d97706;border:1px solid #d97706}
          .severity-low{color:#16a34a;border:1px solid #16a34a}
          .disclaimer{margin-top:20px;padding:10px;border:1px solid #e2e8f0;border-radius:6px;font-size:11px;color:#64748b;text-align:center}
          @media print{body{padding:16px}}
        </style></head><body>
        <h1>📋 Dental Assessment Report</h1>
        <h2>AI-Assisted Analysis by Assnani — ${new Date().toLocaleDateString()}</h2>
        ${reportBody.innerHTML.replace(/class="report-section"/g,'class="section"').replace(/class="report-section-title"/g,'class="section-title"').replace(/class="report-item"/g,'class="item"')}
        <div class="disclaimer">⚠️ This is an AI-assisted preliminary analysis. Final diagnosis must be verified by a licensed dental professional.</div>
      </body></html>`);
      printWin.document.close();
      printWin.onload = () => { printWin.print(); };
    });

    // New chat
    document.getElementById('btn-new-chat').addEventListener('click', () => resetChat());

    // Start conversation
    transition('WELCOME');
  }

  function resetChat() {
    reportOverlay.style.display = 'none';
    sidePanel.style.display = 'none';
    btnTogglePanel.style.display = 'none';
    msgContainer.innerHTML = '';
    hideQuickReplies();
    hideUpload();
    hideInput();
    symptoms = {
      has_pain:false,pain_location:'',pain_type:'',pain_intensity:0,
      pain_duration:'',pain_triggers:[],has_swelling:false,
      swelling_severity:'',has_fever:false,difficulty_opening:false,
      has_trauma:false,has_broken_tooth:false,previous_root_canal:false,
      last_visit:'',recent_extraction:false
    };
    detectionData = null;
    analysisResult = null;
    geminiReport = null;
    const oldPdf = document.getElementById('panel-pdf-section');
    if (oldPdf) oldPdf.remove();
    uploadedFiles = [];
    imageDimensions = { width: 0, height: 0 };
    state = 'WELCOME';
    transition('WELCOME');
  }

  return { init };
})();

document.addEventListener('DOMContentLoaded', () => Chatbot.init());