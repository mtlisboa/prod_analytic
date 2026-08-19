# API GraphQL de análise

Módulo de consultas analíticas somente leitura. Operações de cadastro, edição e exclusão não fazem parte deste esquema.

## Endpoint e autenticação

- Endpoint: `/api/analytics/graphql/`
- Método recomendado: `POST`
- Autenticação: sessão Django do usuário conectado
- IDE em desenvolvimento: abra o endpoint com `GET`
- Formato do corpo: `{"query": "...", "variables": {}}`

Todos os resolvers limitam exercícios, técnicas e séries ao usuário autenticado.

## Campos disponíveis

| Enum | Campo | Tipo | Unidade | Funções |
|---|---|---|---|---|
| `EXERCISE` | Exercício | categoria | — | `RAW`, `COUNT` |
| `SET_POSITION` | Número da série | número | série | todas |
| `WEIGHT` | Força/carga | número | kg | todas |
| `REPS` | Repetições totais | número | repetições | todas |
| `PARTIAL_REPS` | Repetições parciais | número | repetições | todas |
| `PARTIAL_REPS_RATIO` | Repetições parciais / total | número | % | todas |
| `NON_PARTIAL_REPS` | Repetições totais - parciais | número | repetições | todas |
| `EXECUTION` | Tempo de execução | número | s | todas |
| `REST` | Tempo de descanso | número | s | todas |
| `TECHNIQUE` | Técnica | categoria | — | `RAW`, `COUNT` |
| `DATE` | Data | categoria | — | `RAW`, `COUNT` |

Funções numéricas: `RAW`, `COUNT`, `SUM`, `AVG`, `MIN` e `MAX`. O campo `analysisFields` é a fonte oficial para montar clientes dinamicamente; ele informa as funções aceitas por campo.

## 1. Catálogo de campos

```graphql
query AnalysisFields {
  analysisFields {
    key
    label
    kind
    unit
    groupable
    supportedFunctions { key label }
  }
}
```

## 2. Catálogo de filtros

```graphql
query AnalysisCatalog {
  analysisCatalog {
    exercises { id name }
    techniques { id name }
  }
}
```

## 3. Análise temporal

`timeAnalysis` mantém o eixo X como tempo. `period` aceita `DAILY`, `WEEKLY` e `MONTHLY`. Cada item de `lines` combina campo e função. Cada combinação de `groupBy` gera uma linha diferente.

```graphql
query TimeAnalysis($input: TimeAnalysisInput!) {
  timeAnalysis(input: $input) {
    x { label unit kind }
    y { label unit kind }
    series { label points { x y } }
  }
}
```

Variáveis de exemplo:

```json
{
  "input": {
    "startDate": "2026-08-01",
    "endDate": "2026-08-31",
    "period": "WEEKLY",
    "lines": [
      {"field": "WEIGHT", "function": "AVG"},
      {"field": "REST", "function": "SUM"},
      {"field": "SET_POSITION", "function": "COUNT"}
    ],
    "groupBy": ["EXERCISE"],
    "exerciseIds": [],
    "techniqueId": null
  }
}
```

## 4. Comparação dinâmica

`comparisonAnalysis` aceita um campo em X e várias linhas configuráveis em Y, cada
uma com campo e função independentes. `groupBy` aceita vários campos e multiplica
cada linha Y pelas combinações de classes encontradas.

```graphql
query ComparisonAnalysis($input: ComparisonAnalysisInput!) {
  comparisonAnalysis(input: $input) {
    x { label unit kind }
    y { label unit kind }
    series { label points { x y } }
  }
}
```

Exemplo: força e descanso por número da série, com linhas para cada exercício e técnica:

```json
{
  "input": {
    "startDate": "2026-08-01",
    "endDate": "2026-08-31",
    "x": {"field": "SET_POSITION", "function": "RAW"},
    "lines": [
      {"field": "WEIGHT", "function": "AVG"},
      {"field": "REST", "function": "AVG"}
    ],
    "groupBy": ["EXERCISE", "TECHNIQUE"],
    "exerciseIds": [],
    "techniqueId": null
  }
}
```

### Semântica das funções na comparação

- X e uma linha Y com `RAW`: retorna um ponto para cada série registrada.
- X com `RAW` e Y agregada: agrupa os registros pelo valor de X e aplica a função em Y.
- X agregada e Y com `RAW`: agrupa pelo valor de Y e aplica a função em X.
- X e Y agregadas: retorna um ponto agregado para cada linha definida por `groupBy`.
- Sem `groupBy`, cada configuração Y gera sua própria linha.

## Erros de validação

Funções incompatíveis com o tipo do campo retornam erro GraphQL. Por exemplo, `SUM` não pode ser aplicada a `EXERCISE`. Datas finais anteriores às iniciais e identificadores inválidos também são rejeitados pelo esquema ou pelos resolvers.
