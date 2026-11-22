const feed = document.getElementById("feed");

async function loadNews() {
  try {
    const res = await fetch("data/news.json");
    if (!res.ok) throw new Error(res.status);
    const items = await res.json();
    feed.innerHTML = items.map(renderCard).join("");
  } catch (err) {
    feed.textContent = "Could not load news: " + err.message;
  }
}

function renderCard(item) {
  const lang = "en";
  const section = (label, key) =>
    item[key][lang] ? `<h3>${label}</h3><p>${item[key][lang]}</p>` : "";

  return `
    <article class="card">
      <small>${item.date} · ${item.topic}</small>
      <h2>${item.title[lang]}</h2>
      ${section("News Details", "details")}
      ${section("Why It Matters", "why_it_matters")}
      ${section("Perspectives", "perspectives")}
      ${section("Logical Reasons & Possibilities", "reasoning")}
      <a href="${item.source.url}" target="_blank" rel="noopener">
        Source: ${item.source.name}
      </a>
    </article>`;
}

loadNews();
