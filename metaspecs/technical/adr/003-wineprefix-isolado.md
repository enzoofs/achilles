# ADR-003: WINEPREFIX Isolado por Jogo

## Status
Aceito

## Contexto
Wine usa um "prefix" (pasta com estrutura Windows) para cada ambiente. Usar o prefix padrão (`~/.wine`) para todos os jogos causa conflitos de DLLs e configurações.

## Decisão
Cada jogo recebe automaticamente um WINEPREFIX em `~/.local/share/achilles/prefixes/{slug}/`.

## Justificativa
- **Isolamento**: Um jogo que precisa de .NET 4.8 não interfere com outro que precisa de Visual C++ 2010
- **Limpeza fácil**: Deletar um prefix remove completamente o jogo sem afetar outros
- **Padrão XDG**: Dados em `~/.local/share/` seguem convenções Linux
- **Automático**: Usuário não precisa entender WINEPREFIXes

## Implementação
```python
slug = re.sub(r"[^a-zA-Z0-9]", "-", nome.lower()).strip("-")
wineprefix = os.path.join("~/.local/share/achilles/prefixes", slug)
```

## Consequências
- Usa mais espaço em disco (cada prefix ~1.5 GB com Wine base)
- Usuário avançado pode apontar para prefix customizado via propriedades do jogo
- Prefix é criado automaticamente pelo Wine na primeira execução
