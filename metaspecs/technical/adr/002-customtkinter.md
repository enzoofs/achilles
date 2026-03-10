# ADR-002: CustomTkinter como Framework UI

## Status
Aceito

## Contexto
Opções consideradas: tkinter puro, CustomTkinter, PyQt5/6, GTK (PyGObject), Electron/Tauri.

## Decisão
CustomTkinter sobre tkinter.

## Justificativa
- **Aparência moderna**: Tema escuro nativo, widgets arredondados, sem parecer app dos anos 90
- **Leve**: Única dependência pip (customtkinter), sem pacotes de sistema pesados
- **API familiar**: Mesma API do tkinter, curva de aprendizado zero
- **Catppuccin**: Fácil de aplicar tema Catppuccin Mocha com cores hex
- **Sem Qt/GTK**: Evita dependências de sistema complexas no Arch

## Alternativas Rejeitadas
- **tkinter puro**: Aparência datada, sem tema escuro nativo
- **PyQt**: Licenciamento complicado (GPL), pesado
- **GTK**: Bom no Linux mas verboso, curva de aprendizado maior
- **Electron/Tauri**: Overengineering para este caso de uso

## Consequências
- Requer venv por causa do PEP 668 do Arch
- Requer pacote `tk` do sistema (`sudo pacman -S tk`)
- Limitações de layout do tkinter persistem (pack/grid/place)
