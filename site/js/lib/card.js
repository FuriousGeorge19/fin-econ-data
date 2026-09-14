// The only code that plots into a card (chart-components spec, "Card mount
// lifecycle"). Builds the whole card DOM from a block's JSON, fetches its
// data eagerly, then imports the chart type module and calls its render
// once. Every query is scoped to the card's own container so more than one
// card — even two mounts of the same type — never collide.
import { loadSeries } from './data.js';
import { getTheme } from './theme.js';
import { freshnessBadgeText, renderAboutHTML } from './asof.js';
import { downloadBlob } from './export.js';
import { mountPresets } from './presets.js';

function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[ch]));
}

function cardSkeleton(block, presentation) {
    const hasTable = !!presentation.table;
    const hasStats = !!presentation.stats;
    const panels = ['chart', hasTable ? 'table' : null, 'about'].filter(Boolean);
    const labels = { chart: 'Chart', table: 'Table', about: 'About' };
    const tabsHtml = panels
        .map((p, i) => `<button class="subtab${i === 0 ? ' active' : ''}" data-panel="${p}">${labels[p]}</button>`)
        .join('');

    const tablePanel = hasTable ? `
        <div class="subtab-panel" data-panel="table" hidden>
            <div class="table-slot"><p class="loading">Loading data…</p></div>
        </div>` : '';

    return `
        <div class="card-headrow">
            <div>
                <h2><a href="${escapeHtml(block.href)}">${escapeHtml(block.title)}</a></h2>
                <p class="subtitle">${escapeHtml(block.summary || '')}</p>
            </div>
            <span class="badge" hidden></span>
        </div>
        <div class="stats"${hasStats ? '' : ' hidden'}></div>
        <div class="subtabs-row">
            <div class="subtabs">${tabsHtml}</div>
            <div class="export-row">
                <button class="export-btn" data-export="csv">Export CSV</button>
                <button class="export-btn" data-export="json">Export JSON</button>
            </div>
        </div>
        <div class="subtab-panel" data-panel="chart">
            <div class="control-row">
                <div class="presets"></div>
                <div class="controls"></div>
            </div>
            <div class="chart"></div>
        </div>
        ${tablePanel}
        <div class="subtab-panel" data-panel="about" hidden>
            <div class="about"><p class="loading">Loading data…</p></div>
        </div>
    `;
}

function wireSubtabs(container) {
    container.querySelectorAll('.subtab').forEach(btn => {
        btn.addEventListener('click', () => selectSubtab(container, btn.dataset.panel));
    });
}

function selectSubtab(container, panel) {
    container.querySelectorAll('.subtab').forEach(b => {
        b.classList.toggle('active', b.dataset.panel === panel);
    });
    container.querySelectorAll('.subtab-panel').forEach(p => {
        p.hidden = p.dataset.panel !== panel;
    });
    if (panel === 'chart') {
        const gd = container.querySelector('.chart');
        if (gd && gd._fullLayout) Plotly.Plots.resize(gd);
    }
}

function renderBadge(container, ctx) {
    const el = container.querySelector('.badge');
    const text = freshnessBadgeText(ctx.meta, ctx.as_of, ctx.today);
    if (text) {
        el.textContent = text;
        el.hidden = false;
    } else {
        el.hidden = true;
    }
}

function renderAbout(container, ctx) {
    const el = container.querySelector('.about');
    if (el) el.innerHTML = renderAboutHTML(ctx.meta, ctx.as_of);
}

function renderStats(container, statsList) {
    const el = container.querySelector('.stats');
    if (!el) return;
    if (!statsList || !statsList.length) {
        el.hidden = true;
        return;
    }
    el.hidden = false;
    el.innerHTML = statsList.map(s => `
        <div class="stat">
            <span class="label">${escapeHtml(s.label)}</span>
            <span class="value"${s.color ? ` style="color: ${s.color}"` : ''}>${escapeHtml(s.value)}</span>
            ${s.date ? `<span class="stat-date">${escapeHtml(s.date)}</span>` : ''}
        </div>
    `).join('');
}

function renderTable(container, result) {
    const slot = container.querySelector('.table-slot');
    if (!slot) return;
    if (!result) {
        slot.innerHTML = '';
        return;
    }
    const thead = `<tr>${result.columns.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>`;
    const tbody = result.rows.map(row => `<tr>${row.map(cell =>
        `<td${cell.color ? ` style="color: ${cell.color}"` : ''}>${escapeHtml(String(cell.text))}</td>`
    ).join('')}</tr>`).join('');
    const note = result.note ? `<p class="subtitle">${escapeHtml(result.note)}</p>` : '';
    slot.innerHTML = `${note}<table><thead>${thead}</thead><tbody>${tbody}</tbody></table>`;
}

function wireExport(container, ctx, type) {
    const filenameBase = `${ctx.id}_${ctx.as_of.last_observation}`;
    container.querySelector('[data-export="csv"]').addEventListener('click', () => {
        downloadBlob(`${filenameBase}.csv`, type.csv ? type.csv(ctx) : '', 'text/csv');
    });
    container.querySelector('[data-export="json"]').addEventListener('click', () => {
        downloadBlob(`${filenameBase}.json`, JSON.stringify(ctx.data, null, 2), 'application/json');
    });
}

function buildCtx({ block, data, recessions, today, controlsEl }) {
    return {
        id: block.id,
        data,
        meta: data.meta,
        as_of: data.as_of,
        presentation: block.presentation,
        today,
        theme: getTheme(),
        variant: block.size || 'half',
        recessions,
        initialPreset: block.preset || null,
        slots: { controls: controlsEl },
    };
}

export async function mount(block, today) {
    if (block.text) return; // narrative text blocks: nothing to mount (Phase 5)

    const container = document.querySelector(`.card[data-block="${block.id}"]`);
    if (!container) return;

    const presentation = block.presentation || {};
    const chart = presentation.chart || {};

    container.classList.add(`card--${block.size || 'half'}`);
    container.innerHTML = cardSkeleton(block, presentation);
    wireSubtabs(container);

    let data;
    let recessions = null;
    try {
        const [seriesData, usrecData] = await Promise.all([
            loadSeries(block.id),
            chart.recessions ? loadSeries('usrec').catch(() => null) : Promise.resolve(null),
        ]);
        data = seriesData;
        recessions = usrecData ? usrecData.recessions : null;
    } catch (err) {
        container.querySelector('.chart').innerHTML =
            `<p class="loading">Failed to load data. ${escapeHtml(err.message)}</p>`;
        return;
    }

    const controlsEl = container.querySelector('.controls');
    const ctx = buildCtx({ block, data, recessions, today, controlsEl });

    renderBadge(container, ctx);
    renderAbout(container, ctx);

    let type;
    try {
        type = await import(`/js/charts/${chart.type}.js`);
    } catch (err) {
        container.querySelector('.chart').innerHTML =
            `<p class="loading">Failed to load chart module. ${escapeHtml(err.message)}</p>`;
        return;
    }

    if (presentation.stats && type.stats) renderStats(container, type.stats(ctx));
    if (presentation.table && type.table) renderTable(container, type.table(ctx));
    wireExport(container, ctx, type);

    const chartEl = container.querySelector('.chart');
    let instance = type.render(chartEl, ctx);

    if (chart.presets && chart.presets.length) {
        mountPresets(container.querySelector('.presets'), {
            presets: chart.presets, gd: chartEl, today, initialPreset: ctx.initialPreset,
        });
    }

    // A theme toggle is not wired into the generated pages yet (open item —
    // see the S6b handoff); this listener is here so it works the moment
    // one dispatches `themechange`, with no further contract change needed.
    document.addEventListener('themechange', () => {
        instance.destroy();
        const newCtx = buildCtx({ block, data, recessions, today, controlsEl });
        instance = type.render(chartEl, newCtx);
        if (presentation.stats && type.stats) renderStats(container, type.stats(newCtx));
        if (presentation.table && type.table) renderTable(container, type.table(newCtx));
    });
}
