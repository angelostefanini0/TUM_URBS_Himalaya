document.addEventListener("DOMContentLoaded", () => {
  const map = L.map("map").setView([28.2, 82.0], 5);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors"
  }).addTo(map);

  const latitude = document.getElementById("latitude");
  const longitude = document.getElementById("longitude");
  const location = document.getElementById("location");
  const status = document.getElementById("resourceStatus");
  const downloads = document.getElementById("resourceDownloads");
  const next = document.getElementById("nextButtonMap");
  let marker;

  function place(lat, lon) {
    latitude.value = Number(lat).toFixed(6);
    longitude.value = Number(lon).toFixed(6);
    marker = marker ? marker.setLatLng([lat, lon]) : L.marker([lat, lon]).addTo(map);
  }

  map.on("click", async event => {
    place(event.latlng.lat, event.latlng.lng);
    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${event.latlng.lat}&lon=${event.latlng.lng}`);
      const data = await response.json();
      location.value = data.display_name || "";
    } catch (_) {}
  });

  document.getElementById("searchButton").addEventListener("click", async () => {
    if (!location.value.trim()) return AppUI.setStatus(status, "Enter a location to search.", "error");
    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(location.value)}`);
      const data = await response.json();
      if (!data.length) throw new Error("Location not found.");
      place(data[0].lat, data[0].lon);
      map.setView([data[0].lat, data[0].lon], 11);
    } catch (error) { AppUI.setStatus(status, error.message, "error"); }
  });

  document.getElementById("startButton").addEventListener("click", async event => {
    const button = event.currentTarget;
    AppUI.busy(button, true, "Fetching hourly profiles…");
    try {
      const response = await fetch("/api/renewables", {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({lat: latitude.value, lon: longitude.value})
      });
      const data = await AppUI.json(response);
      AppUI.setStatus(status, data.warning || "Solar, wind and hydro profiles are ready.", data.warning ? "info" : "success");
      document.getElementById("downloadPVButton").href = `/downloads/${data.pv_json_file}`;
      document.getElementById("downloadWindButton").href = `/downloads/${data.wind_json_file}`;
      downloads.hidden = false;
      next.disabled = false;
    } catch (error) { AppUI.setStatus(status, error.message, "error"); }
    finally { AppUI.busy(button, false); }
  });

  next.addEventListener("click", async () => {
    AppUI.busy(next, true, "Preparing profiles…");
    try {
      await AppUI.json(await fetch("/transform_files", {method:"POST"}));
      await AppUI.json(await fetch("/reset_total_series", {method:"POST"}));
      window.location.href = "/demand";
    } catch (error) {
      AppUI.setStatus(status, error.message, "error");
      AppUI.busy(next, false);
    }
  });

  const dialog = document.getElementById("dischargeModal");
  document.getElementById("getDischarge").addEventListener("click", () => dialog.showModal());
});

