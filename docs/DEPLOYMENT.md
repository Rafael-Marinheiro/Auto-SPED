# Implantação e operação

Este guia cobre a instalação por código-fonte e o aplicativo Windows. Ele não
substitui a homologação fiscal no PVA nem a política de backup da empresa.

## Requisitos

- Windows x64 para os artefatos distribuídos atualmente.
- Acesso de leitura ao banco Firebird e ao diretório de saída.
- Serviço Firebird compatível em execução.
- `fbclient.dll` da versão do Firebird e da mesma arquitetura do processo.
- Espaço livre para o TXT, logs locais e artefatos temporários.

Para instalação pelo código-fonte, use Python 3.10 a 3.12, faixa exercitada no
CI. O pacote Windows é construído com Python 3.12.

## Aplicativo Windows

O workflow **Windows package** produz uma pasta portátil e um instalador por
usuário. Baixe o artefato do commit ou da tag homologada, extraia-o em uma pasta
local e mantenha a versão anterior até concluir a validação.

Os binários ainda não possuem assinatura de código. Confirme a origem no
repositório oficial e leia a seção de cadeia de suprimentos em
[Segurança operacional](SECURITY.md) antes de ignorar qualquer aviso do
SmartScreen.

O instalador não inclui banco, credenciais, arquivos fiscais nem
`fbclient.dll`. Na primeira execução:

1. selecione o capturador Firebird;
2. informe o caminho do `.FDB`;
3. selecione ou baixe o cliente Firebird compatível;
4. escolha a competência e o destino do TXT;
5. revise resumo, leiaute fiscal e pré-validação;
6. emita e valide o arquivo no PVA.

## Instalação pelo código-fonte

```powershell
git clone https://github.com/Rafael-Marinheiro/Auto-SPED.git
cd Auto-SPED
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[desktop]"
python -m pytest -q
auto-sped-desktop
```

Para emissão automatizada, prefira parâmetros explícitos:

```powershell
python main_fast.py --database "D:\Fiscal\DADOS.FDB" --start-date 2026-08-01 --end-date 2026-08-31 --output "D:\Fiscal\Saidas\sped-2026-08.txt" --fbclient "C:\Program Files\Firebird\Firebird_2_5\bin\fbclient.dll"
```

O `main_fast.py` continua sendo o fluxo mensal homologado para o
`DADOS.FDB`. Novos capturadores não devem alterar suas consultas.

## Conta e permissões

Use uma conta Windows dedicada quando possível. Para geração e pré-validação,
conceda somente leitura no banco e escrita apenas no diretório de saída e no
perfil local do Auto-SPED. Não execute como administrador sem necessidade.

Correções no banco são uma função separada: exigem plano confirmado, executor
restrito e permissão de atualização. Faça backup verificado antes de qualquer
correção e nunca conceda escrita apenas para facilitar uma emissão comum.

## Dados locais

Por padrão, a aplicação usa `%LOCALAPPDATA%\Auto-SPED` para histórico e
clientes Firebird baixados. O arquivo SPED é gravado somente no destino
escolhido. Proteja essas pastas conforme a política de retenção da empresa.

O repositório e os pacotes não devem conter `.FDB`, XML, PDF fiscal, TXT SPED,
credenciais, logs de clientes ou relatórios de validação.

## Checklist mensal

1. Confirme competência, estabelecimento, UF e código de receita.
2. Confirme a versão do servidor e a DLL Firebird selecionada.
3. Faça backup do banco segundo a rotina da empresa.
4. Execute a pré-validação e resolva erros antes da emissão.
5. Gere o TXT em um novo nome; não sobrescreva a última versão aceita.
6. Valide no PVA e arquive o TXT aceito com seu recibo fora do repositório.
7. Registre a versão/commit do Auto-SPED usada na emissão.

## Atualização e rollback

Antes de atualizar, preserve o instalador anterior e não altere o banco. Instale
a nova versão, gere um período anonimizado ou já conhecido e compare a saída.
Se houver regressão, volte ao pacote anterior; os formatos do banco não são
migrados pelo Auto-SPED.

Para releases, uma tag `v*` aciona o build Windows. Publique as notas da
versão, os artefatos e, quando a assinatura estiver implantada, os checksums e
as informações do certificado.

Consulte também [Firebird](FIREBIRD_SETUP.md),
[versionamento fiscal](FISCAL_VERSIONING.md) e
[solução de problemas](TROUBLESHOOTING.md).
