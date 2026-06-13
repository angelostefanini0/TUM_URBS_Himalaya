document.addEventListener("DOMContentLoaded", () => {
  const library = document.getElementById("technologyLibrary");
  const zone = document.getElementById("dropZone");
  const status = document.getElementById("processStatus");
  const selected = new Set();
  const endpoints = {hydro:"/process_hydro",solar:"/process_solar",wind:"/process_wind",gasplant:"/process_gasplant",ligniteplant:"/process_ligniteplant"};

  async function selectTechnology(id, source) {
    if (selected.has(id)) return;
    try {
      const data = await AppUI.json(await fetch(endpoints[id], {
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({action:id})
      }));
      selected.add(id);
      zone.classList.add("has-items");
      zone.querySelector("p")?.remove();
      const item = document.createElement("div");
      item.className = "selected-tech";
      item.innerHTML = `<span>${data.process}</span><small>Selected</small>`;
      zone.appendChild(item);
      source.disabled = true;
      AppUI.setStatus(status, `${data.process} added to the scenario.`, "success");
    } catch (error) { AppUI.setStatus(status, error.message, "error"); }
  }

  library.querySelectorAll("[data-technology]").forEach(card => {
    card.addEventListener("click", () => selectTechnology(card.dataset.technology, card));
    card.addEventListener("dragstart", event => event.dataTransfer.setData("text/plain", card.dataset.technology));
  });
  zone.addEventListener("dragover", event => { event.preventDefault(); zone.classList.add("is-over"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("is-over"));
  zone.addEventListener("drop", event => {
    event.preventDefault(); zone.classList.remove("is-over");
    const id = event.dataTransfer.getData("text/plain");
    const source = library.querySelector(`[data-technology="${id}"]`);
    if (source) selectTechnology(id, source);
  });
  document.getElementById("technologySearch").addEventListener("input", event => {
    const query = event.target.value.toLowerCase();
    library.querySelectorAll(".technology-card").forEach(card => card.hidden = !card.textContent.toLowerCase().includes(query));
  });

  const dialog = document.getElementById("customProcessDialog");
  document.getElementById("openCustomProcess").addEventListener("click", () => dialog.showModal());
  document.getElementById("customProcessForm").addEventListener("submit", async event => {
    event.preventDefault();
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const data = await AppUI.json(await fetch("/save_process_data", {
        method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)
      }));
      dialog.close();
      zone.classList.add("has-items"); zone.querySelector("p")?.remove();
      zone.insertAdjacentHTML("beforeend", `<div class="selected-tech"><span>${data.process}</span><small>Custom</small></div>`);
      AppUI.setStatus(status, `${data.process} saved. Add its commodity relationships before scientific use.`, "success");
    } catch (error) { AppUI.setStatus(status, error.message, "error"); }
  });

  document.getElementById("nextButtonProcess").addEventListener("click", async event => {
    const button = event.currentTarget; AppUI.busy(button,true,"Preparing URBS inputs…");
    try {
      await AppUI.json(await fetch("/move_files",{method:"POST"}));
      window.location.href="/runurbs";
    } catch(error){AppUI.setStatus(status,error.message,"error");AppUI.busy(button,false);}
  });
});

