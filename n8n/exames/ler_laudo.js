'use strict';
/*
 * ler_laudo.js — lê o texto de um laudo do Instituto de Biomedicina do ABC (Banco de Resultados), do jeito que o
 * nó "Extract from File" (PDF) do n8n entrega, e devolve cada valor preso à DATA DA COLETA do bloco onde ele está.
 * A data de liberação vem junto só como informação; nunca é âncora.
 *
 * Mesmo código no nó "Ler laudo" do fluxo "Exames - Banco de Resultados" e nos testes (node).
 * Bloco = linhas até "Data da Coleta: dd/mm/aaaa hh:mm:ss Resultado liberado em: ...".
 * Formatos vistos (88 laudos reais, 12/11/2026): valor na linha do nome (bioquímica), "rótulo : valor" (gaso,
 * coagulação, painel cardíaco, culturas), hemograma em tabela, antibiograma (droga + "CIM S/I/R").
 */

// a hora da coleta às vezes falta ("Data da Coleta: 02/11/2026 Resultado liberado em: ...")
const RE_COLETA = /^Data da Coleta:\s*(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?(?:\s+Resultado liberado em:\s*(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?)?/i;
const RE_LIBERADO = /^Resultado liberado em:\s*(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2})(?::(\d{2}))?)?/i;
const RE_META = /^(Material de Coleta|Amostra|M[ée]todo)\s*:/i;
const RE_CAMPO = /^(Material de Coleta|Amostra|M[ée]todo|V\.\s?R\.|Valor(?:es)? de Refer[êe]ncia|Coment[áa]rio|Observa[çc](?:[ãa]o|[õo]es)|Nota)\s*:\s*(.*)$/i;
const RE_ROTULO = /^([^:]*?[^\s.:])[\s.]*:\s*(.*)$/;
const RE_TITULO_VALOR = /^(.+?)\s+([<>]=?\s*)?(\d[\d.]*(?:,\d+)?)(?:\s+([^\s]*[a-zμµ%/][^\s]*))?$/;
const RE_REF_ROTULO = /^(Normal|V\.?\s*R\.?|Refer[êe]ncia|Sens[íi]vel|Resistente|Intermedi[áa]rio)$/i;
const RE_DESCARTE = /^(Lote|Validade)\b/i;
const RE_CABECALHO = /^(Eritrograma|Leucograma|Plaquetas|Exame (F[íi]sico|Qu[íi]mico|Microsc[óo]pico)|CALCULADO|SERINGA|MULHER HOMEM|Valores de Refer[êe]ncia|Antibacterianos\b.*)$/i;
const RE_CULTURA = /CULTURA|SWAB|URINA C\/|ANTIBIOGRAMA|INIBIT|DIFFICILE/i;
const UNIDADES_SOLTAS = new Set(['fL', 'fl', 'pg', 'mmHg', 'seg.', 'seg', 's', 'ml', 'mL', 'UI', 'U', 'g', 'mg', 'ng', 'mm', 'mEq']);

// sigla do BRIEFING (docs/BRIEFING.md) por grupo (título do bloco) e rótulo; chaves sem acento, só A-Z0-9
const SIGLA_GRUPO = [
  ['HEMOGRAMA', { HEMOGLOBINA: 'HB', HEMATOCRITO: 'HT', LEUCOCITOS: 'LEUCO', SEGMENTADOS: 'SEG', BASTONETES: 'BAST', PLAQUETAS: 'PLAQ' }],
  ['GASOMETRIA', { PH: 'pH', PCO2: 'pCO2', PO2: 'pO2', HCO3: 'HCO3', BEECF: 'BE', SO2: 'SatO2', LAC: 'Lactato' }],
  ['PAINELCARDIACO', { TROPONINA: 'Troponina' }],
  ['TEMPODEATIVIDADEDAPROTROMBINA', { INR: 'INR' }],
];
// bloco de um exame só (título = nome do exame)
const SIGLA_UNICO = {
  UREIA: 'UR', CREATININA: 'CR', SODIO: 'NA', POTASSIO: 'K', MAGNESIO: 'MG', CALCIOIONICO: 'CAI', FOSFORO: 'P',
  PROTEINACREATIVA: 'PCR', DIMERO: 'D-dímero', DDIMERO: 'D-dímero', HEMOGLOBINA: 'HB', HEMATOCRITO: 'HT',
  LACTATO: 'Lactato', TROPONINA: 'Troponina',
};

function chave(s) {
  return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().replace(/[^A-Z0-9]/g, '');
}

// data do laudo (horário de Brasília, sem horário de verão desde 2019) -> ISO em UTC
function iso(d, m, a, h, mi, s) {
  return new Date(a + '-' + m + '-' + d + 'T' + (h || '00') + ':' + (mi || '00') + ':' + (s || '00') + '-03:00').toISOString();
}

function nomeChave(s) {
  return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().replace(/[^A-Z ]/g, ' ').replace(/\s+/g, ' ').trim();
}

// dia (aaaa-mm-dd) em Brasília
function diaBr(t) {
  return new Date(Date.parse(t) - 3 * 3600e3).toISOString().slice(0, 10);
}

function ehUnidade(t) {
  return t === '%' || (t.length <= 12 && (t.includes('/') || UNIDADES_SOLTAS.has(t)));
}

function ehNumero(s) {
  return /^[<>]?=?\s*-?\d[\d.,]*$/.test(String(s).trim());
}

// "10.300" = 10300; "9,30" = 9.3; "1.03" e "13.7" = decimal com ponto (INR, TAP); densidade "1.010" = 1.01
function paraNumero(v, rotulo) {
  const s = String(v == null ? '' : v).trim();
  if (!/^-?\d[\d.,]*$/.test(s)) return null;
  let n;
  if (s.includes(',')) n = Number(s.replace(/\./g, '').replace(',', '.'));
  else if (/^\d{1,3}(\.\d{3})+$/.test(s) && !/densidade/i.test(rotulo || '')) n = Number(s.replace(/\./g, ''));
  else n = Number(s);
  return Number.isFinite(n) ? n : null;
}

function unidadeDaRef(vr) {
  const m = String(vr || '').match(/\d\s*([a-zA-Zμµ%/][\w/.μµ%]*)/);
  return m && ehUnidade(m[1]) ? m[1] : '';
}

// tira cabeçalho e rodapé de cada página; guarda nome do paciente e local de coleta do cabeçalho
function linhasDoLaudo(texto) {
  const linhas = [];
  const cab = { paciente: '', local: '' };
  let dentro = false;
  let anterior = '';
  for (const bruto of String(texto || '').split('\n')) {
    const l = bruto.trim();
    if (!l) continue;
    if (/^Instituto de Biomedicina do ABC/i.test(l)) { dentro = true; anterior = l; continue; }
    if (dentro) {
      if (/^RESULTADO$/i.test(l)) { dentro = false; continue; }
      const p = l.match(/^Paciente\s*:\s*(.+)$/i);
      if (p && !cab.paciente) cab.paciente = p[1].trim();
      const lc = l.match(/^Local Coleta\s*:?\s*(.*)$/i);
      if (lc && lc[1] && !cab.local) cab.local = lc[1].trim();
      else if (/^Local Coleta/i.test(anterior) && !cab.local) cab.local = l;
      anterior = l;
      continue;
    }
    if (/^Os valores dos testes de laborat|^tempo ?de jejum|^Folha:\s*\d+\s*de\s*\d+|Laudo liberado eletronicamente/i.test(l)) continue;
    linhas.push(l);
  }
  return { linhas, cab };
}

function lerMeta(L) {
  const f = { material: '', amostra: '', metodo: '', vr: '', obs: [] };
  let atual = null;
  for (let i = 0; i < L.length; i++) {
    const l = L[i];
    if (/^M[ée]todo$/i.test(l) && L[i + 1] === ':') { atual = 'metodo'; i++; continue; }
    const m = l.match(RE_CAMPO);
    if (m) {
      const k = /^Mat/i.test(m[1]) ? 'material' : /^Amo/i.test(m[1]) ? 'amostra' : /^M[ée]t/i.test(m[1]) ? 'metodo'
        : /^(V|Valor)/i.test(m[1]) ? 'vr' : 'obs';
      atual = k;
      if (k === 'obs') f.obs.push(m[2].trim());
      else f[k] = (f[k] + ' ' + m[2]).trim();
      continue;
    }
    if (atual === 'obs' && f.obs.length) f.obs[f.obs.length - 1] += ' ' + l;
    else if (atual) f[atual] = (f[atual] + ' ' + l).trim();
  }
  f.obs = f.obs.map((o) => o.trim()).filter((o) => o && !/Novos valores de refer/i.test(o));
  return f;
}

// linhas que vêm depois de "rótulo: valor": unidade, faixa de referência, valor absoluto (diferencial) e texto
function detalhar(r, cultura) {
  const d = [];
  for (let i = 0; i < r.depois.length; i++) {
    const l = r.depois[i];
    if (r.depois[i + 1] === '3' && /mm$/.test(l.split(' ')[0])) { d.push(l.replace(/^(\S*mm)/, (x) => x + '3')); i++; }
    else d.push(l);
  }
  let valor = String(r.valor).trim();
  let unidade = '';
  let ref = r.ref || '';
  let abs = null;
  let absU = '';
  let absRef = '';
  let fase = 'v';
  const vu = valor.match(/^([<>]?=?\s*-?\d[\d.,]*)\s+(\S+)$/);
  if (vu && ehUnidade(vu[2])) { valor = vu[1]; unidade = vu[2]; }
  const numerico = ehNumero(valor);
  const textos = [];
  for (const l of d) {
    const t = l.split(/\s+/)[0];
    const resto = l.slice(t.length).trim();
    if (numerico && /^\d[\d.,]*$/.test(l) && unidade === '%' && abs === null) { abs = l; fase = 'a'; continue; }
    if (ehUnidade(t)) {
      if (fase === 'v' && !unidade) { unidade = t; if (/\d/.test(resto)) ref = (ref + ' ' + resto).trim(); continue; }
      if (fase === 'a' && !absU) { absU = t; if (/\d/.test(resto)) absRef = (absRef + ' ' + resto).trim(); continue; }
    }
    if (/^\(|^[<>]?\s*\d[\d.,]*\s*(-|a\b|at[ée])/.test(l)) {
      if (fase === 'a') absRef = (absRef + ' ' + l).trim(); else ref = (ref + ' ' + l).trim();
      continue;
    }
    if (RE_CABECALHO.test(l)) continue;
    textos.push(l);
  }
  // resultado em texto quebrado na linha do PDF ("... em 5 dias de" / "incubação."): linha que começa minúscula continua o valor
  if (!numerico) while (textos.length && /^[a-zà-ú]/.test(textos[0])) valor += ' ' + textos.shift();
  const out = [{ exame: r.exame, valor, unidade, referencia: ref, obs: (cultura || !numerico) ? textos.join(' ').slice(0, 400) : '' }];
  if (abs !== null) out.push({ exame: r.exame + ' (abs)', valor: abs, unidade: absU, referencia: absRef, obs: '' });
  return out;
}

// bloco com vários exames: "rótulo : valor", com o ":" e o valor às vezes em linhas separadas
function lerRegistros(linhas, cultura) {
  const regs = [];
  const obs = [];
  const pend = [];
  let cur = null;
  let aguardando = null;
  for (let i = 0; i < linhas.length; i++) {
    const l = linhas[i];
    if (/^Valores de Refer[êe]ncia$/i.test(l)) { if (regs.length) break; continue; }
    if (aguardando !== null) { cur = { exame: aguardando, valor: l, depois: [] }; regs.push(cur); aguardando = null; continue; }
    if (l === ':') {
      if (!cur) {
        const bons = pend.filter((x) => !(x === x.toUpperCase() && /[A-Z]/.test(x)));
        aguardando = (bons.length ? bons : pend.slice(-1)).join(' ');
      } else aguardando = cur.depois.pop() || '';
      pend.length = 0;
      continue;
    }
    const m = l.match(RE_ROTULO);
    if (m && !/^[(\d<>]/.test(m[1])) {
      pend.length = 0;
      if (RE_REF_ROTULO.test(m[1])) { if (cur) cur.ref = ((cur.ref || '') + ' ' + l).trim(); continue; }
      if (/^Observa[çc]/i.test(m[1])) { if (m[2]) obs.push(m[2]); continue; }
      if (m[2] === '') { aguardando = m[1]; continue; }
      cur = { exame: m[1], valor: m[2], depois: [] };
      regs.push(cur);
      continue;
    }
    if (cur) cur.depois.push(l); else pend.push(l);
  }
  const valores = [];
  for (const r of regs) if (!RE_DESCARTE.test(r.exame)) valores.push(...detalhar(r, cultura));
  return { valores, obs };
}

function lerAntibiograma(res) {
  let org = '';
  const valores = [];
  for (let i = 1; i < res.length; i++) {
    const l = res[i];
    const mo = l.match(/^Micro-?organismo\s*:\s*(.+)$/i);
    if (mo) { org = mo[1].trim(); continue; }
    const prox = res[i + 1] || '';
    const r = prox.match(/^(\S*)\s+([SIR])$/) || prox.match(/^()([SIR])$/);
    if (r && /^[A-Za-zÀ-ú]/.test(l) && !/^Antibacterianos/i.test(l)) {
      valores.push({ exame: l, valor: r[2], unidade: '', referencia: r[1] ? 'CIM ' + r[1] : '', obs: org });
      i++;
    }
  }
  if (!valores.length) {
    // disco-difusão: tabela com colunas S / I / R; o texto do PDF perde a coluna, então não se adivinha
    const drogas = res.slice(1).filter((l) => /^[A-Za-zÀ-ú]/.test(l) && !/^(Sens[íi]vel|Resistente|exposi[çc][ãa]o|Intermedi|Micro)/i.test(l));
    valores.push({ exame: 'ANTIBIOGRAMA', valor: 'ler no PDF (tabela S/I/R por colunas)', unidade: '', referencia: '', obs: drogas.join(', ').slice(0, 400) });
  }
  return { grupo: 'ANTIBIOGRAMA' + (org ? ' - ' + org : ''), valores, obs: [] };
}

function lerBloco(L) {
  const titulo = L[0] || '';
  let iMeta = L.length;
  for (let i = 1; i < L.length; i++) {
    if (RE_META.test(L[i]) || (/^M[ée]todo$/i.test(L[i]) && L[i + 1] === ':')) { iMeta = i; break; }
  }
  const res = L.slice(0, iMeta);
  const meta = lerMeta(L.slice(iMeta));
  let grupo = titulo;
  let valores = [];
  let obsRes = [];
  if (/^ANTIBIOGRAMA/i.test(titulo)) {
    ({ grupo, valores } = lerAntibiograma(res));
  } else {
    const m = titulo.match(RE_TITULO_VALOR);
    if (m && (res.length === 1 || (res.length === 2 && ehUnidade(res[1])))) {
      grupo = m[1].trim();
      valores.push({
        exame: grupo, valor: (m[2] ? m[2].replace(/\s+/g, '') : '') + m[3],
        unidade: m[4] || (res.length === 2 ? res[1] : '') || unidadeDaRef(meta.vr), referencia: meta.vr, obs: '',
      });
    } else {
      const linhas = m ? [m[1].trim() + ' : ' + (m[2] || '') + m[3] + (m[4] ? ' ' + m[4] : '')].concat(res.slice(1)) : res.slice(1);
      if (m) grupo = m[1].trim();
      ({ valores, obs: obsRes } = lerRegistros(linhas, RE_CULTURA.test(titulo)));
      if (!valores.length && !m && res.length >= 2 && !RE_ROTULO.test(res[1])) {
        valores.push({ exame: titulo, valor: res.slice(1).join(' ').slice(0, 400), unidade: '', referencia: meta.vr, obs: '' });
      }
    }
  }
  const obs = obsRes.concat(meta.obs);
  const maquina = /M[AÁ]QUINA/i.test(obs.join(' ') + ' ' + meta.amostra);
  const gk = chave(grupo);
  const par = SIGLA_GRUPO.find(([k]) => gk.startsWith(k));
  for (const v of valores) {
    const ek = chave(v.exame);
    v.sigla = maquina ? '' : par ? (par[1][ek] || '') : valores.length === 1 ? (SIGLA_UNICO[ek] || '') : '';
    v.valor_num = paraNumero(v.valor, v.exame);
    if (maquina) v.obs = (v.obs ? v.obs + ' | ' : '') + 'amostra da máquina (circuito de diálise): não é do paciente';
  }
  return { grupo, valores, material: meta.material, amostra: meta.amostra, metodo: meta.metodo, obs: obs.join(' | ') };
}

function lerLaudo(texto) {
  const { linhas, cab } = linhasDoLaudo(texto);
  const blocos = [];
  const avisos = [];
  let atual = [];
  for (const l of linhas) {
    const c = l.match(RE_COLETA);
    if (c) {
      const b = lerBloco(atual);
      b.coleta = iso(c[1], c[2], c[3], c[4], c[5], c[6]);
      b.coleta_sem_hora = !c[4];
      b.liberado = c[7] ? iso(c[7], c[8], c[9], c[10], c[11], c[12]) : null;
      blocos.push(b);
      atual = [];
      continue;
    }
    const lib = l.match(RE_LIBERADO);
    if (lib && !atual.length && blocos.length && !blocos[blocos.length - 1].liberado) {
      blocos[blocos.length - 1].liberado = iso(lib[1], lib[2], lib[3], lib[4], lib[5], lib[6]);
      continue;
    }
    atual.push(l);
  }
  if (atual.length) avisos.push('trecho sem Data da Coleta ignorado: "' + atual[0].slice(0, 50) + '"');
  for (const b of blocos) {
    if (!b.valores.length) avisos.push('bloco sem valor lido: "' + String(b.grupo).slice(0, 50) + '"');
    if (b.valores.some((v) => /^ler no PDF/.test(v.valor))) avisos.push('antibiograma em colunas: ler S/I/R no PDF');
  }
  return { paciente: cab.paciente, local: cab.local, blocos, avisos };
}

/*
 * Linhas das tabelas exames_valores e exames_laudos para um laudo baixado.
 * meta = {id_doc, paciente (nome normalizado), leito, coleta (dt_doc_real, ISO), inclusao, exames, pendente}
 * Coleta sem hora no laudo: usa a hora do pedido (dt_doc_real) se for o mesmo dia, e avisa no obs.
 */
function paraBanco(meta, texto, erro, agora) {
  const r = erro ? { paciente: '', blocos: [], avisos: ['PDF não lido: ' + erro] } : lerLaudo(texto);
  const avisos = r.avisos.slice();
  const nomePdf = nomeChave(r.paciente);
  if (nomePdf && meta.paciente && nomePdf !== meta.paciente) {
    avisos.push('nome no PDF diferente do pedido: laudo descartado');
    r.blocos = [];
  }
  const valores = [];
  const cont = {};
  for (const b of r.blocos) {
    let coleta = b.coleta;
    let obsColeta = '';
    if (b.coleta_sem_hora) {
      if (meta.coleta && diaBr(meta.coleta) === diaBr(b.coleta)) { coleta = meta.coleta; obsColeta = 'hora da coleta tirada do pedido (laudo sem hora)'; }
      else obsColeta = 'laudo sem hora da coleta';
    }
    for (const v of b.valores) {
      const base = [meta.id_doc, coleta, chave(b.grupo), chave(v.exame)].join('|');
      cont[base] = (cont[base] || 0) + 1;
      valores.push({
        chave: base + (cont[base] > 1 ? '#' + cont[base] : ''), id_doc: meta.id_doc, paciente: meta.paciente, leito: meta.leito,
        grupo: b.grupo, exame: v.exame, sigla: v.sigla, valor: v.valor, valor_num: v.valor_num, unidade: v.unidade,
        referencia: String(v.referencia || '').slice(0, 300), material: b.material, coleta, liberado: b.liberado,
        obs: [v.obs, b.obs, obsColeta].filter(Boolean).join(' | ').slice(0, 500),
      });
    }
  }
  const laudo = {
    id_doc: meta.id_doc, paciente: meta.paciente, leito: meta.leito, coleta: meta.coleta, inclusao: meta.inclusao,
    exames: meta.exames, pendente: !!meta.pendente, n_valores: valores.length, aviso: avisos.join(' | ').slice(0, 500), lido_em: agora,
  };
  return { valores, laudo };
}

if (typeof module !== 'undefined' && module.exports) module.exports = { lerLaudo, paraBanco, paraNumero, chave, nomeChave };
