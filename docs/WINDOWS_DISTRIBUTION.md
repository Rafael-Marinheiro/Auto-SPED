# Distribuição Windows

O aplicativo pode ser gerado como pasta portátil e como instalador por usuário.
O pacote inclui Python e a interface PySide6, mas não inclui bancos, dados
fiscais, credenciais nem `fbclient.dll`.

## Build local

Requer Python 3.10 ou superior. Para gerar apenas a pasta portátil:

```powershell
python -m pip install -e ".[desktop,build]"
.\scripts\build_windows.ps1 -SkipInstaller
```

O resultado fica em `dist\Auto-SPED`. Para gerar também o instalador, instale o
Inno Setup 6 e execute o script sem `-SkipInstaller`. O instalador é gravado em
`dist\installer` e usa a versão declarada em `pyproject.toml`.

## Build no GitHub

O workflow **Windows package** pode ser iniciado manualmente e também roda ao
publicar uma tag `v*`. Ele disponibiliza dois artefatos: pasta portátil e
instalador.

## Firebird

Na primeira execução, selecione uma DLL local compatível ou use o download sob
demanda da interface. A arquitetura do cliente Firebird deve coincidir com a do
aplicativo, atualmente Windows x64. Consulte `FIREBIRD_SETUP.md`.

## Assinatura e segurança

Os builds atuais não possuem assinatura de código. O Windows pode exibir um
aviso do SmartScreen. Uma distribuição pública deve assinar o executável e o
instalador com certificado da organização e publicar checksums dos artefatos.

Nunca inclua um `DADOS.FDB`, SPED real, log, XML fiscal ou segredo dentro de
`packaging`, `build` ou `dist`.
