document.addEventListener("DOMContentLoaded", () => {
  const status = document.getElementById("demandStatus");
  const total = document.getElementById("totalDemand");
  const list = document.getElementById("commodityList");
  let chart;

  function renderSelections(selections) {
    const entries = Object.entries(selections);
    list.innerHTML = entries.length ? entries.map(([name, count]) =>
      `<div class="selection-item"><span>${name}</span><strong>${count}</strong></div>`
    ).join("") : `<p class="muted">No categories added.</p>`;
  }

  document.getElementById("energyForm").addEventListener("submit", async event => {
    event.preventDefault();
    const button = event.submitter;
    AppUI.busy(button, true, "Adding…");
    try {
      const response = await fetch("/calculate", {method:"POST", body:new FormData(event.currentTarget)});
      const data = await AppUI.json(response);
      total.textContent = `${data.total_demand.toLocaleString(undefined,{maximumFractionDigits:1})} kWh/year`;
      renderSelections(data.selections);
      AppUI.setStatus(status, "Demand profile updated.", "success");
    } catch (error) { AppUI.setStatus(status, error.message, "error"); }
    finally { AppUI.busy(button, false); }
  });

  async function refreshChart() {
    try {
      const data = await AppUI.json(await fetch("/get_chart_data"));
      chart?.destroy();
      chart = new Chart(document.getElementById("demandChart"), {
        type:"line",
        data:{labels:data.labels,datasets:[{label:"Electricity demand",data:data.values,borderColor:"#1457d9",backgroundColor:"rgba(33,197,217,.13)",fill:true,pointRadius:0,borderWidth:2}]},
        options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},scales:{x:{ticks:{maxTicksLimit:8}},y:{beginAtZero:true}}}
      });
    } catch (error) { AppUI.setStatus(status, error.message, "error"); }
  }
  document.getElementById("generateChartButton").addEventListener("click", refreshChart);
  document.getElementById("generateJSONButton").addEventListener("click", async event => {
    const button = event.currentTarget;
    AppUI.busy(button, true, "Generating input…");
    try {
      const data = await AppUI.json(await fetch("/generate_json", {method:"POST"}));
      window.location.href = data.next_url;
    } catch (error) { AppUI.setStatus(status, error.message, "error"); AppUI.busy(button,false); }
  });
  refreshChart();
});

