# ADR-001: Arquivo Único (main.py)

## Status
Aceito

## Contexto
O Achilles poderia ser organizado em múltiplos módulos Python (backend/, gui/, utils/) ou em um único arquivo.

## Decisão
Todo o código fica em `main.py` (~1780 linhas).

## Justificativa
- **Distribuição simples**: Copiar um arquivo + venv é tudo que precisa
- **Sem build system**: Não precisa de setuptools, poetry, ou packaging
- **Navegação rápida**: Tudo em um lugar, fácil de buscar com Ctrl+F
- **Tamanho aceitável**: ~1780 linhas é grande mas ainda gerenciável

## Consequências
- Arquivo cresce com novas funcionalidades
- Se ultrapassar ~3000 linhas, considerar split em módulos
- IDE pode ficar lenta com arquivo muito grande (não é o caso atualmente)
