// Teste da página de extração (extracao-web): leituras simuladas → bloco e JSON do plantão.
// Uso: node tests/pagina/teste_pagina.js <pagina.html>  → imprime {beds, json} em JSON.
// O teste em Python (tests/test_pagina.py) roda o motor sobre o JSON e compara com o bloco da página.
const { chromium } = require("playwright");
const path = require("path");

const ident = { leito: "7", nome: "PACIENTE FICTICIO DE TESTE", idade: "68", sexo: "M", unidade: "UTI ADULTO 2" };
const horas = ["7", "9", "11", "13", "15", "17", "19", "21", "23", "1", "3", "5"];
const sv = Object.assign({}, ident, {
  data_folha: "31/12/2025", pendencias: [],
  afericoes: horas.map((h, i) => ({
    hora: h, t: ["37,9", "38,2", "37,6", "37,1", "36,8", "36,6", "36,5", "36,7", "36,9", "36,6", "36,4", "36,5"][i],
    fr: String(22 - (i % 4)), fc: String(96 + i), pa: [{ pas: String(130 - 4 * i), pad: String(70 - i), pam: String(90 - i) }],
    dx: { "7": "212", "13": "65", "19": "154" }[h] || null, spo2: h === "23" ? "?" : (h === "3" ? "90" : "94"), suporte: "2L",
  })),
});
const bal = Object.assign({}, ident, {
  data_folha: "31/12/2025", pendencias: [], dieta: "SNE", evacuacao: "1x (++, pastosa)",
  balanco: [
    { coluna: "SNE", rotulo: null, celulas: horas.map((h) => ({ hora: h, ml: "50" })) },
    { coluna: "Endovenoso", rotulo: "NORA", celulas: horas.map((h) => ({ hora: h, ml: "3" })) },
    { coluna: "Dil.", rotulo: null, celulas: [{ hora: "10", ml: "100" }, { hora: "16", ml: "1.000" }] },
    { coluna: "Diurese", rotulo: null, celulas: horas.map((h) => ({ hora: h, ml: h === "3" ? "?" : "60" })) },
    { coluna: "Dreno/SVD", rotulo: "penrose", celulas: [{ hora: "7", ml: "20" }] },
  ],
  rodape: { ganhos_24h: "1.836", perdas_24h: "680", diurese_24h: "660", bh_24h: "+ 1.156" },
});
const rx = Object.assign({}, ident, {
  data_folha: "01/01/2026", pendencias: [], diagnostico: "PAC grave", alergias: "Dipirona", dieta_prescrita: "Enteral 50 ml/h",
  itens: [{ texto: "Tazocin — 4,5 g — EV — 6/6 h", bloco: "Infeccioso e Respiratório", revisar_ocr: true }],
  suspensos: [], procedimentos: [], recomendacoes: [], safety: "Nenhum risco imediato detectado com base nos dados fornecidos.",
});

(async () => {
  const browser = await chromium.launch(process.env.CHROMIUM ? { executablePath: process.env.CHROMIUM } : {});
  const page = await browser.newPage();
  await page.route(/^https?:/, (r) => r.abort());  // sem rede: fontes e pdf.js não carregam, e não precisam
  await page.goto("file://" + path.resolve(process.argv[2]), { waitUntil: "domcontentloaded" });
  const out = await page.evaluate(([sv, bal, rx]) => {
    const X = window.__extracao;
    X.S.pages = [
      { id: 1, label: "sv", status: "ok", data: { tipo: "sv", pacientes: [sv] } },
      { id: 2, label: "bal", status: "ok", data: { tipo: "balanco", pacientes: [bal] } },
      { id: 3, label: "rx", status: "ok", data: { tipo: "prescricao", pacientes: [rx] } },
    ];
    const rodar = () => {
      const R = X.assemble();
      return { beds: R.beds.map((b) => ({ texto: b.texto, pend: b.pend, flags: b.flags })), json: X.jsonOrdenado(X.plantaoJSON(R)) };
    };
    const h24 = rodar();
    document.querySelector('input[name="jan"][value="n"]').checked = true;
    return Object.assign(h24, { noturno: rodar() });
  }, [sv, bal, rx]);
  console.log(JSON.stringify(out));
  await browser.close();
})().catch((e) => { console.error(e); process.exit(1); });
