/* ===== Tooth Chart — Interactive SVG Dental Chart ===== */
const ToothChart = {
  // FDI tooth numbering
  upperRight: [18,17,16,15,14,13,12,11],
  upperLeft:  [21,22,23,24,25,26,27,28],
  lowerLeft:  [31,32,33,34,35,36,37,38],
  lowerRight: [48,47,46,45,44,43,42,41],

  selectedQuadrant: null,

  render(container, onSelect) {
    container.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'tooth-chart-container';
    wrap.innerHTML = `<p>Select the area of discomfort:</p>`;

    const chart = document.createElement('div');
    chart.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:4px;width:100%;max-width:400px;';

    const quadrants = [
      { key: 'upper-right', label: 'Upper Right', teeth: this.upperRight, color: '#0ea5e9' },
      { key: 'upper-left',  label: 'Upper Left',  teeth: this.upperLeft,  color: '#8b5cf6' },
      { key: 'lower-right', label: 'Lower Right', teeth: this.lowerRight, color: '#f59e0b' },
      { key: 'lower-left',  label: 'Lower Left',  teeth: this.lowerLeft,  color: '#00d4aa' },
    ];

    quadrants.forEach(q => {
      const qDiv = document.createElement('button');
      qDiv.className = 'quick-reply-btn';
      qDiv.style.cssText = `
        display:flex;flex-direction:column;align-items:center;gap:4px;
        padding:14px 10px;border-radius:12px;width:100%;white-space:normal;
      `;
      qDiv.innerHTML = `
        <span style="font-size:20px">${q.key.includes('upper') ? '🦷' : '🦴'}</span>
        <span style="font-weight:600;font-size:13px">${q.label}</span>
        <span style="font-size:10px;color:var(--text-muted)">Teeth ${q.teeth[q.teeth.length-1]}-${q.teeth[0]}</span>
      `;
      qDiv.addEventListener('click', () => {
        this.selectedQuadrant = q.key;
        chart.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
        qDiv.classList.add('selected');
        setTimeout(() => onSelect(q.key, q.label), 300);
      });
      chart.appendChild(qDiv);
    });

    // Add "General / All" option
    const genBtn = document.createElement('button');
    genBtn.className = 'quick-reply-btn';
    genBtn.style.cssText = 'grid-column:span 2;padding:10px;';
    genBtn.textContent = '🔄 General / All areas';
    genBtn.addEventListener('click', () => {
      this.selectedQuadrant = 'general';
      chart.querySelectorAll('button').forEach(b => b.classList.remove('selected'));
      genBtn.classList.add('selected');
      setTimeout(() => onSelect('general', 'General / All areas'), 300);
    });
    chart.appendChild(genBtn);

    wrap.appendChild(chart);
    container.appendChild(wrap);
  }
};
