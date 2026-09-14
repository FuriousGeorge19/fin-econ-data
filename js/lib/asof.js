import { formatDateLong, formatFetchedAt, addMonthsUTC, daysBetweenUTC } from './dates.js';

function inputPhrase(inputDesc, asOfInput) {
    const label = inputDesc.id;
    if (inputDesc.status === 'discontinued') {
        const since = formatDateLong(addMonthsUTC(asOfInput.confirmed_through, 1)).replace(/^\d+ /, '');
        return `${label} confirmed through ${asOfInput.period_label}, estimated since ${since} (source discontinued)`;
    }
    return `${label} through ${asOfInput.period_label}`;
}

export function asOfSourceLine(meta, as_of) {
    if (as_of.inputs) {
        const parts = meta.inputs.map(inp => inputPhrase(inp, as_of.inputs[inp.id]));
        return `${meta.source_line} · ${parts.join(' · ')}`;
    }
    return `${meta.source_line} · data through ${as_of.period_label}`;
}

// Pure builder for the in-chart source-line annotation; the shared layout
// builder (plotly-layout.js) is the one that puts it into layout.annotations
// and reserves room for it at the bottom of the plot (chart-chrome spec).
export function asOfAnnotation(meta, as_of, theme) {
    return {
        xref: 'paper', yref: 'paper',
        x: 0, y: 0,
        xanchor: 'left', yanchor: 'top',
        yshift: -30,
        text: asOfSourceLine(meta, as_of),
        showarrow: false,
        align: 'left',
        font: { color: theme.annotation, size: 10 },
    };
}

function overdueInputEntry(meta, as_of) {
    if (!as_of.inputs) return null;
    return Object.entries(as_of.inputs).find(([id, entry]) => {
        const inputDesc = meta.inputs.find(i => i.id === id);
        const required = inputDesc.required !== false;
        const active = (inputDesc.status || 'active') === 'active';
        return required && active && entry.due_by === as_of.due_by;
    });
}

export function freshnessBadgeText(meta, as_of, today) {
    if (today <= as_of.due_by) return null;
    const daysLate = daysBetweenUTC(as_of.due_by, today);
    const dueByLabel = formatDateLong(as_of.due_by);
    const overdue = overdueInputEntry(meta, as_of);
    if (overdue) {
        const [id, entry] = overdue;
        const label = id.charAt(0).toUpperCase() + id.slice(1);
        return `${label} overdue · ${entry.period_label} expected by ${dueByLabel} · ${daysLate} days late`;
    }
    return `Overdue · expected by ${dueByLabel} · ${daysLate} days late`;
}

export function renderAboutHTML(meta, as_of) {
    const sourcesHTML = meta.sources.map(s => {
        const licence = s.licence ? ` — ${s.licence}` : '';
        return `<li><a href="${s.url}" target="_blank" rel="noopener">${s.name}</a>${licence}</li>`;
    }).join('');

    const inputsHTML = meta.inputs.map(inp => {
        const entry = (as_of.inputs && as_of.inputs[inp.id]) || as_of;
        const status = inp.status || 'active';
        const statusCell = status === 'discontinued'
            ? `discontinued<span class="about-note">${inp.status_note || ''}</span>`
            : status;
        return `<tr>
            <td>${inp.label}</td>
            <td>${inp.series_id || '—'}</td>
            <td>${inp.cadence}</td>
            <td>${inp.publication_lag_business_days} business days</td>
            <td>${entry.period_label || '—'}</td>
            <td>${statusCell}</td>
        </tr>`;
    }).join('');

    const coverageHTML = (as_of.first_observation && as_of.observation_count)
        ? `<p>Coverage: ${formatDateLong(as_of.first_observation)} – ${formatDateLong(as_of.last_observation)} (${as_of.observation_count.toLocaleString()} observations).</p>`
        : `<p>Latest observation: ${as_of.period_label}.</p>`;

    const methodologyHTML = (meta.methodology || []).map(p => `<p>${p}</p>`).join('');
    const notesHTML = (meta.notes || []).map(p => `<p>${p}</p>`).join('');

    return `
        <div class="about-section">
            <h3>Sources</h3>
            <ul>${sourcesHTML}</ul>
        </div>
        <div class="about-section">
            <h3>Inputs</h3>
            <table class="about-table">
                <thead>
                    <tr>
                        <th>Input</th><th>Series ID</th><th>Cadence</th>
                        <th>Publication lag</th><th>Last observation</th><th>Status</th>
                    </tr>
                </thead>
                <tbody>${inputsHTML}</tbody>
            </table>
        </div>
        <div class="about-section">
            <h3>Freshness</h3>
            <p>Next update expected by ${formatDateLong(as_of.due_by)} (judged on the US Eastern date).</p>
            <p>Last fetched: ${formatFetchedAt(as_of.fetched_at)}.</p>
            ${coverageHTML}
        </div>
        <div class="about-section">
            <h3>Revisions</h3>
            <p>${meta.revision_note}</p>
        </div>
        <div class="about-section">
            <h3>Methodology</h3>
            ${methodologyHTML}
        </div>
        ${notesHTML ? `<div class="about-section"><h3>Notes</h3>${notesHTML}</div>` : ''}
    `;
}
