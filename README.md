# Reconciliação Automatizada Koncili x Omie

Pipeline de dados que extrai, valida, normaliza e concilia lançamentos
financeiros exportados da **Koncili** (plataforma de conciliação de
recebíveis/pagamentos) e da **Omie** (ERP), consolidando tudo em um único
relatório — com rastreabilidade total do que foi casado, do que diverge
em valor, e do que existe em apenas uma das fontes.

> Projeto desenvolvido como estudo de caso de Engenharia de Dados /
> Data Science (FIAP), simulando uma rotina real de conciliação financeira
> com dados **sintéticos** (nenhum dado real de empresa é usado ou necessário).

## Por que este projeto existe

Conciliação manual entre um ERP e uma plataforma de pagamentos é um
processo clássico de "planilha comparando planilha": lento, sujeito a
erro humano, e que normalmente não deixa rastro de *por que* duas linhas
foram consideradas a mesma transação. Este projeto resolve isso como um
pipeline de dados de verdade — com contratos de schema, testes
automatizados, matching auditável e execução agendada.

## Arquitetura

```
┌──────────────┐     ┌──────────────┐
│ koncili.xlsx │     │   omie.xlsx  │
└──────┬───────┘     └──────┬───────┘
       │  EXTRACT (pandas)  │
       ▼                    ▼
  Validação de schema (pandera) ── falha explícita se o layout mudar
       │                    │
       ▼                    ▼
  NORMALIZE  (datas, valores, CPF/CNPJ, texto → schema canônico comum)
       └─────────┬──────────┘
                  ▼
         MATCH EXATO (chave: cpf_cnpj + numero_documento,
                       tolerância de valor e de data)
                  │
                  ▼ (o que não casou)
         MATCH FUZZY (RapidFuzz na descrição, com score mínimo)
                  │
                  ▼
         CLASSIFICAÇÃO: CONCILIADO / DIVERGENTE_VALOR /
                         SOMENTE_KONCILI / SOMENTE_OMIE
                  │
                  ▼
   EXPORT: Excel consolidado (abas por status) + histórico em SQLite
                  │
                  ▼
        Orquestração: Apache Airflow (DAG diária, com retries)
```

Cada etapa é um módulo Python independente e testável
(`src/reconciler/extract.py`, `transform.py`, `match.py`, `export.py`),
orquestrado por `pipeline.py` — o mesmo código roda via CLI local,
dentro de Docker, ou agendado pelo Airflow, sem duplicação de lógica.

## Stack

| Camada | Ferramenta | Papel |
|---|---|---|
| Processamento | Pandas | Leitura, limpeza e transformação dos dados |
| Validação de schema | Pandera | Garante contrato de dados antes de qualquer transformação |
| Configuração | Pydantic Settings | Parâmetros validados (tolerâncias, caminhos), sem hardcode |
| Matching difuso | RapidFuzz | Casa lançamentos sem chave exata, com score de confiança |
| Orquestração | Apache Airflow | Agendamento, retries automáticos, histórico de execuções |
| Containerização | Docker / Docker Compose | Ambiente reproduzível em qualquer máquina |
| CLI | Typer | Execução manual via linha de comando |
| Testes | Pytest | Testes unitários (transform, match) e de integração (pipeline ponta a ponta) |
| CI | GitHub Actions | Lint + testes automáticos em todo push/PR |
| Logs | Loguru | Logging estruturado de cada etapa |
| Dados de demonstração | Faker | Gera planilhas sintéticas reproduzindo casos reais de conciliação |

Decisões de arquitetura (e os trade-offs considerados) estão detalhadas
em [`docs/decisions.md`](docs/decisions.md).

## Como rodar

### 1. Localmente

```bash
pip install -r requirements.txt
pip install -e .

# gera koncili.xlsx e omie.xlsx sintéticos em data/raw/
python scripts/generate_fake_data.py

# roda o pipeline completo
reconciler
```

O resultado consolidado fica em `data/output/conciliacao_consolidada.xlsx`,
com abas: `Todos`, `CONCILIADO`, `DIVERGENTE_VALOR`, `SOMENTE_KONCILI`,
`SOMENTE_OMIE` e `Resumo`.

### 2. Com Docker

```bash
docker build -t reconciler .
docker run -v "$(pwd)/data:/app/data" reconciler
```

### 3. Orquestrado pelo Airflow (ambiente de demonstração)

```bash
docker compose up
```

Acesse `http://localhost:8080` (usuário/senha exibidos no log do
container) e dispare manualmente a DAG `koncili_omie_reconciliation`.

### 4. Testes

```bash
pip install -e ".[dev]"
pytest --cov=reconciler
```

## Lógica de conciliação

1. **Match exato**: `cpf_cnpj + numero_documento`, aceitando diferença de
   até `data_tolerancia_dias` dias e `valor_tolerancia` reais (ambos
   configuráveis em `config.py` / `.env`).
2. **Match fuzzy** (fallback, só para o que sobrou do passo 1): compara a
   descrição com `RapidFuzz`, restrito a candidatos com data e valor
   próximos, e só aceita o match se o score ficar acima de
   `fuzzy_score_minimo`. O score fica registrado na saída — nenhum match
   fuzzy é "silencioso".
3. **Nada é descartado**: tudo que não casa em nenhuma etapa aparece como
   `SOMENTE_KONCILI` ou `SOMENTE_OMIE`, para investigação manual.

## Dados

Os dados usados aqui são **100% sintéticos**, gerados por
`scripts/generate_fake_data.py` com `Faker`. Isso é proposital: um
pipeline de conciliação financeira real nunca deveria ter seus dados de
produção publicados — o projeto demonstra a engenharia sem expor
informação sensível de nenhuma empresa.

## Licença

MIT — ver [LICENSE](LICENSE).
