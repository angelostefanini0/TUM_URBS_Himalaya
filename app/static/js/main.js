window.AppUI = {
  setStatus(element, message, type = "info") {
    element.hidden = false;
    element.className = `status-box ${type === "error" ? "is-error" : type === "success" ? "is-success" : ""}`;
    element.textContent = message;
  },
  async json(response) {
    const data = await response.json().catch(() => ({}));
    if (!response.ok || data.status === "failure") {
      throw new Error(data.error || `Request failed (${response.status})`);
    }
    return data;
  },
  busy(button, active, label = "Working…") {
    if (active) {
      button.dataset.label = button.textContent;
      button.textContent = label;
      button.disabled = true;
    } else {
      button.textContent = button.dataset.label || button.textContent;
      button.disabled = false;
    }
  }
};

document.querySelectorAll("[data-close-dialog]").forEach(button => {
  button.addEventListener("click", () => button.closest("dialog").close());
});

