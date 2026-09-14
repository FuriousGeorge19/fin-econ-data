// UTC-only date arithmetic and formatting, shared by every card and chart
// type. The browser only ever compares dates here — business-day arithmetic
// stays in scripts/staleness.py (chart-chrome, data-freshness specs).

const MONTH_ABBR = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                     'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

export function todayET() {
    return new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' });
}

function toISO(utcMs) {
    return new Date(utcMs).toISOString().slice(0, 10);
}

export function addDaysUTC(dateStr, days) {
    const [y, m, d] = dateStr.split('-').map(Number);
    return toISO(Date.UTC(y, m - 1, d + days));
}

export function addMonthsUTC(dateStr, months) {
    const [y, m, d] = dateStr.split('-').map(Number);
    return toISO(Date.UTC(y, m - 1 + months, d));
}

export function addYearsUTC(dateStr, years) {
    const [y, m, d] = dateStr.split('-').map(Number);
    return toISO(Date.UTC(y + years, m - 1, d));
}

export function formatDateLong(iso) {
    const [y, m, d] = iso.split('-').map(Number);
    return `${d} ${MONTH_ABBR[m - 1]} ${y}`;
}

export function formatFetchedAt(iso) {
    const dt = new Date(iso);
    const d = dt.getUTCDate();
    const mon = MONTH_ABBR[dt.getUTCMonth()];
    const y = dt.getUTCFullYear();
    const hh = String(dt.getUTCHours()).padStart(2, '0');
    const mm = String(dt.getUTCMinutes()).padStart(2, '0');
    return `${d} ${mon} ${y}, ${hh}:${mm} UTC`;
}

export function daysBetweenUTC(fromIso, toIso) {
    const [fy, fm, fd] = fromIso.split('-').map(Number);
    const [ty, tm, td] = toIso.split('-').map(Number);
    return Math.round((Date.UTC(ty, tm - 1, td) - Date.UTC(fy, fm - 1, fd)) / 86400000);
}

// Single shared "nearest on or before" primitive — every comparison (stat
// windows, table changes, curve overlays) is built on this one function.
export function nearestOnOrBefore(sortedDates, targetISO) {
    for (let i = sortedDates.length - 1; i >= 0; i--) {
        if (sortedDates[i] <= targetISO) return sortedDates[i];
    }
    return null;
}

export function valueOnOrBefore(observations, targetISO) {
    const dates = observations.map(o => o.date);
    const found = nearestOnOrBefore(dates, targetISO);
    return found === null ? null : observations.find(o => o.date === found);
}
