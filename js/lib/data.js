// Root-relative fetch so a card on any page (/, /economy/, /charts/<id>/,
// /<section>/<slug>/) resolves the same file regardless of its own depth.
export async function loadSeries(id) {
    const resp = await fetch(`/data/${id}.json`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return resp.json();
}
