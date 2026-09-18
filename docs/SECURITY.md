# Segurança operacional

O Auto-SPED processa dados fiscais e pode acessar um banco de produção. Trate o
aplicativo, seus arquivos de entrada e suas saídas como ativos sensíveis.

## Modelo de confiança

A geração comum lê o banco e grava um TXT no caminho escolhido. O aplicativo não
envia conteúdo fiscal para serviços externos. A função opcional de download do
cliente Firebird acessa somente URLs catalogadas de releases oficiais e armazena
a DLL no perfil local do usuário.

O projeto não é um cofre de credenciais nem um sistema de backup. A segurança do
servidor Firebird, do Windows, do PVA e do armazenamento dos recibos continua sob
responsabilidade do operador.

## Dados que não podem ser publicados

Nunca adicione ao Git, a issues, artefatos de CI ou mensagens públicas:

- bancos `.FDB` e cópias de segurança;
- TXT SPED, XML, PDF fiscal e recibos;
- credenciais, strings de conexão e arquivos `.env`;
- logs ou relatórios com CNPJ, CPF, chaves de acesso ou valores reais;
- DLLs e instaladores baixados para uso local.

O `.gitignore` oferece uma barreira adicional, mas não substitui a revisão do
`git status`. Se um dado real entrar no histórico, remover apenas o arquivo no
commit seguinte não é suficiente: interrompa a publicação, revogue segredos e
reescreva o histórico com procedimento controlado.

## Privilégio mínimo

Para geração e pré-validação, use credenciais de leitura. Restrinja escrita ao
diretório de saída e a `%LOCALAPPDATA%\Auto-SPED`. Não execute como
administrador e não abra o compartilhamento do banco para redes não confiáveis.

As correções Firebird são isoladas da geração. O executor atual:

- aceita somente a fonte e os campos explicitamente permitidos;
- exige token derivado do plano revisado;
- usa parâmetros SQL para valores e lista fechada para nomes de campo;
- verifica o valor anterior como pré-condição;
- aplica todas as mudanças em uma transação;
- executa rollback em caso de erro;
- gera recibo e trilha JSONL após o commit.

Uma falha ao persistir a auditoria depois do commit exige reconciliação manual;
não tente desfazer automaticamente uma transação já confirmada. Proteja o
arquivo de auditoria contra alteração e retenha-o segundo a política da empresa.

## Cliente Firebird

A DLL deve combinar com a versão do servidor e com a arquitetura do processo.
O seletor valida a arquitetura, limita downloads ao catálogo oficial, impede
travessia de diretórios no ZIP e não executa instaladores.

Limitação atual: os kits Firebird são baixados por HTTPS, mas seus hashes ainda
não estão fixados no catálogo do Auto-SPED. Em ambiente de alta garantia, baixe
o kit diretamente do projeto Firebird, confira assinatura ou checksum publicado
pelo fornecedor e selecione a DLL local. Não trate a ausência dessa verificação
como autorização para ignorar alertas do antivírus.

## Cadeia de suprimentos

Os executáveis e instaladores do Auto-SPED ainda não são assinados. Até a
implantação da assinatura:

1. obtenha artefatos apenas do repositório oficial;
2. confirme que o build corresponde ao commit ou tag homologada;
3. prefira reconstruir pelo workflow público ou pelo código-fonte;
4. faça varredura antimalware antes da distribuição interna;
5. não ignore um alerta que indique origem diferente ou arquivo modificado.

Dependências devem ser instaladas em ambiente virtual. Atualizações de
PySide6, PyInstaller, driver Firebird ou conectores exigem CI, teste de paridade
e novo build antes da produção.

## Retenção, logs e suporte

O histórico da interface fica em
`%LOCALAPPDATA%\Auto-SPED\history.jsonl` e contém metadados operacionais.
O fluxo mensal legado pode criar `execucao.log` no diretório corrente. Ambos
podem revelar caminhos, períodos e detalhes de erro; restrinja acesso, defina
retenção e sanitize antes de compartilhar.

Ao pedir suporte, envie a versão/commit, versão do Firebird, arquitetura,
mensagem de erro e um exemplo anonimizado. Substitua identificadores e valores
sem alterar a estrutura necessária para reproduzir o problema.

## Resposta a incidente

Se houver suspeita de vazamento ou binário adulterado:

1. pare novas emissões e preserve evidências;
2. desconecte o artefato suspeito do ambiente fiscal;
3. revogue credenciais possivelmente expostas;
4. compare o hash e a origem do pacote com o build homologado;
5. restaure a partir de backup verificado quando necessário;
6. registre impacto, período e arquivos envolvidos;
7. reporte a vulnerabilidade por canal privado, sem anexar dados fiscais reais.

Consulte [Implantação](DEPLOYMENT.md) e
[Solução de problemas](TROUBLESHOOTING.md).
