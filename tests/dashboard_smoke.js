// Ejecuta el JS del dashboard con un DOM simulado y comprueba que se dibuja bien.
// Uso: node tests/dashboard_smoke.js <dashboard.html> <light|dark>
const fs = require("fs"), vm = require("vm");
const [, , ruta, tema] = process.argv;
const html = fs.readFileSync(ruta, "utf8");
const datos = html.match(/<script id="datos" type="application\/json">([\s\S]*?)<\/script>/)[1];
const js = html.match(/<script>([\s\S]*?)<\/script>/)[1];
const errores = [];

function fake(tag) {
  const e = {
    tagName: (tag || "div").toUpperCase(), children: [], attrs: {}, dataset: {}, style: {}, _html: "", _text: "",
    setAttribute(k, v) {
      this.attrs[k] = String(v);
      if (/undefined|NaN/.test(String(v))) errores.push(`atributo ${k}=${v}`);
    },
    getAttribute(k) { return this.attrs[k] ?? null; },
    removeAttribute(k) { delete this.attrs[k]; },
    appendChild(c) { this.children.push(c); return c; },
    insertAdjacentHTML(_, h) { this.innerHTML = this._html + h; },
    getBoundingClientRect() { return {left: 0, top: 0, bottom: 0, width: 10, height: 10}; },
    addEventListener() {}, querySelector() { return null; }, closest() { return null; },
    set innerHTML(h) {
      this._html = h;
      if (h === "") this.children = [];
      const m = h.match(/.{0,60}(undefined|NaN|\[object Object\]).{0,30}/);
      if (m) errores.push("HTML con " + m[0]);
    },
    get innerHTML() { return this._html; },
    set textContent(v) { this._text = String(v); if (/undefined|NaN/.test(this._text)) errores.push("texto: " + v); },
    get textContent() { return this._text; },
  };
  return e;
}
const els = {};
const raiz = fake("html");
const document = {
  getElementById(id) { if (id === "datos") return {textContent: datos}; return els[id] ||= fake("div"); },
  createElement: fake, createElementNS: (_, t) => fake(t), addEventListener() {},
  documentElement: raiz, title: "",
};
const location = {hash: ""};
const window = {
  addEventListener() {}, scrollTo() {}, innerWidth: 1920, innerHeight: 1080,
  matchMedia: () => ({matches: tema === "dark", addEventListener() {}, addListener() {}}),
};
const ctx = {document, location, window, matchMedia: window.matchMedia,
             localStorage: {getItem() { return null; }, setItem() {}}, console};
vm.createContext(ctx);
vm.runInContext(js + "\n;globalThis.__ruta = ruta; globalThis.__ORDEN = ORDEN;", ctx);

function recorrer(el, f) { f(el); (el.children || []).forEach(c => recorrer(c, f)); }
function luminancia(hex) {
  const c = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map(v => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function contraste(a, b) {
  const [l1, l2] = [luminancia(a), luminancia(b)].sort((x, y) => y - x);
  return (l1 + 0.05) / (l2 + 0.05);
}

let celdas = 0, barrasPareadas = 0;
for (const slug of ctx.__ORDEN) {
  location.hash = "#" + slug;
  ctx.__ruta();
  recorrer(els.vista, el => {
    // Mapa de calor: cada casilla con fondo y texto en hex, y contraste suficiente
    for (const m of el._html.matchAll(/<td style="background:(#[0-9a-f]{6});color:(#[0-9a-f]{6})"/g)) {
      celdas++;
      const r = contraste(m[1], m[2]);
      if (r < 4.5) errores.push(`${slug}: casilla ${m[1]} con texto ${m[2]} contraste ${r.toFixed(2)}`);
    }
    // Barras segmento/total: el valor va pegado a la barra del segmento, no a la más larga
    if (el.attrs.class === "pareadas") {
      for (const g of el.children.filter(c => c.tagName === "G")) {
        const [pSeg] = g.children.filter(c => c.tagName === "PATH");
        const valor = g.children.find(c => c.tagName === "TEXT" && c.attrs.class === "t-value");
        const fin = pSeg.attrs.d ? Number(pSeg.attrs.d.match(/Q([\d.]+),/)[1]) : null;
        if (fin !== null && Math.abs(Number(valor.attrs.x) - (fin + 6)) > 0.5) {
          errores.push(`${slug}: valor en x=${valor.attrs.x}, la barra del segmento acaba en ${fin}`);
        }
        barrasPareadas++;
      }
    }
  });
}
if (celdas === 0) errores.push("el mapa de calor no tiene casillas con colores en hex");
if (barrasPareadas === 0) errores.push("no se ha dibujado ninguna barra segmento/total");
if (errores.length) { console.log(errores.slice(0, 15).join("\n")); process.exit(1); }
console.log(`OK ${tema}: ${ctx.__ORDEN.length} vistas, ${celdas} casillas, ${barrasPareadas} barras pareadas`);
