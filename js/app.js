const feed = document.getElementById("feed");
const LANG = "en"; // becomes "en" or "my" in a later task

function esc(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}

function formatDate(iso) {
  return new Date(iso + "T00:00:00").toLocaleDateString("en-GB", {
    day: "numeric", month: "short", year: "numeric",
  });
}

function section(label, field) {
  const text = field?.[LANG];
  return text ? `<h3>${label}</h3><p>${esc(text)}</p>` : "";
}

function renderStory(item) {
  const why = item.why_it_matters?.[LANG];
  return `
    <article class="story">
      <div class="meta">
        <time datetime="${esc(item.date)}">${formatDate(item.date)}</time>
        <span class="topic">${esc(item.topic.replace(/-/g, " "))}</span>
      </div>
      <h2>${esc(item.title[LANG])}</h2>
      ${section("News details", item.details)}
      ${why ? `<div class="why"><h3>Why it matters</h3><p>${esc(why)}</p></div>` : ""}
      ${section("Perspectives", item.perspectives)}
      ${section("Logical reasons and possibilities", item.reasoning)}
      <a class="source" href="${esc(item.source.url)}" target="_blank" rel="noopener">
        Source: ${esc(item.source.name)}
      </a>
    </article>`;
}

async function loadNews() {
  try {
    const res = await fetch("data/news.json");
    if (!res.ok) throw new Error("file not found (" + res.status + ")");
    const items = await res.json();
    feed.innerHTML = items.map(renderStory).join("");
  } catch (err) {
    feed.innerHTML = `<p class="status">Could not load news: ${esc(err.message)}</p>`;
  }
}

loadNews();
