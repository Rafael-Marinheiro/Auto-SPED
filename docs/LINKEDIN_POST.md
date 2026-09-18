# Publicação do Auto-SPED no LinkedIn

## Texto sugerido

Transformei uma necessidade real do meu trabalho em um projeto open source:
o **Auto-SPED**, um gerador de EFD ICMS/IPI com arquitetura de capturadores
reutilizáveis.

O desafio inicial era emitir o SPED mensal a partir de um ERP com banco
Firebird sem perder o fluxo já homologado. Ao evoluir a solução, separei o que
era específico do banco da lógica fiscal. Hoje, um capturador traduz Firebird,
PostgreSQL, XML ou CSV para um contrato comum, enquanto o núcleo normaliza,
valida e escreve os registros do arquivo fiscal.

Alguns pontos que implementei:

- geração por CLI e interface desktop;
- seleção do cliente Firebird compatível com a versão e arquitetura;
- mapa de captura entre tabela, campo fiscal e registro SPED;
- validação preventiva de documentos, itens, CST, CFOP, NCM e totais;
- correções transacionais com confirmação, rollback e trilha de auditoria;
- versionamento do leiaute por competência;
- testes automatizados, lint, tipagem e empacotamento para Windows;
- contrato para que outros desenvolvedores criem seus próprios conectores.

Mantive o fluxo mensal usado em produção durante a refatoração, protegendo a
continuidade operacional com testes de paridade. Também removi dados fiscais
reais do escopo público: o repositório contém somente código, documentação e
exemplos fictícios.

O projeto está disponível sob licença MIT para estudo, adaptação e
colaboração:

https://github.com/Rafael-Marinheiro/Auto-SPED

Se você trabalha com ERP, integração fiscal, Python ou Firebird, ficarei feliz
em trocar experiências sobre conectores e validação de dados fiscais.

## Hashtags sugeridas

#Python #OpenSource #SPED #EFDICMSIPI #Firebird #ERP #Automacao
#EngenhariaDeSoftware #QualidadeDeSoftware #Portfolio

## Checklist antes de publicar

- Anexar `output/pdf/Auto-SPED_LinkedIn_Carrossel.pdf` como documento.
- Usar o título do documento: `Auto-SPED - do ERP ao arquivo fiscal`.
- Conferir se o repositório e a aba Actions estão públicos e acessíveis.
- Fixar a publicação na seção Destaques do perfil.
- Adicionar o projeto à seção Projetos com o link do GitHub.

## Descrição curta para a seção Projetos

Gerador open source de EFD ICMS/IPI em Python. Separa conectores de dados do
núcleo fiscal, suporta Firebird e fontes de referência, oferece validação
preventiva, mapa de captura, interface desktop, CLI, auditoria transacional e
distribuição para Windows.
