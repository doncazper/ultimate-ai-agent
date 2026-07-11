const STORAGE_KEY = "uaa.control-center.render-reviews.v1";

const state = {
  manifest: null,
  renders: [],
  filtered: [],
  currentId: null,
  activeSet: "target-v1",
  query: "",
  versionByRender: {},
  compareByRender: {},
  reviews: loadReviews(),
};

const els = Object.fromEntries([
  "search", "setFilters", "renderList", "approvedCount", "reviewCount",
  "progressBar", "exportReviews", "importReviews", "renderId",
  "renderCategory", "surfaceTitle", "surfacePurpose", "versionSelect",
  "compareVersion", "openImage", "truthText", "imageStage", "renderImage",
  "comparePanel", "compareImage", "currentVersionTag", "compareVersionTag",
  "imageError", "previousRender",
  "nextRender", "positionText", "reviewSurface", "saveState",
  "statusControl", "critiqueText", "saveReview", "metaId", "metaSet",
  "metaRoute", "metaVersion", "historyList",
].map((id) => [id, document.getElementById(id)]));

boot().catch((error) => {
  document.body.innerHTML = `<main class="fatal-error"><h1>Render review could not load</h1><p>${escapeHtml(error.message)}</p></main>`;
});

async function boot() {
  const response = await fetch("renders.json", { cache: "no-store" });
  if (!response.ok) throw new Error(`Manifest request failed with ${response.status}.`);
  state.manifest = await response.json();
  state.renders = [...state.manifest.renders].sort((a, b) => a.order - b.order);
  bindEvents();
  renderSetFilters();
  applyFilters();
}

function bindEvents() {
  els.search.addEventListener("input", (event) => {
    state.query = event.target.value.trim().toLowerCase();
    applyFilters();
  });
  els.previousRender.addEventListener("click", () => move(-1));
  els.nextRender.addEventListener("click", () => move(1));
  els.versionSelect.addEventListener("change", () => {
    saveTextIfDirty();
    state.versionByRender[state.currentId] = els.versionSelect.value;
    renderCurrent();
  });
  els.compareVersion.addEventListener("click", () => {
    state.compareByRender[state.currentId] = !state.compareByRender[state.currentId];
    renderCurrent();
  });
  els.statusControl.addEventListener("click", (event) => {
    const button = event.target.closest("button[data-status]");
    if (!button) return;
    updateDraft({ status: button.dataset.status });
    renderReviewControls();
    renderList();
    updateProgress();
  });
  els.critiqueText.addEventListener("input", () => {
    els.saveState.textContent = "Unsaved changes";
    els.saveState.classList.add("dirty");
  });
  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      const prefix = button.dataset.prompt;
      const current = els.critiqueText.value;
      els.critiqueText.value = current ? `${current.trim()}\n${prefix}` : prefix;
      els.critiqueText.focus();
      els.critiqueText.setSelectionRange(els.critiqueText.value.length, els.critiqueText.value.length);
      els.saveState.textContent = "Unsaved changes";
      els.saveState.classList.add("dirty");
    });
  });
  els.saveReview.addEventListener("click", saveCurrentReview);
  els.exportReviews.addEventListener("click", exportReviews);
  els.importReviews.addEventListener("change", importReviews);
  window.addEventListener("keydown", (event) => {
    if (event.target.matches("input, textarea, select")) return;
    if (event.key === "ArrowLeft") move(-1);
    if (event.key === "ArrowRight") move(1);
  });
}

function renderSetFilters() {
  els.setFilters.replaceChildren();
  state.manifest.sets.forEach((set) => {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = set.label;
    button.title = set.description;
    button.setAttribute("aria-pressed", String(state.activeSet === set.id));
    button.addEventListener("click", () => {
      state.activeSet = set.id;
      renderSetFilters();
      applyFilters();
    });
    els.setFilters.append(button);
  });
}

function applyFilters() {
  state.filtered = state.renders.filter((render) => {
    const inSet = render.set === state.activeSet;
    const haystack = `${render.id} ${render.surface} ${render.category} ${render.purpose}`.toLowerCase();
    return inSet && (!state.query || haystack.includes(state.query));
  });
  if (!state.filtered.some((render) => render.id === state.currentId)) {
    state.currentId = state.filtered[0]?.id ?? null;
  }
  renderList();
  renderCurrent();
  updateProgress();
}

function renderList() {
  els.renderList.replaceChildren();
  let lastCategory = null;
  state.filtered.forEach((render, index) => {
    if (render.category !== lastCategory) {
      const heading = document.createElement("div");
      heading.className = "render-group";
      heading.textContent = render.category;
      els.renderList.append(heading);
      lastCategory = render.category;
    }
    const latestVersionId = render.versions.at(-1).id;
    const review = reviewFor(render.id, latestVersionId);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "render-link";
    button.setAttribute("aria-current", String(render.id === state.currentId));
    button.innerHTML = `
      <span class="render-number">${String(index + 1).padStart(2, "0")}</span>
      <span class="render-name"><strong>${escapeHtml(render.surface)}</strong><span>${escapeHtml(render.id)}</span></span>
      <span class="review-dot ${review.status}" title="${statusLabel(review.status)}"></span>`;
    button.addEventListener("click", () => {
      saveTextIfDirty();
      state.currentId = render.id;
      renderList();
      renderCurrent();
    });
    els.renderList.append(button);
  });
}

function renderCurrent() {
  const render = currentRender();
  if (!render) {
    els.surfaceTitle.textContent = "No matching renders";
    els.surfacePurpose.textContent = "Clear search or choose another render set.";
    els.renderImage.removeAttribute("src");
    els.imageError.hidden = false;
    return;
  }
  const versionId = state.versionByRender[render.id] ?? render.versions.at(-1).id;
  const version = render.versions.find((item) => item.id === versionId) ?? render.versions.at(-1);
  const versionIndex = render.versions.findIndex((item) => item.id === version.id);
  const previousVersion = versionIndex > 0 ? render.versions[versionIndex - 1] : null;
  const compareEnabled = Boolean(previousVersion && state.compareByRender[render.id]);
  state.versionByRender[render.id] = version.id;

  els.renderId.textContent = render.id;
  els.renderCategory.textContent = render.category;
  els.surfaceTitle.textContent = render.surface;
  els.surfacePurpose.textContent = render.purpose;
  els.truthText.textContent = render.truth;
  els.reviewSurface.textContent = render.surface;
  els.metaId.textContent = render.id;
  els.metaSet.textContent = setLabel(render.set);
  els.metaRoute.textContent = render.route;
  els.metaVersion.textContent = version.label;
  els.positionText.textContent = `${state.filtered.findIndex((item) => item.id === render.id) + 1} of ${state.filtered.length}`;

  els.versionSelect.replaceChildren();
  render.versions.forEach((item) => {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = item.label;
    option.selected = item.id === version.id;
    els.versionSelect.append(option);
  });

  els.renderImage.alt = `${render.surface} ${version.label} Control Center design render`;
  els.imageError.hidden = true;
  els.renderImage.hidden = false;
  els.renderImage.onload = () => {
    els.renderImage.hidden = false;
    els.imageError.hidden = true;
  };
  els.renderImage.onerror = () => {
    els.renderImage.hidden = true;
    els.imageError.hidden = false;
  };
  els.renderImage.src = `${version.image}?v=${encodeURIComponent(state.manifest.updated)}`;
  els.openImage.href = version.image;
  els.compareVersion.hidden = !previousVersion;
  els.compareVersion.setAttribute("aria-pressed", String(compareEnabled));
  els.compareVersion.textContent = compareEnabled ? "Close compare" : "Compare";
  els.imageStage.classList.toggle("compare-mode", compareEnabled);
  els.currentVersionTag.hidden = !compareEnabled;
  els.currentVersionTag.textContent = version.label;
  els.comparePanel.hidden = !compareEnabled;
  if (compareEnabled) {
    els.compareVersionTag.textContent = previousVersion.label;
    els.compareImage.alt = `${render.surface} ${previousVersion.label} comparison render`;
    els.compareImage.src = `${previousVersion.image}?v=${encodeURIComponent(state.manifest.updated)}`;
  } else {
    els.compareImage.removeAttribute("src");
  }
  renderReviewControls();
  renderHistory(render);
}

function renderReviewControls() {
  const render = currentRender();
  if (!render) return;
  const review = reviewFor(render.id, state.versionByRender[render.id]);
  els.statusControl.querySelectorAll("button[data-status]").forEach((button) => {
    button.setAttribute("aria-checked", String(button.dataset.status === review.status));
  });
  els.critiqueText.value = review.notes ?? "";
  els.saveState.textContent = review.updatedAt ? `Saved ${formatTime(review.updatedAt)}` : "Saved locally";
  els.saveState.classList.remove("dirty");
}

function renderHistory(render) {
  els.historyList.replaceChildren();
  [...render.versions].reverse().forEach((version) => {
    const item = document.createElement("div");
    item.className = "history-item";
    item.innerHTML = `<strong>${escapeHtml(version.label)}</strong><span>${version.id === state.versionByRender[render.id] ? "Viewing" : "Available"}</span>`;
    els.historyList.append(item);
  });
}

function updateDraft(patch) {
  const render = currentRender();
  if (!render) return;
  const versionId = state.versionByRender[render.id] ?? render.versions.at(-1).id;
  const key = reviewKey(render.id, versionId);
  state.reviews[key] = { ...reviewFor(render.id, versionId), ...patch, updatedAt: new Date().toISOString() };
  persistReviews();
}

function saveCurrentReview() {
  updateDraft({ notes: els.critiqueText.value.trim() });
  const render = currentRender();
  const versionId = state.versionByRender[render.id] ?? render.versions.at(-1).id;
  els.saveState.textContent = `Saved ${formatTime(reviewFor(render.id, versionId).updatedAt)}`;
  els.saveState.classList.remove("dirty");
  renderList();
  updateProgress();
}

function saveTextIfDirty() {
  if (!els.saveState.classList.contains("dirty") || !state.currentId) return;
  updateDraft({ notes: els.critiqueText.value.trim() });
}

function move(delta) {
  if (!state.filtered.length) return;
  saveTextIfDirty();
  const index = state.filtered.findIndex((render) => render.id === state.currentId);
  const nextIndex = (index + delta + state.filtered.length) % state.filtered.length;
  state.currentId = state.filtered[nextIndex].id;
  renderList();
  renderCurrent();
  els.renderList.querySelector('[aria-current="true"]')?.scrollIntoView({ block: "nearest" });
}

function updateProgress() {
  const setRenders = state.renders.filter((render) => render.set === state.activeSet);
  const reviewed = setRenders.filter((render) => {
    const review = reviewFor(render.id, render.versions.at(-1).id);
    return review.status !== "draft" || Boolean(review.notes);
  }).length;
  const approved = setRenders.filter((render) => reviewFor(render.id, render.versions.at(-1).id).status === "approved").length;
  const ratio = setRenders.length ? reviewed / setRenders.length : 0;
  els.approvedCount.textContent = `${approved} approved`;
  els.reviewCount.textContent = `${reviewed} of ${setRenders.length} reviewed`;
  els.progressBar.style.width = `${Math.round(ratio * 100)}%`;
}

function exportReviews() {
  saveTextIfDirty();
  const payload = {
    schema: "uaa.control_center.render_review_export.v1",
    exportedAt: new Date().toISOString(),
    manifestUpdated: state.manifest.updated,
    reviews: state.reviews,
  };
  const url = URL.createObjectURL(new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `control-center-render-reviews-${new Date().toISOString().slice(0, 10)}.json`;
  anchor.click();
  URL.revokeObjectURL(url);
}

async function importReviews(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  try {
    const payload = JSON.parse(await file.text());
    if (payload.schema !== "uaa.control_center.render_review_export.v1" || typeof payload.reviews !== "object") {
      throw new Error("Unsupported review export format.");
    }
    state.reviews = { ...state.reviews, ...payload.reviews };
    persistReviews();
    renderList();
    renderCurrent();
    updateProgress();
  } catch (error) {
    window.alert(`Could not import reviews: ${error.message}`);
  } finally {
    event.target.value = "";
  }
}

function currentRender() {
  return state.renders.find((render) => render.id === state.currentId) ?? null;
}

function reviewFor(id, versionId) {
  return state.reviews[reviewKey(id, versionId)] ?? state.reviews[id] ?? { status: "draft", notes: "", updatedAt: null };
}

function reviewKey(id, versionId) {
  return `${id}:${versionId ?? "latest"}`;
}

function loadReviews() {
  try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) ?? {}; }
  catch { return {}; }
}

function persistReviews() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(state.reviews));
}

function setLabel(id) {
  return state.manifest.sets.find((set) => set.id === id)?.label ?? id;
}

function statusLabel(status) {
  return ({ draft: "Draft", "needs-revision": "Needs revision", approved: "Approved", superseded: "Superseded" })[status] ?? status;
}

function formatTime(value) {
  return new Intl.DateTimeFormat(undefined, { hour: "numeric", minute: "2-digit" }).format(new Date(value));
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
}
