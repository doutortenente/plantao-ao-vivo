---
name: "admissao-uti"
description: "Nota de admissão em UTI (1º dia de UTI) do Dr. Nicolas, na voz e no formato das evoluções reais dele, entregue em Word Times New Roman 10. Use sempre que ele pedir admissão, admitir leito, nota de admissão ou primeiro dia de UTI, ou mandar material de paciente recém-chegado, mesmo sem dizer skill. Para admissão, use esta e não a sasi-ingest-export; evolução diária fica na skill plantao."
---

# Admissão UTI

Nota de admissão do Dr. Nicolas, pronta para colar no prontuário e imprimir. O padrão vem das evoluções reais dele (Word da UTI 2 de 10/10/26, com a admissão do leito 02 como referência direta) e do rascunho admissao-uti v3 dele. A nota tem de parecer escrita por ele: de intensivista para intensivista, densa e sem floreio.

## Regras

1. **Zero alucinação.** Só entra dado com fonte legível: documento enviado ou ditado dele. Campo do modelo sem dado fica com o rótulo e nada depois, e ele completa ao canetar. Nunca escrever "[ ]", "não informado", "(revisar)", "?" ou reticências dentro da nota.
2. **Dose, via e posologia só com fonte** (prescrição, relatório, ditado). O item pode entrar sem dose se o nome tiver fonte.
3. **Julgamento acima da letra.** O modelo dá a estrutura. Contradição entre fontes, ou dentro do próprio modelo, se resolve com critério, sem perguntar. Só perguntar quando a resposta muda a nota e não há como decidir (ex.: leito não identificado).
4. **Nada de explicação dentro da nota:** sem mecanismo de ação, sem justificativa didática, sem comentário sobre fonte ou método.
5. **Estilo.** Acentuação completa; CAPS só em siglas e no rótulo ALERGIAS; decimal com vírgula; sem setas ou símbolos decorativos. O "=>" dele só como subitem de problema ou de exame, como nas evoluções.
6. **Não repetir:** alerta já dado na conversa não volta.

## Modelo

`{...}` é instrução e não vai para a nota.

```
{LL} - {NOME COMPLETO}
ADMISSÃO UTI {N} - {DD-MM-AA}

Paciente de {idade} anos{, descritor quando relevante}, em 1º dia de internação em UTI por quadro de:
1. {problema principal, com o dado que justifica UTI}
   => {subitem, quando ajuda}
2. {...}

Admissão ({DD/MM/AA}): {retrato da chegada à UTI}

HPMA: {história até a chegada}

Antecedentes: {...}

Medicamentos de uso domiciliar: {...}

ALERGIAS: {...}

Dispositivos:
IOT - 
CVC - 
Cateter arterial - 
SVD - 
SNE/SNG - 
{Outros - só se houver}

Uso:
Drogas Vasoativas: 
Sedação: 
Antibióticos: 
NPT: 
TNE: 

Sinais Vitais admissão:
PA: {PAS} x {PAD} ({PAM}) mmHg
FC: {valor} bpm
SpO2: {valor}%, {aa / cateter X l/min / VNI / VM FiO2 X% PEEP X}
FR: {valor} ipm
DX: {valor} mg/dl
Temp: {valor} °C

Exame Físico Geral:
- Geral: 
- Sistema Nervoso Central: 
- Sistema Cardiovascular: 
- Sistema Respiratório: 
- Sistema Digestório: 
- Extremidades: 

Exames Complementares:
- {Exame (data hora)}: {resultado resumido}

Plano terapêutico e Condutas:
1. {Sistema}:
- {ação};
2. {...}
{N}. Profilaxias: TEV: {...}; LAMG: {...}; cabeceira {30º ou 45º}.
```

## Como preencher

**Problemas.** Específicos e com o número que justifica UTI: "Urgência hipertensiva (PA 220/110 mmHg na origem)", "IRA - KDIGO I". Nunca diagnóstico nu.

**Admissão.** Retrato da chegada em 2 a 4 linhas, na voz dele: "Admito paciente em leito de UTI devido a ...", "Chega do PS em ar ambiente, orientado, PA 126/87 mmHg (PAM 97), FC 97 bpm, com SNG aberta e AVP em MSE." Inclui o achado-chave, o exame-âncora de entrada e a conduta inicial relevante (parecer pedido, ATB iniciado, IOT no PS). Não é a HPMA.

**HPMA.** Um parágrafo cronológico: início, evolução, atendimento de origem (com sinais vitais e exames de lá), indicação de UTI, chegada. Até 6 a 10 linhas; nunca encher para chegar no tamanho. Lacuna na cronologia não se preenche.

**Antecedentes.** Em ordem de relevância para o quadro, em linha única. Tabagismo e etilismo só entram se forem fator de risco do quadro.

**Medicamentos de uso domiciliar.** Genérico (Marca) dose posologia, separados por ";". Ex.: "Losartana (Aradois) 50 mg 1x/dia; Sertralina (Zoloft) 25 mg 1x/dia". Anticoagulante e antiagregante vêm primeiro. Sem posologia na fonte, só omitir, sem comentário.

**ALERGIAS.** "Nega", ou os agentes separados por " | ", com a reação quando houver.

**Dispositivos e Uso.** As cinco linhas sempre. "Não." ou "Sim, detalhe (data)." só com fonte. Sem fonte, a linha fica vazia: sem a prescrição, o paciente pode estar com vasodilatador ou sedação na bomba.

**Sinais Vitais admissão.** Primeira aferição na UTI, como escrita na folha. A PAM entre parênteses vem do monitor e é transcrita como está, mesmo que não bata com a fórmula. Valor ilegível: linha vazia. Os sinais vitais não se repetem no exame físico.

**Exame Físico Geral.** Se ele não ditou o exame, usar o histórico admissional da enfermagem (ele altera ao canetar). Vocabulário dele: "descorado 2+/4+, desidratado +/4, anictérico, acianótico, afebril"; "ECG 15, pupilas isocóricas, RFM+, sem déficits focais"; "RCR em 2T, BCNF, perfusão periférica preservada"; "MV+ bilateralmente, sem ruídos adventícios"; "abdome flácido, indolor à palpação, RHA+, DB negativo"; "panturrilhas livres, sem sinais de TVP". Normalidade só se a fonte disser normal. Glasgow só se anotado. Sedado: RASS e pupilas. VM: modo e parâmetros no Respiratório.

**Exames Complementares.** Só o que muda conduta, com data e laudo resumido; achado secundário relevante vai em "=> Demais achados:". ECG com os valores do aparelho; interpretação de traçado por foto não entra.

**Plano terapêutico e Condutas.** É a parte que mais pesa. Numerado por sistema, um item por linha com "- " e ";", com os verbos dele: Solicito, Mantido, Inicio, Suspendo, Reduzo, Aguarda, Realizo, Vigilância de, Seguimento com, Pendente discutir com diarista.
- Primeiro, a conduta que ele ditou, redigida nesse padrão e sem perder nada.
- Depois, o que tem lastro no material:
  - investigação pedida no relatório de origem ou no laudo;
  - consequência direta de dado documentado (alergia que interfere no tratamento esperado, duplicidade ou interação no uso domiciliar, dispositivo);
  - contingência "se X, Y" para problema documentado.
- Meta numérica quando a fonte der o número ou quando for a meta usual do problema (ex.: PAM >= 65 mmHg em choque, SpO2 >= 92%, BH neutro). Sem meta defensável, não inventar.
- A última linha é sempre "Profilaxias: TEV: ...; LAMG: ...; cabeceira 30º." Sem prescrição, os rótulos ficam vazios.

## Entrega

1. Escrever a nota em texto (nota.txt) e gerar o Word com o script abaixo: `python3 gerar_admissao.py nota.txt DD-MM-AA-utiN-admissao-leitoLL.docx`.
2. Converter para PDF e olhar as páginas antes de mandar. Se passar de uma folha, o plano vai inteiro para a segunda; isso é aceitável.
3. Mandar o .docx. No chat vão só duas coisas:
   - até 3 linhas de alerta, apenas o que muda conduta ou impediu preencher, sem repetir;
   - a **Conduta destilada**: ações-chave, doses e metas que tenham fonte.
   A nota inteira não vai para o chat, salvo se ele pedir o texto.

Formato, igual ao Word das evoluções dele:
- Página Carta; margens esq. 1,25, dir. 1,34, sup. e inf. 2,5 cm.
- Times New Roman 10 em tudo, espaçamento simples, linha em branco entre seções.
- Negrito só em: as duas linhas de cabeçalho, a frase "Paciente de...", os títulos de seção, os rótulos em linha (Admissão, HPMA, Antecedentes, Medicamentos, ALERGIAS), os rótulos dos sinais vitais, o nome do exame complementar e os sistemas numerados do plano.
- Sem cor, caixa, filete, rodapé ou escore.

```python
# Uso: python3 gerar_admissao.py nota.txt saida.docx [margem_sup_inf_cm]
import re, sys
from docx import Document
from docx.shared import Pt, Cm
from docx.oxml.ns import qn

PLANO = "Plano terapêutico e Condutas:"
SECOES = ("Dispositivos:", "Uso:", "Sinais Vitais admissão:", "Exame Físico Geral:",
          "Exames Complementares:", PLANO)
EM_LINHA = re.compile(r"^(Admissão \([^)]*\):|HPMA:|Antecedentes:|Medicamentos de uso domiciliar:|ALERGIAS:)")


def gerar(txt, saida, margem=2.5):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"; st.font.size = Pt(10)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    pf = st.paragraph_format
    pf.space_before = Pt(0); pf.space_after = Pt(0); pf.line_spacing = 1.0
    s = doc.sections[0]
    s.page_width, s.page_height = Cm(21.59), Cm(27.94)
    s.left_margin, s.right_margin = Cm(1.25), Cm(1.34)
    s.top_margin = s.bottom_margin = Cm(margem)
    secao, cab = None, 0
    for linha in open(txt, encoding="utf-8").read().rstrip().split("\n"):
        p = doc.add_paragraph()
        if secao == PLANO:
            p.paragraph_format.keep_with_next = True  # plano não se parte entre páginas
        if not linha.strip():
            continue

        def run(t, negrito=False):
            r = p.add_run(t); r.bold = negrito
            r.font.name = "Times New Roman"; r.font.size = Pt(10)

        if linha.strip() in SECOES:
            secao = linha.strip(); run(linha.strip(), True)
            if secao == PLANO:
                p.paragraph_format.keep_with_next = True
            continue
        if cab < 2:  # "LL - NOME" e "ADMISSÃO UTI N - DD-MM-AA"
            cab += 1; run(linha, True); continue
        if linha.startswith("Paciente de"):
            run(linha, True); continue
        m = None
        if secao is None:
            m = EM_LINHA.match(linha)
        elif secao == "Sinais Vitais admissão:":
            m = re.match(r"^[^:]{1,10}:", linha)
        elif secao == "Exames Complementares:" and linha.startswith("- "):
            m = re.match(r"^- [^:]{1,80}:", linha)
        elif secao == PLANO:
            m = re.match(r"^\d+\. [^:]{1,40}:", linha)
            if not m and re.match(r"^\d+\. ", linha):
                run(linha, True); continue
        if m:
            run(m.group(0), True); run(linha[m.end():])
        else:
            run(linha)
    doc.save(saida)


if __name__ == "__main__":
    gerar(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 2.5)
```

## Exemplo: admissão real do leito 02 (10/10/26) no modelo

```
02 - NOME COMPLETO
ADMISSÃO UTI 2 - 10-10-26

Paciente de 55 anos, em 1º dia de internação em UTI por quadro de:
1. Abdome agudo obstrutivo
   => Suboclusão intestinal em paciente com cirurgia colorretal prévia
2. IRA - KDIGO I

Admissão (10/10/26): Chega do PS em ar ambiente, orientado, PA 126/87 mmHg (PAM 97), FC 97 bpm, com SNG aberta e AVP em MSE. Abdome flácido, plano, com desconforto à palpação profunda globalmente, sem sinais de peritonite. TC de abdome e pelve sem contraste (10/10) sugestiva de quadro suboclusivo. Parecer da Cirurgia Geral solicitado.

HPMA: Refere ingesta de fast-food em 09/10. Acordou em 10/10 com múltiplos episódios de vômitos, sem aspecto fecaloide, associados a diarreia; nega outros sintomas. Procurou o PS em 10/10, onde apresentava PA 136/72 mmHg, FC 118 bpm, TAX 36,3 °C e SpO2 96% em ar ambiente, com abdome flácido, doloroso à palpação em epigástrio e fossa ilíaca esquerda, DB negativa e Murphy negativo. Realizada TC de abdome e pelve sem contraste, sugestiva de quadro suboclusivo. No PS foram solicitadas passagem de SNG, internação em UTI e avaliação da Cirurgia. Admitido na UTI 2 em 10/10/2026.

Antecedentes: Colite ulcerativa com cirurgia intestinal prévia (hemicolectomia), HAS, placa ortopédica em ombro.

Medicamentos de uso domiciliar: Losartana (Aradois) 50 mg 1x/dia; Sertralina (Zoloft) 25 mg 1x/dia.

ALERGIAS: AINEs | Reação prévia a contraste (não especificada).

Dispositivos:
IOT - Não.
CVC - Não.
Cateter arterial - Não.
SVD - Não.
SNE/SNG - Sim, SNG aberta (10/10/26).
Outros - AVP em MSE (20), salinizado.

Uso:
Drogas Vasoativas: Não.
Sedação: Não.
Antibióticos: Não.
NPT: Não.
TNE: Não.

Sinais Vitais admissão:
PA: 126 x 87 (97) mmHg
FC: 97 bpm
SpO2: 99%, aa
FR: 21 ipm
DX: 
Temp: 

Exame Físico Geral:
- Geral: 
- Sistema Nervoso Central: ECG 15, pupilas isocóricas e reagentes, sem déficits focais. Analgesia adequada.
- Sistema Cardiovascular: Ritmo regular, perfusão periférica boa. Ritmo sinusal ao monitor.
- Sistema Respiratório: MV+ bilateralmente, sem ruídos adventícios. Em ar ambiente.
- Sistema Digestório: Dieta zero. Abdome flácido, plano, desconforto à palpação profunda globalmente, sem sinais de peritonite. RHA+.
- Extremidades: Sem edemas, panturrilhas livres, sem sinais de TVP.

Exames Complementares:
- TC de abdome e pelve sem contraste (10/10/26): Manipulação cirúrgica no retossigmoide com afilamento de alças, dilatação de alças colônicas e de delgado a montante, níveis hidroaéreos, calibre até 4,7 cm; sugestiva de quadro suboclusivo. Sem líquido livre.
   => Demais achados: cistos renais corticais bilaterais; microcálculo não obstrutivo em rim esquerdo; hérnia umbilical com conteúdo gorduroso, sem sinais inflamatórios.

Plano terapêutico e Condutas:
1. TGI:
- Dieta zero + SNG aberta com quantificação de débito;
- Solicito parecer da Cirurgia Geral.
2. Hidratação/Metabólico:
- Aporte calórico durante o jejum.
3. Analgesia:
- Buscopan Composto 8/8h + Tramadol SOS.
4. Fisioterapia respiratória e motora.
5. Profilaxias: TEV: Enoxaparina 40 mg SC 1x/dia; LAMG: Pantoprazol 40 mg EV; cabeceira 45º.
```

## Casos especiais

- **Reinternação na UTI:** "1º dia de reinternação em UTI". O motivo e a internação anterior entram no problema 1 e nos Antecedentes.
- **Transferência de outra UTI:** 1º dia nesta UTI; o histórico (hospital, datas, motivo) vai nos Antecedentes.
- **Pós-operatório imediato:** problema 1 = procedimento + intercorrência; cirurgia e data na HPMA.
- **Fontes conflitantes** (ex.: duas PA sem horário): usar a mais próxima da chegada à UTI. Se o conflito mudar a conduta, vira uma linha de alerta no chat.
