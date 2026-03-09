const API_BASE = "http://localhost:4000/api";

export async function simulateCareer(payload) {
  const response = await fetch(`${API_BASE}/simulate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || "Simulation request failed");
  }

  return response.json();
}
