# Roteiro de apresentação — Pipeline de Reconciliação Koncili x Omie

Documento de apoio para explicar o projeto em entrevista técnica ou para
o RH, em diferentes níveis de profundidade. Repositório:
https://github.com/Pruppety/koncili-omie-reconciliation

---

## 1. Pitch de 30 segundos (abertura)

> "Construí um pipeline de dados que automatiza a conciliação financeira
> entre duas fontes diferentes — uma plataforma de pagamentos (Koncili) e
> um ERP (Omie) — algo que normalmente é feito manualmente comparando
> planilha com planilha. O projeto não é só um script: tem validação de
> schema, lógica de matching auditável, testes automatizados, execução em
> container, orquestração via Airflow e CI no GitHub Actions. Usei dados
> 100% sintéticos para poder publicar no GitHub sem expor informação real
> de empresa nenhuma."

Use isso como resposta a "me conta sobre um projeto que você fez".

---

## 2. O problema de negócio (contextualizar antes da técnica)

Toda empresa que recebe pagamentos por uma plataforma (Koncili) e lança
isso no ERP (Omie) precisa, periodicamente, confirmar que o que foi
pago bate com o que foi lançado contabilmente. Feito manualmente, isso:

- É lento (alguém abre duas planilhas e compara linha a linha)
- É sujeito a erro humano (olho cansado não vê diferença de R$ 0,50)
- Não deixa rastro de *por que* duas linhas foram consideradas a mesma
  transação — se alguém perguntar depois, não tem como provar

O pipeline resolve isso automatizando a comparação e, mais importante,
tornando a decisão de "isso é a mesma transação" auditável e explicável.

**Se o entrevistador perguntar "por que esse projeto e não outro?"**:
é um problema real, recorrente em qualquer empresa que opera com
recebíveis — não é um dataset de Kaggle, é engenharia de dados aplicada
a um processo de negócio de verdade.

---

## 3. Visão geral da arquitetura (o "mapa" do projeto)

Desenhe ou descreva este fluxo — é o que ancora toda a conversa técnica:

```
Koncili.xlsx  Omie.xlsx
     │            │
  EXTRACT      EXTRACT        (pandas lê o Excel)
     │            │
  VALIDATE     VALIDATE       (pandera garante o schema — falha explícita
     │            │            se o layout mudar)
  NORMALIZE    NORMALIZE      (datas, valores, CPF/CNPJ, texto → schema
     │            │            canônico comum)
     └─────┬──────┘
         MATCH EXATO           (chave: cpf_cnpj + numero_documento,
            │                   com tolerância de valor/data)
            ▼ (o que não casou)
         MATCH FUZZY           (RapidFuzz na descrição, só como fallback,
            │                   com score mínimo configurável)
         CLASSIFICAÇÃO         (CONCILIADO / DIVERGENTE_VALOR /
            │                   SOMENTE_KONCILI / SOMENTE_OMIE)
         EXPORT                (Excel consolidado + histórico em SQLite)
            │
      Orquestrado por Airflow (DAG diária, com retries automáticos)
```

**Frase-chave para fixar**: "Cada etapa é um módulo Python independente
e testável — extract, transform, match, export — orquestrado por uma
função única que roda igual na CLI, no Docker ou agendada pelo Airflow."

---

## 4. Decisões técnicas que valem a pena defender em detalhe

Para cada uma, a estrutura de resposta é: **o que eu escolhi → o que eu
descartei → por quê**. Isso é o que diferencia "eu segui um tutorial" de
"eu entendo engenharia de software".

### 4.1 Por que Pandas e não Polars/DuckDB?

> "Para o volume que esse processo tem no mundo real — planilhas de até
> algumas centenas de milhares de linhas, rodando uma vez por dia —
> Pandas é suficiente e é o que o mercado mais usa e reconhece. Eu
> conheço Polars e DuckDB, que ganham em performance com datasets
> maiores via processamento columnar, mas usar isso aqui seria otimização
> prematura: eu estaria resolvendo um problema de escala que esse pipeline
> não tem."

### 4.2 Por que validar schema com Pandera em vez de só tratar exceção?

> "Pipeline financeiro que falha silenciosamente é o pior cenário possível:
> se a Koncili renomear uma coluna na exportação, sem validação explícita
> o pipeline continuaria rodando e geraria um relatório de conciliação
> errado — e ninguém notaria até alguém reclamar que o saldo não bate.
> Com Pandera, isso vira uma falha explícita e legível na entrada, antes
> de qualquer transformação."

### 4.3 Por que matching em duas camadas (exato → fuzzy), e não tudo fuzzy?

> "Comparar tudo por similaridade de texto desde o início pareceria mais
> simples, mas abre espaço para falso positivo sem necessidade — duas
> empresas com nome parecido não são a mesma transação. Por isso eu só
> uso fuzzy matching no que não achou par exato, limito aos candidatos
> com data e valor próximos, exijo um score mínimo, e registro esse score
> na saída. Qualquer pessoa pode abrir a planilha final e ver exatamente
> como cada conciliação foi decidida — isso é o que torna o resultado
> auditável, requisito não-negociável em dado financeiro."

### 4.4 Por que Airflow para algo que roda 1x por dia?

> "Um cron já resolveria o agendamento puro. Airflow entra porque dá,
> sem eu escrever lógica extra: retries automáticos se o arquivo estiver
> temporariamente bloqueado, histórico visual de cada execução, e um
> caminho natural de crescimento se no futuro eu precisar encadear mais
> fontes no mesmo pipeline — sem precisar reescrever a orquestração."

### 4.5 Por que dados sintéticos (Faker) em vez de dados reais anonimizados?

> "Um projeto público no GitHub não pode conter nenhum dado real de
> empresa, nem anonimizado — anonimização mal feita é um risco conhecido
> de reidentificação. Gerei dados fictícios que reproduzem os mesmos
> tipos de caso (conciliado, divergente em valor, órfão em cada lado,
> caso que só casa via fuzzy) e esses mesmos dados servem de fixture
> para os testes automatizados."

---

## 5. Qualidade de engenharia (o que prova que não é "só um script")

Liste e, se possível, mostre ao vivo:

1. **Testes automatizados** (`pytest --cov=reconciler`) — 93% de
   cobertura, incluindo um teste de integração ponta a ponta que gera
   dados sintéticos e roda o pipeline completo.
2. **CI no GitHub Actions** — todo push roda lint (`ruff`) e os testes
   automaticamente. Mostre o badge/histórico de execuções no GitHub.
3. **Docker** — o pipeline roda igual em qualquer máquina
   (`docker build` + `docker run`), sem "na minha máquina funciona".
4. **Separação de responsabilidades** — `extract.py`, `transform.py`,
   `match.py`, `export.py` são funções puras testáveis isoladamente.
5. **Configuração via Pydantic Settings** — nenhum caminho ou tolerância
   fica hardcoded no meio da lógica de negócio.

---

## 6. Perguntas que provavelmente vão te fazer (e como responder)

**"Como você garante que não perde nenhum registro no processo?"**
> Tenho um teste (`test_match.py`) que verifica que a soma de linhas da
> saída é igual ao maior número de registros de entrada — ou seja, todo
> lançamento de origem aparece em exatamente uma linha do resultado,
> conciliado ou não.

**"O que acontece se a Koncili mudar o formato da planilha?"**
> O Pandera valida o schema na extração (`extract.py`). Se uma coluna
> obrigatória não existir ou o tipo não bater, o pipeline falha
> imediatamente com uma mensagem clara, em vez de silenciosamente gerar
> um resultado incorreto.

**"Por que não usar só Excel/VBA, que é o que a empresa provavelmente já usa?"**
> VBA não tem testes automatizados, não versiona bem em Git, e não separa
> lógica de apresentação. Python com esse pipeline dá rastreabilidade
> (histórico em SQLite), testabilidade e permite crescer (novas fontes,
> mais regras) sem reescrever tudo.

**"Esse projeto rodaria em produção como está?"**
> Seria um bom MVP. Para produção eu mudaria pelo menos três coisas: (1)
> trocar o SQLite do Airflow local por Postgres + executor distribuído,
> (2) mover credenciais/caminhos sensíveis para um secrets manager em vez
> de `.env`, e (3) adicionar alertas (Slack/e-mail) quando o percentual
> de divergências passar de um limite — hoje isso só aparece no log.

**"Qual foi a parte mais difícil?"**
> Decidir onde a linha entre match exato e fuzzy devia ficar — matching
> fuzzy sem critério gera falso positivo, mas ser rígido demais deixa
> casos óbvios sem conciliar. A solução foi limitar o fuzzy aos candidatos
> já próximos em data/valor e exigir um score mínimo configurável, sempre
> registrado na saída.

---

## 7. Encerramento sugerido

> "O código completo, com README, decisões de arquitetura documentadas
> e CI rodando, está no GitHub: github.com/Pruppety/koncili-omie-reconciliation.
> Qualquer dúvida de uma parte específica eu posso abrir o código agora e
> mostrar."

Tenha o repositório aberto numa aba durante a conversa — poder mostrar
o CI verde e os testes passando ao vivo é mais forte que qualquer slide.
