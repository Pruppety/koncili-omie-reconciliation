# Decisões de arquitetura (ADRs resumidos)

Registro curto do "porquê" de cada escolha relevante — útil tanto para
quem for dar manutenção no projeto quanto para explicar as decisões em
entrevista técnica.

## 1. Pandas em vez de Polars/DuckDB

Para o volume alvo (planilhas de até centenas de milhares de linhas,
execução diária), pandas é suficiente e é o que o mercado mais usa e
reconhece. Polars/DuckDB entram como evolução natural se o volume
crescer (processamento columnar, lazy evaluation) — mas nesse estágio
seriam otimização prematura.

## 2. Pandera para contrato de dados, não só `try/except`

Pipelines financeiros falham de forma mais perigosa quando falham
*silenciosamente* — uma coluna renomeada na exportação da Koncili pode
gerar um relatório de conciliação errado sem nenhum erro visível.
Validar o schema explicitamente na entrada (`extract.py`) garante que
qualquer mudança de layout vira uma falha clara, não um dado corrompido.

## 3. Match exato primeiro, fuzzy como fallback explícito

Casar tudo por similaridade de texto desde o início seria mais "fácil",
mas erra por aceitar falsos positivos sem necessidade. A estratégia em
camadas (exato → fuzzy só no que sobrou, com score mínimo configurável
e score sempre registrado na saída) é o que torna o resultado auditável:
qualquer pessoa pode abrir a planilha final e ver *como* cada
conciliação foi decidida.

## 4. Airflow em vez de só um cron/script

Para uma rotina que roda 1x/dia, um cron já resolveria o agendamento —
mas Airflow adiciona, sem custo de código extra: retries automáticos em
falha transitória (ex: arquivo temporariamente bloqueado), histórico
visual de execuções, e um caminho natural de crescimento caso no futuro
seja necessário encadear mais fontes de dados no mesmo pipeline.

## 5. Separação extract / transform / match / export

Cada etapa é uma função pura que recebe e devolve um DataFrame no
schema esperado. Isso permite testar `transform.py` sem precisar ler um
Excel, e testar `match.py` sem depender da normalização — o que torna o
pipeline debugável etapa por etapa quando um caso específico "não casa
como devia".

## 6. Dados sintéticos via Faker, nunca dados reais no repositório

Um projeto de portfólio público não pode conter nenhuma informação real
de empresa (CNPJ, valores, fornecedores). O gerador de dados fake
(`scripts/generate_fake_data.py`) reproduz os mesmos tipos de caso
(conciliado, divergente, órfão em cada lado, caso que exige fuzzy) sem
expor nada sensível — e também serve de fixture para os testes
automatizados.
