# 🗺️ Mapa da Folha — Beneficência Portuguesa / UTI Adulto

Modelo: `Mod. 0120-01 - G.I.Press`. Cada leito = **2 páginas**.

## Cabeçalho (identificação)

- `Pac:` código + NOME. `Idade / Sexo / Bloco:UTI ADULTO 2 / Quarto / Leito`.
- Tarjas: ALERGIA / DIABÉTICO / CONTATO → puxar p/ contexto (não pro bloco).
- Data Int. = data de internação. `Data` (manuscrita no topo) = data da folha.

## PÁGINA 1 — "PLANEJAMENTO ASSISTENCIAL TERAPIA INTENSIVA ADULTO"

Grade horária: linhas pares vazias, ímpares preenchidas (q2h): 7,9,11,13,15,17 // 19,21,23,1,3,5.

Colunas (esquerda → direita):

1. **Hora**
2. **T** (temperatura, °C)
3. **FR** (rpm)
4. **FC** (bpm)
5. **Pressão Arterial** — `:00h` e `:30h`, formato `Sist/Diast (Méd)`
6. **Glicemia mg/dl** (células às vezes destacadas em amarelo = pico)
7. **Saturação Arterial** (SpO2 %)
8. **Dor (escala)** · **PVC** · **RASS** (quase sempre em branco)
9. **Suporte Ventilatório**: Cateter O2 (lit/min) · Nebulização · Modalidade · Peep · FiO2
    - "AA" = ar ambiente. "1L"/"2L" = cateter nasal. Transcrever literal o resto.

⚠ ARMADILHAS:

- **FR×FC invertem** na caligrafia. Desambiguar: 60–140 → FC; 8–35 → FR.
- **PAM (Méd)** entre parênteses é o valor confiável. Em conflito, ancorar nela.
- Sist/Diast às vezes ilegível → `?`, mas manter PAM se legível.
- Carimbos de enfermagem cortam linhas → não confundir assinatura com dado.

## PÁGINA 2 — "Controle de dor / Ganhos / Perdas"

Topo (Controle de dor) geralmente vazio → ignorar salvo registro.

Bloco **GANHOS** (colunas variam por leito, ler o cabeçalho manuscrito):

- Nutrição: VO / Dieta / SNE / Água / Med
- Endovenoso (bomba de infusão): rótulos manuscritos (ex.: NORA, droga, HC) → BIC
- Infus. Rápida · Dil. (legenda: +10 / O20 / *50 / △100 / ▲250)

Bloco **PERDAS**:

- Diurese · SNG/SNE · Evacuação · Resíduo Gástrico · Dreno/SVD

**RODAPÉS (verdade confiável — usar estes):**

- `Ganhos 6h-18h` / `Perdas 6h-18h` / `Balanço 6h-18h`
- `Ganhos 19h-6h` / `Perdas 19h-6h` / `Balanço 19h-6h`
- `Ganhos hídrico 24h:` → `D:` (diurese 24h) e `BH:` (balanço 24h)

DERIVAÇÕES:

- **Ingesta (janela)** = soma dos `Ganhos` da (s) janela (s). Subtotal ilegível → `?`.
- **Diurese** = `D:` do rodapé (ou soma da coluna Diurese se `D:` ilegível).
- **BH** = `BH:` do rodapé.
- **Evacuação** = nº de episódios + qualidade (P/L/E/ME/SC) + quantidade (+/++/+++).
- **Resíduo gástrico / Dreno** → linha extra se houver valor.

## Legenda de evacuação (rodapé impresso)

P=Pastosa · L=Líquidas · E=Endurecidas · ME=Melena · SC=Sangue/coágulos. Quantidade: + Pequena · ++ Média · +++ Grande.
