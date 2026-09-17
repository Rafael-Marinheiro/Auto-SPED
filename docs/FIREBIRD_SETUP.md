# Configuração do cliente Firebird

O Auto-SPED acessa o banco por meio da biblioteca cliente do Firebird
(`fbclient.dll` no Windows). A DLL escolhida para a emissão precisa ser
compatível tanto com o banco/servidor Firebird utilizado quanto com a
arquitetura do Python que executa o programa.

## Escolha da DLL

Informe a DLL explicitamente quando houver mais de uma instalação Firebird na
máquina. Para o ambiente atual de Firebird 2.5 em 64 bits, por exemplo:

```powershell
python main_fast.py --database DADOS.FDB --start-date 2026-08-01 --end-date 2026-08-31 --output saida_sped_out_2026-08.txt --fbclient "C:\Program Files\Firebird\Firebird_2_5\bin\fbclient.dll"
```

Os comandos `sped-generate` e `sped-summary` aceitam o mesmo parâmetro
`--fbclient`.

```powershell
sped-summary --database DADOS.FDB --start-date 2026-08-01 --end-date 2026-08-31 --fbclient "C:\Program Files\Firebird\Firebird_2_5\bin\fbclient.dll"
```

Sem `--fbclient`, a aplicação preserva a compatibilidade legada: verifica
`FBCLIENT_PATH`, instalações locais conhecidas e, por último, deixa o sistema
localizar o nome padrão da biblioteca.

## Seletor desktop e downloads

Após instalar a opção `desktop` (`pip install -e ".[desktop]"`), execute
`auto-sped-desktop`. O seletor procura instalações locais, aceita a escolha
manual de uma DLL e oferece download sob demanda dos kits ZIP oficiais do
Firebird 2.5, 3.0, 4.0 e 5.0, em 32 ou 64 bits. A DLL é extraída para o perfil
local do usuário e não é versionada pelo Auto-SPED.

O catálogo usa os artefatos publicados pelo
[projeto Firebird](https://www.firebirdsql.org/en/downloads/). A série 2.5 é
mantida para compatibilidade, mas está descontinuada pelo projeto Firebird.

## Arquitetura e versão

- Python 64 bits requer `fbclient.dll` 64 bits; Python 32 bits requer DLL de
  32 bits. Confira o Python ativo com:

  ```powershell
  python -c "import struct; print(struct.calcsize('P') * 8)"
  ```

- Use a biblioteca cliente correspondente à versão do Firebird disponível no
  ambiente que fará a conexão. Em caso de atualização do servidor ou troca de
  banco, selecione a DLL daquela instalação antes de emitir.
- O `fdb` carrega a DLL uma única vez por processo. Se for necessário trocar de
  versão de `fbclient.dll`, finalize a aplicação e inicie uma nova execução.
  O Auto-SPED interrompe a operação com mensagem clara se uma segunda DLL for
  solicitada no mesmo processo.

## Diagnóstico rápido

- `WinError 193` ou erro de carregamento: normalmente há incompatibilidade
  entre 32 e 64 bits.
- Biblioteca não encontrada: confira o caminho passado em `--fbclient` e as
  permissões de leitura do arquivo.
- Erro de conexão (`-902`, servidor indisponível): confira o serviço Firebird,
  a porta e o DSN do banco. A escolha da DLL não inicia o servidor.

Nunca versione o banco `.FDB`, credenciais ou arquivos SPED de clientes no
repositório.
