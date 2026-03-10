# ADR-005: Debug Wine por Modo (Instalação vs Jogo)

## Status
Aceito

## Contexto
`WINEDEBUG=-all` era usado para tudo, o que impossibilitava diagnosticar falhas de instalação. O oposto (`WINEDEBUG` sem restrição) gera output massivo que polui a interface.

## Decisão
Dois modos de execução com níveis de debug diferentes:
- **Instalação**: `WINEDEBUG=+file,+loaddll,+seh` — mostra operações de arquivo, DLLs carregadas e exceções
- **Jogo**: `WINEDEBUG=-all` — silencioso para não impactar performance

## Justificativa
- Instalações precisam de diagnóstico para resolver problemas
- Jogos precisam de performance máxima sem output de debug
- Log completo salvo em arquivo permite análise posterior sem poluir a UI

## Implementação
- Parâmetro `modo` ("install" ou "play") no `ExecutorWine`
- Filtro inteligente na UI: só mostra linhas relevantes (erros, chunks, DLLs)
- Log completo não-filtrado salvo em `~/.config/achilles/logs/`
- Botão "Ver log" na pós-instalação para abrir o arquivo com xdg-open

## Consequências
- Logs de instalação ocupam espaço (podem chegar a dezenas de MB)
- Filtro de UI pode esconder linhas importantes se os keywords não cobrirem o caso
- Arquivo de log com timestamp permite comparar instalações diferentes
