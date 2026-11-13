'use strict';
/*
 * montar_resposta.js — a partir das linhas do banco (tabela exames_valores do n8n), monta por paciente:
 *   - laboratorio: seção "Laboratório:" no formato do docs/BRIEFING.md (anterior => atual; eletrólitos só o atual);
 *   - coletas: data/hora da coleta de cada valor usado nessas linhas (âncora = coleta, nunca a liberação);
 *   - culturas, pendentes, avisos e exames (série completa de cada exame da internação, com a data da coleta).
 * Mesmo código no nó "Montar resposta" do fluxo "Exames - Banco de Resultados" e nos testes.
 */

const UNIDADE_BRIEFING = { HB: 'g/dl', HT: '%', PLAQ: '/mm3', LEUCO: '/mm3', UR: 'mg/dl', CR: 'mg/dl' };
const RE_GRUPO_CULTURA = /CULTURA|SWAB|URINA C\/|ANTIBIOGRAMA|INIBIT|DIFFICILE/i;
const GASO = ['pH', 'pCO2', 'pO2', 'HCO3', 'BE', 'SatO2', 'Lactato'];
const OUTROS = ['PCR', 'Troponina', 'D-dímero', 'INR'];
const JANELA_H = 36; // "atual" = colhido nas 36 h antes do pedido (cobre a coleta da madrugada nos dois turnos)
const PENDENTE_DIAS = 7; // pendência mais velha que isso vira só contagem nos avisos

// "dd/mm hh:mm" em Brasília
function dataBr(t) {
  const d = new Date(Date.parse(t) - 3 * 3600e3).toISOString();
  return d.slice(8, 10) + '/' + d.slice(5, 7) + ' ' + d.slice(11, 16);
}

function chaveTexto(s) {
  return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().replace(/[^A-Z0-9]/g, '');
}

const daMaquina = (r) => /máquina/.test(String(r.obs || ''));
const sufixo = (r) => (String(r.chave || '').match(/#\d+$/) || [''])[0];
const isoTxt = (v) => {
  const d = v instanceof Date ? v : new Date(String(v || ''));
  return isNaN(d) ? String(v || '') : d.toISOString();
};

// um valor por (exame, coleta): laudo reemitido repete o mesmo valor; fica o de liberação mais recente
function semRepetir(linhas, chaveDe) {
  const m = new Map();
  for (const r of linhas) {
    const k = chaveDe(r) + '|' + r.coleta;
    const v = m.get(k);
    if (!v || String(r.liberado || '') > String(v.liberado || '')) m.set(k, r);
  }
  return [...m.values()].sort((a, b) => Date.parse(a.coleta) - Date.parse(b.coleta) || String(a.chave).localeCompare(String(b.chave)));
}

// mesmo desenho do montar() de skills/sasi-ingest-export/scripts/labs.py
// "atual" só se colhido a partir de janelaIni (ms); valor mais velho fica fora das linhas (continua em exames)
function laboratorio(S, janelaIni) {
  const ult = (k) => {
    const s = S[k] || [];
    const u = s[s.length - 1];
    return u && Date.parse(u.coleta) >= (janelaIni || 0) ? u : null;
  };
  const ant = (k) => (ult(k) && S[k].length > 1 ? S[k][S[k].length - 2] : null);
  const serie = (k) => {
    const u = ult(k);
    if (!u) return null;
    const a = ant(k);
    return k + ': ' + (a ? a.valor + ' => ' : '') + u.valor + (UNIDADE_BRIEFING[k] ? ' ' + UNIDADE_BRIEFING[k] : '');
  };
  const atual = (k) => (ult(k) ? k + ': ' + ult(k).valor : null);
  const linhas = [];
  let g = ['HB', 'HT', 'PLAQ'].map(serie).filter(Boolean);
  if (g.length) linhas.push(g.join(' | '));
  const leu = ult('LEUCO');
  if (leu) {
    const mesma = (k) => (S[k] || []).filter((r) => r.coleta === leu.coleta).pop();
    const seg = mesma('SEG');
    const bast = mesma('BAST');
    linhas.push(serie('LEUCO') + (seg && bast ? ' (seg ' + seg.valor + ' % / bast ' + bast.valor + ' %)' : ''));
  }
  g = [serie('UR'), serie('CR')].concat(['NA', 'K', 'MG', 'CAI', 'P'].map(atual)).filter(Boolean);
  if (g.length) linhas.push(g.join(' | '));
  const comGaso = GASO.filter((k) => ult(k));
  if (comGaso.length) {
    const t = comGaso.map((k) => ult(k).coleta).sort().pop();
    const partes = GASO.map((k) => (S[k] || []).filter((r) => r.coleta === t).pop()).map((r, i) => (r ? GASO[i] + ' ' + r.valor : null));
    linhas.push('Gaso: ' + partes.filter(Boolean).join(' / '));
  }
  const o = OUTROS.filter((k) => ult(k)).map((k) => k + ' ' + ult(k).valor);
  if (o.length) linhas.push('Outros: ' + o.join(' / '));
  return linhas;
}

// extras = {avisos, pendentes, ref (ISO: momento do pedido ou fim do dia "ate")}
function montarPaciente(p, linhasBrutas, extras) {
  const ex = extras || {};
  const avisos = (ex.avisos || []).slice();
  const refMs = Date.parse(ex.ref || new Date().toISOString());
  const janelaIni = refMs - JANELA_H * 3600e3;
  const linhas = linhasBrutas.map((r) => Object.assign({}, r, { coleta: isoTxt(r.coleta), liberado: r.liberado ? isoTxt(r.liberado) : null }))
    .filter((r) => Date.parse(r.coleta) <= refMs);
  const S = {};
  for (const r of semRepetir(linhas.filter((x) => x.sigla && !daMaquina(x)), (x) => x.sigla)) (S[r.sigla] = S[r.sigla] || []).push(r);
  const coletas = {};
  for (const k of Object.keys(S)) {
    const s = S[k];
    coletas[k] = { atual: dataBr(s[s.length - 1].coleta), anterior: s.length > 1 ? dataBr(s[s.length - 2].coleta) : null };
  }
  const todas = semRepetir(linhas, (r) => chaveTexto(r.grupo) + '|' + chaveTexto(r.exame) + sufixo(r) + (daMaquina(r) ? '|MAQ' : ''));
  const series = new Map();
  const cult = new Map();
  for (const r of todas) {
    if (RE_GRUPO_CULTURA.test(r.grupo)) {
      const k = r.coleta + '|' + r.grupo;
      if (!cult.has(k)) cult.set(k, { coleta: dataBr(r.coleta), liberado: r.liberado ? dataBr(r.liberado) : null, exame: r.grupo, itens: [] });
      cult.get(k).itens.push(r);
      continue;
    }
    const k = chaveTexto(r.grupo) + '|' + chaveTexto(r.exame) + sufixo(r) + (daMaquina(r) ? '|MAQ' : '');
    if (!series.has(k)) {
      const nome = chaveTexto(r.grupo) === chaveTexto(r.exame) ? r.exame : r.exame + ' (' + r.grupo + ')';
      series.set(k, { nome: nome + (daMaquina(r) ? ' [máquina]' : ''), sigla: daMaquina(r) ? '' : (r.sigla || ''), unidade: '', referencia: '', serie: [] });
    }
    const s = series.get(k);
    s.serie.push(r.valor + ' (' + dataBr(r.coleta) + ')');
    s.unidade = r.unidade || s.unidade;
    s.referencia = r.referencia || s.referencia;
  }
  const culturas = [...cult.values()].map((c) => {
    let resultado;
    if (/^ANTIBIOGRAMA/i.test(c.exame) && c.itens.every((r) => /^[SIR]$/.test(r.valor))) {
      const por = { S: [], I: [], R: [] };
      for (const r of c.itens) por[r.valor].push(r.exame);
      resultado = ['S', 'I', 'R'].filter((k) => por[k].length).map((k) => k + ': ' + por[k].join(', ')).join(' | ');
    } else {
      resultado = c.itens.map((r) => (chaveTexto(r.exame) === chaveTexto(c.exame) ? '' : r.exame + ': ') + r.valor
        + (r.unidade ? ' ' + r.unidade : '') + (r.obs ? ' (' + r.obs + ')' : '')).join(' | ');
    }
    return { coleta: c.coleta, liberado: c.liberado, exame: c.exame, resultado: resultado.slice(0, 1200) };
  });
  if (!linhas.length) avisos.push('nenhum valor de laboratório desde ' + String(p.desde).split('-').reverse().join('/'));
  else {
    const ultima = linhas.reduce((m, r) => (r.coleta > m ? r.coleta : m), '');
    if (Date.parse(ultima) < janelaIni) {
      avisos.push('nenhuma coleta nas ' + JANELA_H + ' h antes de ' + dataBr(new Date(refMs).toISOString()) + ' (última: ' + dataBr(ultima)
        + '); seção Laboratório vazia, ver a série em exames');
    }
  }
  return {
    leito: p.leito, nome: p.nome, desde: p.desde, laboratorio: laboratorio(S, janelaIni), coletas, culturas,
    pendentes: ex.pendentes || [], avisos, exames: [...series.values()].map((s) => Object.assign({}, s, { serie: s.serie.join(' | ') })),
  };
}

// e = {pacientes (nó Pacientes), documentos (nó Documentos), linhas (banco), lidos (laudos lidos agora), agora, ref}
function montarResposta(e) {
  const D = e.documentos || {};
  const ref = e.ref || e.agora;
  const limitePend = Date.parse(ref) - PENDENTE_DIAS * 864e5;
  const pacientes = e.pacientes.map((p) => {
    const desdeMs = Date.parse(p.desde + 'T00:00:00-03:00');
    const meus = e.linhas.filter((r) => r.paciente === p.nome && Date.parse(isoTxt(r.coleta)) >= desdeMs);
    const resumo = (D.pacientes || []).find((x) => x.nome === p.nome) || {};
    const avisos = [];
    if (!resumo.docs) {
      avisos.push('nenhum laudo com o nome exato desde ' + p.desde.split('-').reverse().join('/')
        + (resumo.nome_parecido ? ': ' + resumo.nome_parecido + ' laudo(s) com nome parecido, conferir a grafia' : ''));
    }
    for (const l of e.lidos || []) if (l.paciente === p.nome && l.aviso) avisos.push('laudo colhido em ' + dataBr(l.coleta) + ': ' + l.aviso);
    const comPend = (D.docs || []).filter((d) => d.paciente === p.nome && d.pendentes && d.pendentes.length && Date.parse(d.coleta) <= Date.parse(ref));
    const velhos = comPend.filter((d) => Date.parse(d.coleta) < limitePend).length;
    if (velhos) avisos.push(velhos + ' pedido(s) colhido(s) há mais de ' + PENDENTE_DIAS + ' dias ainda com exame sem resultado no site');
    const pendentes = comPend.filter((d) => Date.parse(d.coleta) >= limitePend)
      .map((d) => ({ coleta: dataBr(d.coleta), exames: [...new Set(d.pendentes)] }));
    return montarPaciente(p, meus, { avisos, pendentes, ref });
  });
  const avisos = [];
  if (D.falhas) avisos.push(D.falhas + ' página(s) da busca não vieram em JSON');
  return {
    gerado_em: e.agora, referencia: ref, janela_atual_h: JANELA_H, ancora: 'data da coleta (nunca a da liberação)', laudos_no_site: (D.docs || []).length,
    laudos_lidos_agora: (e.lidos || []).length, avisos, pacientes,
  };
}

if (typeof module !== 'undefined' && module.exports) module.exports = { montarResposta, montarPaciente, laboratorio, dataBr };
