# Solução de problemas

Comece pela mensagem completa, pelo período e pela versão do Auto-SPED. Não
altere o banco para eliminar um erro sem identificar a origem e manter backup.

## Diagnóstico mínimo

```powershell
git rev-parse --short HEAD
python --version
python -c "import struct; print(struct.calcsize('P') * 8)"
python main_fast.py --help
```

No aplicativo empacotado, registre o commit/tag do artefato, a versão do
Firebird, a arquitetura e o caminho da DLL. Compartilhe somente dados
anonimizados.

## Matriz rápida

| Sintoma | Causa provável | Ação |
| --- | --- | --- |
| `WinError 193` | Python/aplicativo e DLL com arquiteturas diferentes | Selecione `fbclient.dll` de 64 bits para o pacote Windows x64 |
| biblioteca não encontrada | caminho inválido ou sem permissão | selecione a DLL manualmente e confira leitura do arquivo |
| erro Firebird `-902` | serviço, porta, DSN ou rede indisponível | confirme serviço, porta 3050/configurada e acesso ao banco |
| pedido de outra DLL no mesmo processo | cliente Firebird já carregado | feche completamente o aplicativo e abra novamente |
| competência não cadastrada | catálogo fiscal não cobre o período | atualize as regras oficiais; não force o último leiaute |
| leiaute incompatível | versão manual não corresponde à competência | use seleção automática ou a versão indicada |
| caracteres inválidos no PVA | codificação inadequada | gere com UTF-8, ISO-8859-1 ou Windows-1252 conforme o ambiente |
| emissão muito lenta | grande volume de documentos e itens | acompanhe o progresso; não encerre enquanto houver atividade |
| SmartScreen | pacote ainda sem assinatura | confirme origem/commit; não ignore alertas de arquivo alterado |

## Conexão Firebird

1. Confirme que o arquivo `.FDB` existe e não é uma cópia incompleta.
2. Confirme qual serviço Firebird atende o banco e em qual porta.
3. Se houver várias instalações, informe `--fbclient` explicitamente.
4. Confira 32/64 bits com o comando de diagnóstico.
5. Reinicie o processo após trocar a DLL; o driver carrega um cliente por
   processo.
6. Teste primeiro a prévia ou a pré-validação, sem escrever no banco.

Consulte [Configuração do Firebird](FIREBIRD_SETUP.md).

## Geração demorada ou aparentemente parada

Bancos com muitas vendas e itens podem levar vários minutos. O
`main_fast.py` registra etapas em `execucao.log`; a interface mostra
progresso e mensagens. Verifique se a contagem de notas continua avançando e se
o processo consome CPU ou I/O antes de encerrá-lo.

Não execute duas emissões pesadas concorrentes contra o mesmo banco sem avaliar
o impacto no servidor. Se o log parar sempre na mesma nota, anote a posição,
modelo e número de forma anonimizada e reproduza em um banco de teste.

## Pré-validação e PVA

Erros de CST, CFOP, NCM, CEST, unidade, totais, duplicidade de C100 e contadores
devem ser corrigidos na origem ou por plano controlado. Não faça substituições
globais no TXT sem entender o efeito fiscal.

Fluxo recomendado:

```powershell
sped-generate --database DADOS.FDB --start-date 2026-08-01 --end-date 2026-08-31 --fbclient "C:\caminho\fbclient.dll" --validate-only --validation-report relatorio.json
python main_fast.py --database DADOS.FDB --start-date 2026-08-01 --end-date 2026-08-31 --output saida.txt --fbclient "C:\caminho\fbclient.dll"
sped-validate saida.txt --report relatorio-sped.json
```

Depois, importe no PVA. O validador interno reduz erros estruturais, mas o PVA e
a legislação da UF continuam sendo a validação fiscal final.

### NUM_DOC obrigatório ou duplicidade de C100

Confira modelo, série, chave, participante, operação e número no banco. Notas de
mesmo número podem ser distintas quando série ou chave diferem; não invente o
`NUM_DOC` a partir da chave sem confirmar o documento. Se o mesmo conjunto de
campos aparece duas vezes, investigue a origem duplicada antes de excluir linhas.

### CST obrigatório

Localize o item e confronte CST, CFOP, operação, regime e tributação. O valor não
deve ser deduzido apenas para satisfazer o PVA. Corrija o banco somente com
evidência, backup, confirmação e trilha de auditoria.

### Contadores e ordem de blocos

Não edite manualmente `9990` ou `9999` antes de executar
`sped-validate`. O escritor calcula os totalizadores a partir das linhas
finais. Erros de registro esperado, como abertura/fechamento de blocos, indicam
ordem ou presença incompatível e devem ser corrigidos na geração.

## Codificação e caminhos

Use um destino novo e gravável. Caminhos com espaços devem ficar entre aspas.
Se o PVA exibir acentos incorretos, gere outra cópia com `--encoding cp1252`
ou `--encoding iso-8859-1`; não recodifique em editor que possa alterar
delimitadores ou finais de linha.

## Onde encontrar informações

- Interface: botão **Ver histórico**.
- Histórico local: `%LOCALAPPDATA%\Auto-SPED\history.jsonl`.
- Log do fluxo homologado: `execucao.log` no diretório de execução.
- Relatório preventivo: caminho informado em `--validation-report`.
- Execuções de CI e build: aba **Actions** do repositório.

Antes de enviar qualquer arquivo ao suporte, remova CNPJ, CPF, IE, chaves,
nomes, endereços e valores reais. Prefira uma fixture mínima que preserve apenas
a estrutura do erro.

Consulte [Implantação](DEPLOYMENT.md) e [Segurança](SECURITY.md).
