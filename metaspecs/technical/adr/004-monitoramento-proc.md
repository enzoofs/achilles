# ADR-004: Monitoramento via /proc

## Status
Aceito

## Contexto
Instalações de repacks (especialmente FitGirl) podem levar horas e parecer travadas. Precisávamos monitorar atividade do processo sem dependências externas como `psutil`.

## Decisão
Ler diretamente de `/proc/[pid]/` para monitorar CPU, I/O e file descriptors.

## Justificativa
- **Zero dependências**: Não precisa de `psutil` ou `py-cpuinfo`
- **Dados ricos**: `/proc` expõe tudo que precisamos no Linux
- **Detecção de chunks**: Lendo `/proc/[pid]/fd` conseguimos ver qual `re_chunk_XXX.pak` está sendo processado
- **Detecção de travamento**: Comparando deltas de CPU e I/O entre leituras

## Implementação
| Fonte | Dado | Uso |
|-------|------|-----|
| `/proc/[pid]/stat` | campos 14+15 (utime+stime) | Delta de CPU entre leituras |
| `/proc/[pid]/io` | write_bytes | Volume de dados escritos em disco |
| `/proc/[pid]/fd` | symlinks | Detectar `re_chunk_XXX.pak` abertos |
| `/proc/[pid]/task/[pid]/children` | PIDs filhos | Árvore de processos (Wine spawna subprocessos) |

## Consequências
- Funciona apenas no Linux (não é problema, Achilles é Linux-only)
- Pode falhar com `PermissionError` se o processo rodar com outro usuário
- Requer tratamento de exceções robusto (processos podem morrer entre leituras)
