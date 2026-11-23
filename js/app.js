const feed = document.getElementById("feed");
const roleSelect = document.getElementById("role");
const topicSelect = document.getElementById("topic");
const LANG = "en"; // becomes "en" or "my" in a later task
let allItems = [];

document.documentElement.lang = LANG;

const esc = (s) =>
  String(s ?? "").replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));

const t = (field) => field?.[LANG] || field?.en || "";
const nice = (s) => s.replace(/-/g, " ").replace(/^./, (c) => c.toUpperCase());
const colour = (s) => [...s].reduce((a, c) => a + c.charCodeAt(0), 0) % 4;

function loadPrefs() {
  try {
    return JSON.parse(localStorage.getItem("nbp-prefs")) || {};
  } catch {
    return {};
  }
}

function savePrefs() {
  localStorage.setItem("nbp-prefs", JSON.stringify({
    role: roleSelect.value,
    topic: topicSelect.value,
  }));
}

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function depth(label, field) {
  const text = t(field);
  return text
    ? `<details class="depth"><summary>${label}</summary><div>${esc(text)}</div></details>`
    : "";
}

function renderStory(item, i) {
  const why = t(item.why_it_matters);
  return `
    <article class="story" data-c="${colour(item.topic)}" style="--i:${Math.min(i, 8)}">
      ${i === 0 ? `<span class="badge">Top story</span>` : ""}
      <p class="story__meta">
        <time datetime="${esc(item.date)}">${formatDate(item.date)}</time>
        <span>${esc(nice(item.topic))}</span>
      </p>
      <h2 class="story__title">${esc(t(item.title))}</h2>
      <p class="story__lede">${esc(t(item.details))}</p>
      ${why ? `<aside class="note"><strong>Why it matters</strong><p>${esc(why)}</p></aside>` : ""}
      ${depth("Perspectives", item.perspectives)}
      ${depth("Logical reasons and possibilities", item.reasoning)}
      <footer class="story__foot">
        <a href="${esc(item.source.url)}" target="_blank" rel="noopener">Source: ${esc(item.source.name)}</a>
      </footer>
    </article>`;
}

function fillSelects() {
  const roles = [...new Set(allItems.flatMap((i) => i.roles))];
  const topics = [...new Set(allItems.map((i) => i.topic))];
  roleSelect.innerHTML = roles
    .map((r) => `<option value="${esc(r)}">${esc(nice(r))}</option>`).join("");
  topicSelect.innerHTML =
    `<option value="all">All topics</option>` +
    topics.map((x) => `<option value="${esc(x)}">${esc(nice(x))}</option>`).join("");
}

function render() {
  const role = roleSelect.value;
  const topic = topicSelect.value;
  const shown = allItems.filter(
    (i) => i.roles.includes(role) && (topic === "all" || i.topic === topic)
  );
  document.getElementById("count").textContent =
    shown.length ? `${shown.length} ${shown.length === 1 ? "story" : "stories"}` : "";
  feed.innerHTML = shown.length
    ? shown.map(renderStory).join("")
    : `<p class="status">No stories match these filters. Try another topic.</p>`;
}

async function loadNews() {
  try {
    const res = await fetch("data/news.json");
    if (!res.ok) throw new Error("file not found (" + res.status + ")");
    allItems = await res.json();
    fillSelects();
    const prefs = loadPrefs();
    if ([...roleSelect.options].some((o) => o.value === prefs.role)) roleSelect.value = prefs.role;
    if ([...topicSelect.options].some((o) => o.value === prefs.topic)) topicSelect.value = prefs.topic;
    render();
  } catch (err) {
    feed.innerHTML = `<p class="status">Could not load news: ${esc(err.message)}</p>`;
  }
}

document.getElementById("today").textContent = new Date().toLocaleDateString("en-GB", {
  weekday: "long", day: "numeric", month: "long",
});

[roleSelect, topicSelect].forEach((el) =>
  el.addEventListener("change", () => {
    savePrefs();
    render();
  })
);

loadNews();
