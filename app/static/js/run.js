document.getElementById("urbsRunForm")?.addEventListener("submit", event => {
  const button = event.submitter;
  button.disabled = true;
  button.textContent = "Running optimization…";
  document.getElementById("runLoading").hidden = false;
});
