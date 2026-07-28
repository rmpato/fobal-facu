document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const group = btn.closest(".tabs-group");
    group.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    group.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    group.querySelector(`#${btn.dataset.tab}`).classList.add("active");
  });
});

// Marcar link activo en la navegación
const page = window.location.pathname.split("/").pop() || "index.html";
document.querySelectorAll("nav a[data-page]").forEach((link) => {
  if (link.dataset.page === page || (page === "" && link.dataset.page === "index.html")) {
    link.classList.add("active");
  }
});

// Link al repo en GitHub Pages
const repoLink = document.getElementById("repo-link");
if (repoLink) {
  const host = window.location.hostname;
  if (host.endsWith(".github.io")) {
    const user = host.replace(".github.io", "");
    const parts = window.location.pathname.split("/").filter(Boolean);
    const repo = parts[0] || `${user}.github.io`;
    repoLink.href = `https://github.com/${user}/${repo}`;
  } else {
    repoLink.href = "https://github.com/rmpato/fobal-facu";
  }
}
