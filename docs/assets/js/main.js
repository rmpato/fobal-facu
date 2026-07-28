document.querySelectorAll(".tab-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    const group = btn.closest(".tabs-group");
    group.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
    group.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
    btn.classList.add("active");
    group.querySelector(`#${btn.dataset.tab}`).classList.add("active");
  });
});
