'use strict';
// Testes do leitor de laudo e da montagem da resposta do fluxo n8n "Exames - Banco de Resultados".
// Laudo 100% fictício (tests/fixtures/laudo-n8n-ficticio.txt), no formato que o leitor de PDF do n8n entrega.
// Roda com: node --test tests/exames_n8n.test.js (o CI chama via tests/test_exames_n8n.py).
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const RAIZ = path.join(__dirname, '..');
const { lerLaudo, paraBanco, paraNumero } = require(path.join(RAIZ, 'n8n/exames/ler_laudo.js'));
const { montarResposta } = require(path.join(RAIZ, 'n8n/exames/montar_resposta.js'));
const TEXTO = fs.readFileSync(path.join(__dirname, 'fixtures/laudo-n8n-ficticio.txt'), 'utf8');
const NOME = 'PACIENTE FICTICIO DA SILVA';

const lido = lerLaudo(TEXTO);
const valores = lido.blocos.flatMap((b) => b.valores.map((v) => Object.assign({ grupo: b.grupo, coleta: b.coleta, liberado: b.liberado }, v)));
const achar = (exame, grupo) => valores.find((v) => v.exame === exame && (!grupo || v.grupo.startsWith(grupo)));

test('cabeçalho: nome do paciente e local de coleta', () => {
  assert.equal(lido.paciente, 'PACIENTE FICTÍCIO DA SILVA');
  assert.equal(lido.local, 'UTI-9');
  assert.deepEqual(lido.avisos, []);
});

test('âncora = Data da Coleta do bloco, nunca a liberação', () => {
  const ur = achar('UREIA');
  assert.equal(ur.coleta, '2030-01-10T03:20:00.000Z'); // 00:20 de Brasília
  assert.equal(ur.liberado, '2030-01-10T06:00:00.000Z');
  assert.equal(achar('pH').coleta, '2030-01-10T08:40:00.000Z'); // gaso colhida 05:40, bloco próprio
  assert.equal(achar('Resultado', 'HEMOCULTURA').coleta, '2030-01-03T11:00:00.000Z');
});

test('valor na linha do nome, unidade na linha seguinte ou na mesma', () => {
  assert.deepEqual([achar('UREIA').valor, achar('UREIA').unidade, achar('UREIA').sigla], ['40,0', 'mg/dL', 'UR']);
  assert.deepEqual([achar('CREATININA').valor, achar('CREATININA').sigla], ['1,3', 'CR']);
  assert.deepEqual([achar('POTASSIO').valor, achar('POTASSIO').unidade, achar('POTASSIO').sigla], ['4,1', 'mmol/L', 'K']);
  const pcr = achar('PROTEÍNA C REATIVA');
  assert.deepEqual([pcr.valor, pcr.unidade, pcr.sigla], ['12,50', 'mg/L', 'PCR']); // unidade tirada do V.R.
});

test('cálcio iônico da máquina (circuito) não vira CAI do paciente', () => {
  const cai = achar('CÁLCIO IÔNICO');
  assert.equal(cai.sigla, '');
  assert.match(cai.obs, /máquina/);
});

test('hemograma em tabela: siglas, unidade /mm3, diferencial % e absoluto', () => {
  assert.deepEqual([achar('Hemoglobina').valor, achar('Hemoglobina').valor_num, achar('Hemoglobina').sigla], ['9,30', 9.3, 'HB']);
  assert.equal(achar('Hematócrito').sigla, 'HT');
  const leu = achar('Leucócitos');
  assert.deepEqual([leu.valor, leu.valor_num, leu.unidade, leu.sigla], ['10.300', 10300, '/mm3', 'LEUCO']);
  assert.deepEqual([achar('Bastonetes').valor, achar('Bastonetes').unidade, achar('Bastonetes').sigla], ['2', '%', 'BAST']);
  assert.deepEqual([achar('Bastonetes (abs)').valor, achar('Bastonetes (abs)').unidade], ['206', '/mm3']);
  assert.equal(achar('Segmentados').sigla, 'SEG');
  assert.deepEqual([achar('Plaquetas').valor_num, achar('Plaquetas').sigla], [250000, 'PLAQ']);
});

test('gasometria "rótulo : valor" em linhas soltas; tabela de referência não vira valor', () => {
  const sig = (s) => valores.find((v) => v.sigla === s);
  assert.deepEqual(['pH', 'pCO2', 'Lactato', 'HCO3', 'BE', 'SatO2'].map((s) => sig(s).valor), ['7,456', '34,2', '2,7', '24,3', '-3,2', '96,2']);
  assert.equal(sig('BE').valor_num, -3.2);
  assert.equal(valores.filter((v) => v.grupo === 'GASOMETRIA STAT').length, 6);
});

test('coagulação com ponto decimal (INR 1.03, TP 13.7)', () => {
  assert.deepEqual([achar('INR').valor, achar('INR').valor_num, achar('INR').sigla], ['1.03', 1.03, 'INR']);
  assert.deepEqual([achar('Tempo de Protrombina').valor_num, achar('Tempo de Protrombina').unidade], [13.7, 'seg.']);
  assert.equal(paraNumero('1.010', 'Densidade'), 1.01);
  assert.equal(paraNumero('8.343', 'Segmentados (abs)'), 8343);
});

test('cultura em texto e antibiograma S/I/R', () => {
  assert.equal(achar('Resultado', 'HEMOCULTURA').valor, 'Não houve crescimento bacteriano em 5 dias de incubação.');
  const ami = achar('Amicacina');
  assert.deepEqual([ami.valor, ami.referencia, ami.grupo], ['S', 'CIM 2', 'ANTIBIOGRAMA - Bactéria fictícia']);
  assert.equal(achar('Ceftriaxona').valor, 'R');
});

test('coleta sem hora: usa a hora do pedido do mesmo dia e avisa', () => {
  const meta = { id_doc: '1', paciente: NOME, leito: '09', coleta: '2030-01-09T10:00:00.000Z', inclusao: '2030-01-10T09:00:00.000Z', exames: 'x', pendente: false };
  const { valores: linhas, laudo } = paraBanco(meta, TEXTO, '', '2030-01-10T12:00:00.000Z');
  const pcr = linhas.find((l) => l.sigla === 'PCR');
  assert.equal(pcr.coleta, meta.coleta);
  assert.match(pcr.obs, /hora da coleta tirada do pedido/);
  assert.equal(new Set(linhas.map((l) => l.chave)).size, linhas.length);
  assert.equal(laudo.n_valores, linhas.length);
});

test('nome do PDF diferente do pedido: laudo descartado', () => {
  const { valores: linhas, laudo } = paraBanco({ id_doc: '1', paciente: 'OUTRA PESSOA' }, TEXTO, '', '');
  assert.equal(linhas.length, 0);
  assert.match(laudo.aviso, /nome no PDF diferente/);
});

test('resposta: seção Laboratório do BRIEFING, anterior => atual, janela de 36 h', () => {
  const meta = { id_doc: '1', paciente: NOME, leito: '09', coleta: '2030-01-09T10:00:00.000Z' };
  const linhas = paraBanco(meta, TEXTO, '', '').valores;
  linhas.push({ chave: '0|HB', paciente: NOME, grupo: 'HEMOGRAMA', exame: 'Hemoglobina', sigla: 'HB', valor: '10,1', coleta: '2030-01-09T03:00:00.000Z' });
  const pacientes = [{ leito: '09', nome: NOME, desde: '2030-01-01' }];
  const documentos = { docs: [], pacientes: [{ nome: NOME, docs: 1 }] };
  const R = montarResposta({ pacientes, documentos, linhas, lidos: [], agora: '2030-01-10T15:00:00.000Z', ref: '2030-01-10T15:00:00.000Z' });
  const p = R.pacientes[0];
  assert.deepEqual(p.laboratorio, [
    'HB: 10,1 => 9,30 g/dl | HT: 27,90 % | PLAQ: 250.000 /mm3',
    'LEUCO: 10.300 /mm3 (seg 81 % / bast 2 %)',
    'UR: 40,0 mg/dl | CR: 1,3 mg/dl | K: 4,1',
    'Gaso: pH 7,456 / pCO2 34,2 / HCO3 24,3 / BE -3,2 / SatO2 96,2 / Lactato 2,7',
    'Outros: PCR 12,50 / INR 1.03',
  ]);
  assert.deepEqual(p.coletas.HB, { atual: '10/01 00:20', anterior: '09/01 00:00' });
  assert.ok(p.exames.some((e) => /\[máquina\]/.test(e.nome)));
  assert.ok(p.culturas.some((c) => c.exame.startsWith('ANTIBIOGRAMA') && c.resultado === 'S: Amicacina | R: Ceftriaxona'));
  // 3 dias depois sem coleta nova: seção vazia + aviso (valor velho não passa por atual)
  const velho = montarResposta({ pacientes, documentos, linhas, lidos: [], agora: '2030-01-13T15:00:00.000Z', ref: '2030-01-13T15:00:00.000Z' });
  assert.deepEqual(velho.pacientes[0].laboratorio, []);
  assert.match(velho.pacientes[0].avisos.join(' '), /nenhuma coleta nas 36 h/);
});
