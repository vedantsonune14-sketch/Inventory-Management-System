const API = "http://127.0.0.1:5000/api/products";
const LOW_STOCK_LIMIT = 5;

const tableBody = document.getElementById("tableBody");
const msgBox = document.getElementById("message");
const banner = document.getElementById("lowStockBanner");
const searchBox = document.getElementById("search");

// Escape text to prevent HTML injection (XSS)
const esc = (s) => String(s).replace(/[&<>"']/g, c =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

let msgTimer;
function showMessage(text, ok = true) {
  msgBox.textContent = text;
  msgBox.className = "message " + (ok ? "ok" : "err");
  clearTimeout(msgTimer);
  msgTimer = setTimeout(() => msgBox.classList.add("hidden"), 3500);
}

// Helper for every request: throws an Error with the server's message on failure
async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || "Something went wrong");
  return data;
}

// ---- READ + SEARCH ----
async function loadProducts() {
  try {
    const q = searchBox.value.trim();
    const products = await request(`${API}?q=${encodeURIComponent(q)}`);
    renderTable(products, q);
    await loadLowStock();
  } catch (e) {
    showMessage("Cannot reach server. Is Flask running? " + e.message, false);
  }
}

function renderTable(products, q) {
  if (products.length === 0) {
    tableBody.innerHTML = `<tr><td colspan="6" class="empty">
      ${q ? `No products found for "${esc(q)}"` : "No products yet. Add one above."}</td></tr>`;
    return;
  }
  tableBody.innerHTML = products.map(p => {
    const low = p.quantity <= LOW_STOCK_LIMIT;
    const id = esc(p.product_id);
    return `<tr class="${low ? "low" : ""}">
      <td>${id}</td>
      <td>${esc(p.name)}</td>
      <td>${esc(p.category)}</td>
      <td>${p.quantity}${low ? '<span class="badge">LOW</span>' : ""}</td>
      <td>${p.price.toFixed(2)}</td>
      <td>
        <button class="small" onclick="changeStock('${id}', 1)">+1</button>
        <button class="small" onclick="changeStock('${id}', -1)">−1</button>
        <button class="small" onclick="editProduct('${id}', ${p.quantity}, ${p.price})">Edit</button>
        <button class="small danger" onclick="removeProduct('${id}')">Delete</button>
      </td></tr>`;
  }).join("");
}

async function loadLowStock() {
  const items = await request(`${API}/low-stock`);
  if (items.length) {
    banner.textContent = "⚠ Low stock: " + items.map(i => `${i.name} (${i.quantity})`).join(", ");
    banner.classList.remove("hidden");
  } else {
    banner.classList.add("hidden");
  }
}

// ---- CREATE ----
document.getElementById("addForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    product_id: document.getElementById("product_id").value,
    name: document.getElementById("name").value,
    category: document.getElementById("category").value,
    quantity: document.getElementById("quantity").value,
    price: document.getElementById("price").value,
  };
  try {
    await request(API, { method: "POST", body: JSON.stringify(body) });
    e.target.reset();
    showMessage("Product added successfully");
    loadProducts();
  } catch (err) { showMessage(err.message, false); }
});

// ---- UPDATE ----
async function changeStock(id, change) {
  try {
    await request(`${API}/${encodeURIComponent(id)}/stock`,
      { method: "PATCH", body: JSON.stringify({ change }) });
    loadProducts();
  } catch (err) { showMessage(err.message, false); }
}

async function editProduct(id, oldQty, oldPrice) {
  const qty = prompt("New quantity:", oldQty);
  if (qty === null) return;
  const price = prompt("New price:", oldPrice);
  if (price === null) return;
  try {
    await request(`${API}/${encodeURIComponent(id)}`,
      { method: "PUT", body: JSON.stringify({ quantity: qty, price }) });
    showMessage("Product updated");
    loadProducts();
  } catch (err) { showMessage(err.message, false); }
}

// ---- DELETE ----
async function removeProduct(id) {
  if (!confirm(`Delete product ${id}?`)) return;
  try {
    await request(`${API}/${encodeURIComponent(id)}`, { method: "DELETE" });
    showMessage("Product deleted");
    loadProducts();
  } catch (err) { showMessage(err.message, false); }
}

// ---- LIVE SEARCH (waits 250ms after you stop typing) ----
let timer;
searchBox.addEventListener("input", () => {
  clearTimeout(timer);
  timer = setTimeout(loadProducts, 250);
});

loadProducts();