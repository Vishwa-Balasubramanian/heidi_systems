import { filterCompanies, sortCompanies } from "./logic.mjs";
import { renderContacts } from "./contacts.mjs";
const app = document.querySelector("#app"),
  dialog = document.querySelector("#details");
let data, state, returnFocus;
const esc = (v) =>
  String(v ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const num = (v) => (v == null ? "Unknown" : Number(v).toLocaleString("en-GB"));
const safe = (v) => {
  try {
    const u = new URL(v);
    return ["http:", "https:"].includes(u.protocol) ? esc(u.href) : "#";
  } catch {
    return "#";
  }
};
const labels = {
  residential_management: "Residential management",
  weg_management: "WEG management",
  rental_management: "Rental management",
  commercial_management: "Commercial management",
  managed_units: "Published managed units",
  managed_buildings: "Published buildings / properties",
  heating_cost_billing_relevance: "Heating-cost billing",
  operating_cost_billing_relevance: "Operating-cost billing",
  digital_features: "Customer / owner portal",
  property_coverage: "Multiple-property coverage",
  Berlin_service_area: "Berlin service coverage",
};
const statusLabels = {
  "AI completed": "AI enrichment completed",
  "AI failed": "AI response failed validation",
  "no saved homepage": "No saved homepage available",
  "no listed website": "No website in directory",
};
const fmt = (v) =>
  v === null || v === undefined
    ? "Unknown"
    : v === true
      ? "Evidence found"
      : v === false
        ? "Explicit negative evidence"
        : esc(num(v));
const badge = (p) =>
  `<span class="badge ${p === "High Priority" ? "high" : p === "Medium Priority" ? "medium" : "research"}">${esc(p)}</span>`;
const date = (v) =>
  v
    ? new Date(v).toLocaleDateString("en-GB", {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "Europe/Berlin",
      })
    : "Date unavailable";
function getState() {
  const p = new URLSearchParams(location.search);
  return {
    view: ["priority", "companies", "overview", "methodology"].includes(
      p.get("view"),
    )
      ? p.get("view")
      : "priority",
    priority: p.get("priority") || "all",
    q: p.get("q") || "",
    sort: p.get("sort") || "recommended",
    service: p.get("service") || "",
    units: p.get("units") || "",
    billing: p.get("billing") || "",
    digital: p.get("digital") || "",
    status: p.get("status") || "",
    completeness: p.get("completeness") || "",
    page: Math.max(1, Number(p.get("page")) || 1),
    company: p.get("company") || "",
    filters: p.get("filters") === "1",
  };
}
function update(changes, replace = false) {
  const n = { ...state, ...changes };
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(n)) {
    if (
      v &&
      v !== "all" &&
      !(k === "page" && v === 1) &&
      !(k === "sort" && v === "recommended")
    )
      p.set(k, v === true ? "1" : String(v));
  }
  history[replace ? "replaceState" : "pushState"](
    {},
    "",
    `${location.pathname}?${p}`,
  );
  state = getState();
  render();
}
function navigate(view, priority = "all") {
  update({
    view,
    priority,
    q: "",
    service: "",
    units: "",
    billing: "",
    digital: "",
    status: "",
    completeness: "",
    page: 1,
    company: "",
  });
}
function reset() {
  update({
    q: "",
    priority: "all",
    service: "",
    units: "",
    billing: "",
    digital: "",
    status: "",
    completeness: "",
    page: 1,
  });
}
function metrics() {
  return `<div class="stats">${[
    [
      "Priority shortlist",
      data.metrics.high_priority + data.metrics.medium_priority,
      "High + medium priority",
      "priority",
      "all",
      true,
    ],
    [
      "High priority",
      data.metrics.high_priority,
      "Strongest observed business fit",
      "priority",
      "High Priority",
      false,
    ],
    [
      "Medium priority",
      data.metrics.medium_priority,
      "Promising companies to review",
      "priority",
      "Medium Priority",
      false,
    ],
    [
      "All Berlin companies",
      data.companies.length,
      `${data.metrics.needs_research} still need research`,
      "companies",
      "all",
      false,
    ],
  ]
    .map(
      ([label, value, hint, view, priority, highlight]) =>
        `<button class="stat ${highlight ? "emphasis" : ""}" data-goto="${view}" data-priority="${priority}"><span class="label">${label}</span><span class="arrow">↗</span><strong class="number">${value}</strong><span class="hint">${hint}</span></button>`,
    )
    .join("")}</div>`;
}
function row(c) {
  let unit =
    c.managed_units_qualifier === "lower bound"
      ? `${num(c.managed_units)}+`
      : c.managed_units_qualifier === "approximate"
        ? `~${num(c.managed_units)}`
        : num(c.managed_units);
  return `<tr class="company-row"><td><button class="company-name" data-company="${esc(c.company_id)}">${esc(c.company_name)}<span class="domain">${esc(c.domain || "Website not listed")}</span></button></td><td>${badge(c.priority)}</td><td><span class="score">${c.business_fit_score}<small> / 100</small></span></td><td><div class="completeness"><span class="meter"><i style="width:${c.evidence_completeness}%"></i></span>${c.evidence_completeness}%</div></td><td class="units">${unit}<small>${c.managed_units == null ? "Needs research" : "Published company portfolio"}</small></td><td>${
    [
      ["weg_management", "WEG"],
      ["rental_management", "Rental"],
      ["residential_management", "Residential"],
    ]
      .filter(([k]) => c[k] === true)
      .map(([, label]) => `<span class="service">${label}</span>`)
      .join("") || '<span class="domain">Unconfirmed</span>'
  }</td><td>${c.website ? `<a class="external" href="${safe(c.website)}" target="_blank" rel="noopener noreferrer" aria-label="Visit ${esc(c.company_name)} website">↗</a>` : '<span class="domain">—</span>'}</td><td><button class="row-details" data-company="${esc(c.company_id)}" aria-label="View ${esc(c.company_name)} details">→</button></td></tr>`;
}
function table(rows, group = false) {
  let last;
  return `<div class="table-scroll"><table><thead><tr>${["Company", "Priority", "Fit score", "Completeness", "Units", "Services", "Web", ""].map((h) => `<th scope="col">${h}</th>`).join("")}</tr></thead><tbody>${rows
    .map((c) => {
      let header = "";
      if (group && last !== c.priority) {
        last = c.priority;
        header = `<tr><td colspan="8" class="group-label">${esc(c.priority.toUpperCase())}</td></tr>`;
      }
      return header + row(c);
    })
    .join("")}</tbody></table></div>`;
}
const opt = (value, label, current) =>
  `<option value="${esc(value)}" ${value === current ? "selected" : ""}>${esc(label)}</option>`;
function filters() {
  return `<div class="filter-grid" ${state.filters ? "" : "hidden"}>${[
    [
      "service",
      "Service",
      [
        ["", "All services"],
        ["weg_management", "WEG management"],
        ["rental_management", "Rental management"],
        ["residential_management", "Residential management"],
      ],
    ],
    [
      "units",
      "Portfolio",
      [
        ["", "Any portfolio"],
        ["known", "Published units available"],
      ],
    ],
    [
      "billing",
      "Billing",
      [
        ["", "Any billing status"],
        ["yes", "Billing evidence found"],
      ],
    ],
    [
      "digital",
      "Digital portal",
      [
        ["", "Any portal status"],
        ["yes", "Portal evidence found"],
      ],
    ],
    [
      "status",
      "AI research",
      [["", "All research statuses"], ...Object.entries(statusLabels)],
    ],
    [
      "completeness",
      "Completeness",
      [
        ["", "Any completeness"],
        ["60", "60% or more"],
        ["80", "80% or more"],
        ["100", "100%"],
      ],
    ],
  ]
    .map(
      ([key, label, choices]) =>
        `<label>${label}<select data-filter="${key}" aria-label="${label}">${choices.map(([v, l]) => opt(v, l, state[key])).join("")}</select></label>`,
    )
    .join("")}</div>`;
}
function list() {
  const priority = state.view === "priority",
    filtered = sortCompanies(
      filterCompanies(data.companies, state),
      state.sort,
      priority,
    );
  const pages = Math.max(1, Math.ceil(filtered.length / 25));
  const page = Math.min(state.page, pages);
  const shown = filtered.slice((page - 1) * 25, page * 25);
  const tabs = priority
    ? [
        ["all", "All priority", 35],
        ["High Priority", "High", 18],
        ["Medium Priority", "Medium", 17],
      ]
    : [
        ["all", "All companies", 292],
        ["High Priority", "High", 18],
        ["Medium Priority", "Medium", 17],
        ["Needs Research", "Needs research", 257],
      ];
  const active = [
    "q",
    "service",
    "units",
    "billing",
    "digital",
    "status",
    "completeness",
  ].filter((k) => state[k]);
  return `<div class="eyebrow">${priority ? "YOUR NEXT CONVERSATIONS START HERE" : "THE COMPLETE RESEARCH DATASET"}</div><div class="hero"><div><h1>${priority ? "The companies worth a closer look." : "Every company. A clearer picture."}</h1><p class="intro">${priority ? "35 priority leads, ranked by published business evidence. Explore the fit, see the sources, and decide where to focus." : "Explore all 292 directory-listed Berlin companies, including those that need more research."}</p></div><span class="small-tag">${priority ? "35 evidence-backed candidates" : "292 companies · one research view"}</span></div>${metrics()}<section class="panel"><div class="panel-head"><div><h2>${priority ? "Priority leads" : "All companies"}</h2><p>${priority ? "A focused shortlist for your next review." : "Search the full dataset and uncover the evidence."}</p></div><span class="small-tag">${filtered.length} companies</span></div><div class="toolbar"><label class="search"><span>⌕</span><input id="search" type="search" placeholder="Search company, address or website…" aria-label="Search companies" value="${esc(state.q)}"></label><select id="sort" aria-label="Sort companies">${[
    ["recommended", "Sort: best fit"],
    ["name", "Sort: company name"],
    ["completeness", "Sort: completeness"],
    ["units", "Sort: published units"],
  ]
    .map(([v, l]) => opt(v, l, state.sort))
    .join(
      "",
    )}</select><button class="filter-toggle" id="filter-toggle" aria-expanded="${state.filters}">☷ Filters ${state.filters ? "−" : "+"}</button></div><div class="tabs" role="group" aria-label="Priority filters">${tabs.map(([p, label, n]) => `<button class="tab ${state.priority === p ? "selected" : ""}" data-tab="${p}" aria-pressed="${state.priority === p}">${label}<b>${n}</b></button>`).join("")}${active.length || state.priority !== "all" ? '<button class="clear" id="clear">Clear filters</button>' : ""}</div>${filters()}${active.length ? `<div class="active-filters">${active.map((k) => esc(k === "q" ? `Search: “${state.q}”` : k === "service" ? labels[state[k]] : k === "status" ? statusLabels[state[k]] : k === "completeness" ? `Completeness ≥ ${state[k]}%` : k === "units" ? "Published units" : k === "billing" ? "Billing evidence" : "Portal evidence")).join(" · ")}</div>` : ""}${shown.length ? table(shown, priority) : '<div class="empty"><strong>No companies match these filters.</strong><button class="subtle-btn" id="empty-reset">Clear filters</button></div>'}<div class="pagination"><span>${filtered.length ? `Showing ${(page - 1) * 25 + 1}–${Math.min(page * 25, filtered.length)} of ${filtered.length}` : "0"} companies</span><div class="page-controls"><button class="page-btn" data-page="${page - 1}" ${page <= 1 ? "disabled" : ""} aria-label="Previous page">←</button><span>Page ${page} of ${pages}</span><button class="page-btn" data-page="${page + 1}" ${page >= pages ? "disabled" : ""} aria-label="Next page">→</button></div></div></section><p class="note">Fit scores reflect observed evidence, not purchase probability. Completeness shows how much of the scoring model is supported.<br>${priority ? "257 companies remain in Needs Research; they have not been disqualified." : "Directory-listed Berlin offices are distinct from verified Berlin service coverage."} <a href="?view=methodology" data-view="methodology">Understand the methodology →</a></p>`;
}
function overview() {
  const m = data.metrics;
  return `<div class="eyebrow">RESEARCH, WITH CONTEXT</div><div class="hero"><div><h1>A transparent view of the work.</h1><p class="intro">From a regional directory to a focused Berlin shortlist. Every result has a research status and every accepted business fact has a source.</p></div><a class="subtle-btn" href="Heidi_Berlin_AI.xlsx" download>↓ Download Excel</a></div>${metrics()}<div class="grid-two"><section class="panel content-pad"><h2>Qualification coverage</h2><p class="intro">292 companies, with room to learn more.</p><div class="stacked" role="img" aria-label="18 high priority, 17 medium priority, 257 need research"><span style="width:${(18 / 292) * 100}%;background:#4d8967"></span><span style="width:${(17 / 292) * 100}%;background:#97b3bd"></span><span style="flex:1;background:#e8dabb"></span></div><div class="legend"><span><i style="background:#4d8967"></i>High · 18</span><span><i style="background:#97b3bd"></i>Medium · 17</span><span><i style="background:#e8dabb"></i>Research · 257</span></div><p class="note">A research gap does not establish a poor business fit.</p></section><section class="panel content-pad"><h2>Website research</h2>${[
    ["AI enrichment completed", m.ai_completed],
    ["AI response failed validation", m.ai_failed],
    ["No saved homepage", m.no_saved_homepage],
    ["No website in directory", m.no_listed_website],
  ]
    .map(
      ([l, n]) =>
        `<div class="list-row"><span>${l}</span><strong>${n}</strong></div>`,
    )
    .join(
      "",
    )}</section></div><section class="panel"><div class="panel-head"><div><h2>Start with the strongest signals</h2><p>The first five companies in the shortlist.</p></div><a href="?view=priority" data-view="priority">View all 35 →</a></div>${table(
    sortCompanies(
      data.companies.filter((c) =>
        ["High Priority", "Medium Priority"].includes(c.priority),
      ),
      "recommended",
      true,
    ).slice(0, 5),
  )}</section><div class="grid-two"><section class="panel content-pad"><h2>Evidence, preserved</h2><div class="list-row"><span>Accepted field evidence items</span><strong>${m.field_evidence_validated}</strong></div><div class="list-row"><span>Companies with published unit figures</span><strong>${m.published_unit_counts}</strong></div><div class="list-row"><span>Questionable AI fields removed</span><strong>${m.ai_fields_removed_by_final_review}</strong></div><p class="note">Quotes were checked against saved page text. This is traceability verification, not a measured accuracy rate.</p></section><section class="panel content-pad"><h2>The scope</h2><p class="prose">These are <strong>292 directory-listed Berlin offices</strong> from a 381-record Berlin–Brandenburg directory baseline. Website research uses saved public pages. The dataset is not a complete census of Berlin property managers.</p><a href="?view=methodology" data-view="methodology">Read the method →</a></section></div>`;
}
function methodology() {
  const s = data.scoring;
  const names = {
    services: "Residential / WEG / rental relevance",
    portfolio: "Published managed portfolio",
    billing: "Heating / operating-cost billing",
    coverage: "Multiple-property evidence",
    digital: "Customer / owner portal",
  };
  return `<div class="eyebrow">HOW THE SHORTLIST WAS BUILT</div><div class="hero"><div><h1>Clear rules. Traceable evidence.</h1><p class="intro">Business fit, evidence completeness and contact verification answer different questions. We keep them separate.</p></div><a class="subtle-btn" href="Methodology_and_validation.md" download>↓ Download validation report</a></div><div class="grid-two"><section class="panel content-pad"><h2>What makes a strong fit?</h2><p class="intro">Five criteria. A maximum of 100 observed points.</p><div class="weights">${Object.entries(
    s.weights,
  )
    .map(
      ([k, n]) =>
        `<div class="weight-row"><span>${names[k]}</span><span class="weight-bar"><i style="width:${(n / 30) * 100}%"></i></span><strong>${n}</strong></div>`,
    )
    .join(
      "",
    )}</div><p class="note">Scoring configuration: ${esc(s.version)}.</p></section><section class="panel content-pad"><h2>Priority thresholds</h2><div class="list-row"><span>${badge("High Priority")}</span><strong>${s.high_threshold}+ points</strong></div><div class="list-row"><span>${badge("Medium Priority")}</span><strong>${s.medium_threshold}–${s.high_threshold - 1} points</strong></div><p class="prose">A ranked lead also needs a positive management-service signal, a Berlin office or supported Berlin service area, and at least <strong>${s.min_completeness}% evidence completeness</strong>. Incomplete records stay in Needs Research.</p><p class="note">A score is the observed lower bound; the upper bound includes points that remain unknown.</p></section></div><section class="panel content-pad"><h2>From source to shortlist</h2><p class="prose">Directory import → normalization → conservative deduplication → saved website pages → rule and AI extraction → field validation → deterministic scoring → Excel and website export.</p><div class="grid-two"><div><h3>Facts and interpretations</h3><p class="prose">Directory information establishes a listed identity and office address. Company pages provide published business claims. AI interprets page text and supplies verbatim quotes. Python validation and scoring apply reproducible rules. Source links and retrieval dates remain visible in company details.</p></div><div><h3>What unknown means</h3><p class="prose">A missing figure or service statement is not a negative finding. It receives no observed points, retains potential in the score upper bound, and lowers completeness. False is used only for explicit negative evidence.</p></div></div></section><div class="grid-two"><section class="panel content-pad"><h2>Portfolio scoring</h2>${[
    ...s.portfolio_bands,
  ]
    .reverse()
    .map(
      ([min, p], i, arr) =>
        `<div class="list-row"><span>${min === 0 ? "0" : i === arr.length - 1 ? `${num(min)}+` : `${num(min)}–${num(arr[i + 1][0] - 1)}`} published units</span><strong>${p} points</strong></div>`,
    )
    .join(
      "",
    )}<p class="note">Published company totals may include commercial units or locations outside Berlin. Approximate and lower-bound qualifiers are retained.</p></section><section class="panel content-pad"><h2>Limits worth understanding</h2><p class="prose">AI analysed saved homepages. Existing rule evidence can also come from service pages. Nine AI extractions failed, 43 records lacked a saved homepage, and 58 had no listed website. Directory contact roles and legal ownership of every website have not been independently verified.</p><p class="prose">Generic digital claims, address-only service coverage, misleading portfolio counts and unsupported quotes are rejected. An independent human accuracy study has not been conducted.</p><a href="Methodology_and_validation.md" download>Download the full validation report →</a></section></div>`;
}
function openCompany(id) {
  const c = data.companies.find((x) => x.company_id === id);
  if (!c) {
    if (!dialog.open) {
      document.querySelector("#detail-content").innerHTML =
        '<div class="detail-body"><button class="close" id="close">×</button><h2>Company not found</h2><p>This link does not match a record in the current dataset.</p></div>';
      dialog.showModal();
    }
    document.querySelector("#close").onclick = () => update({ company: "" });
    return;
  }
  returnFocus = document.activeElement;
  document.querySelector("#detail-content").innerHTML =
    `<div class="detail-head"><span class="eyebrow" style="margin:0">COMPANY INTELLIGENCE</span><button class="close" id="close" aria-label="Close company details">×</button></div><div class="detail-body">${badge(c.priority)}<h1 id="detail-title" style="margin-top:15px">${esc(c.company_name)}</h1><p class="intro">${esc(c.street_address || "Address not available")}</p><p>${c.website ? `<a href="${safe(c.website)}" target="_blank" rel="noopener noreferrer">${esc(c.domain)} ↗</a>` : "Website not listed"}</p>${c.address_validation_notes ? `<p class="note">Address note: ${esc(c.address_validation_notes)}</p>` : ""}<div class="detail-metrics"><div><span>Observed business fit</span><strong>${c.business_fit_score}<small>/100</small></strong></div><div><span>Evidence completeness</span><strong>${c.evidence_completeness}%</strong></div><div><span>Possible upper bound</span><strong>${c.score_upper_bound}</strong></div></div><p class="note">Confidence: ${esc(c.confidence)}. Scores reflect observed evidence, not purchase probability.</p><div class="section-space"><h2>Business facts</h2><div class="facts">${Object.entries(
      labels,
    )
      .map(
        ([key, label]) =>
          `<div class="fact"><span>${label}</span>${fmt(c[key])}${key === "managed_units" && c.managed_units != null ? ` <small>(${esc(c.managed_units_qualifier || "published count")}; company portfolio)</small>` : ""}</div>`,
      )
      .join(
        "",
      )}</div></div><section class="section-space"><h2>Why this score?</h2>${c.qualification_notes.map((n) => `<div class="list-row">${esc(n.replaceAll("True", "yes").replaceAll("False", "no"))}</div>`).join("")}</section><section class="section-space"><h2>Source evidence <span class="domain">${Object.keys(c.evidence).length} supported fields · expand to inspect the exact quote</span></h2>${
      Object.entries(c.evidence)
        .map(
          ([field, e]) =>
            `<details class="evidence"><summary>${esc(labels[field] || field)} · ${fmt(c[field])}</summary><blockquote class="quote" lang="de">${esc(e.quote)}</blockquote><a href="${safe(e.source_url)}" target="_blank" rel="noopener noreferrer">Open source ↗</a><div class="evidence-meta">Retrieved ${date(e.retrieved_at)} · ${esc(e.extraction_method)}</div><details class="section-space"><summary>Extraction audit</summary><p class="evidence-meta">Model: ${esc(e.model_name || "No model (rule extraction)")}<br>Prompt: ${esc(e.prompt_version || "Not applicable")}</p></details></details>`,
        )
        .join("") ||
      '<p class="prose">No qualifying business evidence has been retained. More research is needed.</p>'
    }</section><section class="section-space"><h2>Research status</h2><p class="prose">${esc(statusLabels[c.ai_enrichment_status] || "Not recorded")}<br>${esc(c.website_status)}</p><p class="note">Berlin office: ${c.berlin_office ? "directory-listed" : "not listed"}. Service coverage: ${fmt(c.Berlin_service_area)}.</p><a href="${safe(c.source_url)}" target="_blank" rel="noopener noreferrer">Original directory source ↗</a></section><section class="section-space"><h2>Public contact details</h2>${renderContacts(c.contacts)}</section></div>`;
  document.querySelector("#close").onclick = () => update({ company: "" });
  if (!dialog.open) dialog.showModal();
}
function render() {
  document
    .querySelectorAll("nav [data-view]")
    .forEach((a) =>
      a.classList.toggle("active", a.dataset.view === state.view),
    );
  document.querySelector("#breadcrumb").textContent = {
    priority: "Priority Leads",
    companies: "All Companies",
    overview: "Research Overview",
    methodology: "Methodology",
  }[state.view];
  app.innerHTML =
    state.view === "overview"
      ? overview()
      : state.view === "methodology"
        ? methodology()
        : list();
  if (state.company) openCompany(state.company);
  else if (dialog.open) {
    dialog.close();
    returnFocus?.focus();
  }
  bind();
}
function bind() {
  document.querySelectorAll("[data-view]").forEach(
    (a) =>
      (a.onclick = (e) => {
        e.preventDefault();
        navigate(a.dataset.view);
      }),
  );
  document
    .querySelectorAll("[data-goto]")
    .forEach(
      (a) => (a.onclick = () => navigate(a.dataset.goto, a.dataset.priority)),
    );
  document
    .querySelectorAll("[data-company]")
    .forEach((a) => (a.onclick = () => update({ company: a.dataset.company })));
  document
    .querySelectorAll("[data-tab]")
    .forEach(
      (a) => (a.onclick = () => update({ priority: a.dataset.tab, page: 1 })),
    );
  document.querySelectorAll("[data-page]").forEach(
    (a) =>
      (a.onclick = () => {
        update({ page: Number(a.dataset.page) });
        app
          .querySelector(".panel")
          ?.scrollIntoView({ behavior: "smooth", block: "start" });
      }),
  );
  document
    .querySelectorAll("[data-filter]")
    .forEach(
      (a) =>
        (a.onchange = () => update({ [a.dataset.filter]: a.value, page: 1 })),
    );
  document
    .querySelector("#sort")
    ?.addEventListener("change", (e) =>
      update({ sort: e.target.value, page: 1 }),
    );
  document
    .querySelector("#filter-toggle")
    ?.addEventListener("click", () => update({ filters: !state.filters }));
  for (const id of ["clear", "empty-reset"])
    document.querySelector("#" + id)?.addEventListener("click", reset);
  let timer;
  document.querySelector("#search")?.addEventListener("input", (e) => {
    clearTimeout(timer);
    const value = e.target.value,
      position = e.target.selectionStart;
    timer = setTimeout(() => {
      update({ q: value, page: 1 }, true);
      const input = document.querySelector("#search");
      input.focus();
      if (input.type !== "search") input.setSelectionRange(position, position);
    }, 250);
  });
}
dialog.addEventListener("cancel", (e) => {
  e.preventDefault();
  update({ company: "" });
});
dialog.addEventListener("click", (e) => {
  if (e.target === dialog && e.clientX < dialog.getBoundingClientRect().left)
    update({ company: "" });
});
window.addEventListener("popstate", () => {
  state = getState();
  render();
});
try {
  const response = await fetch("data.json");
  if (!response.ok) throw new Error("Research data could not be loaded.");
  data = await response.json();
  state = getState();
  document.querySelector("#date").textContent =
    `Research updated ${date(data.date)}`;
  render();
} catch (error) {
  app.innerHTML = `<div class="error"><h2>Research could not be loaded</h2><p>${esc(error.message)}</p><button onclick="location.reload()">Try again</button></div>`;
}
