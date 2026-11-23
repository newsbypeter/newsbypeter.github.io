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

function renderStory(item) {
  const why = t(item.why_it_matters);
  return `
    <article class="story">
      <p class="story__meta">
        <time datetime="${esc(item.date)}">${formatDate(item.date)}</time>
        <span>${esc(item.topic.replace(/-/g, " "))}</span>
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

function fillTopics() {
  const topics = [...new Set(allItems.map((i) => i.topic))];
  topicSelect.innerHTML =
    `<option value="all">All topics</option>` +
    topics.map((x) => `<option value="${esc(x)}">${esc(x.replace(/-/g, " "))}</option>`).join("");
}

function render() {
  const role = roleSelect.value;
  const topic = topicSelect.value;
  const shown = allItems.filter(
    (i) => i.roles.includes(role) && (topic === "all" || i.topic === topic)
  );
  feed.innerHTML = shown.length
    ? shown.map(renderStory).join("")
    : `<p class="status">No stories match these filters.</p>`;
}

async function loadNews() {
  try {
    const res = await fetch("data/news.json");
    if (!res.ok) throw new Error("file not found (" + res.status + ")");
    allItems = await res.json();
    fillTopics();
    const prefs = loadPrefs();
    if (prefs.role) roleSelect.value = prefs.role;
    if (prefs.topic && [...topicSelect.options].some((o) => o.value === prefs.topic)) {
      topicSelect.value = prefs.topic;
    }
    render();
  } catch (err) {
    feed.innerHTML = `<p class="status">Could not load news: ${esc(err.message)}</p>`;
  }
}

[roleSelect, topicSelect].forEach((el) =>
  el.addEventListener("change", () => {
    savePrefs();
    render();
  })
);

loadNews();
