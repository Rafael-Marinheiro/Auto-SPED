# Backlog de implementação — Auto-SPED

## Princípios inegociáveis

- A emissão atual para `DADOS.FDB` continua disponível até a nova rota produzir
  saídas equivalentes e validadas no PVA.
- Banco, arquivos SPED, credenciais, XMLs e relatórios de clientes não são
  versionados.
- O núcleo fiscal não depende de nomes de tabelas ou de um ERP específico.
- Correções no banco exigem prévia, confirmação explícita e trilha de auditoria.

## Fase 0 — Estabilização e segurança (primeira)

- [x] Manter o fluxo legado homologado sem alteração.
- [x] Ignorar dados fiscais e bancos locais no Git.
- [x] Registrar o contrato inicial de capturadores.
- [ ] Remover do histórico remoto arquivos fiscais eventualmente já publicados.
- [x] Criar repositório limpo `Auto-SPED` e migrar somente código, testes e
  exemplos anonimizados.
- [ ] Definir licença, política de suporte e versão mínima do Python.

## Fase 1 — Núcleo reutilizável (segunda)

- [x] Criar o contrato `FiscalDataProvider`.
- [x] Criar o primeiro capturador Firebird/ERP São Pedro sem alterar consultas.
- [x] Expor mapa detalhado de captura (origem Firebird e destino SPED).
- [x] Criar o caso de uso de geração independente da fonte.
- [x] Parametrizar o fluxo mensal homologado por banco, período e saída.
- [x] Permitir selecionar o cliente Firebird (`fbclient`) por emissão e documentar
  compatibilidade de versão e arquitetura.
- [x] Extrair, por partes, as normalizações homologadas de `main_fast.py` para
  serviços testáveis.
  - [x] Centralizar datas SPED, situação documental e formatação monetária.
  - [x] Remover do fluxo legado os parsers duplicados de situação, data e valor,
    reutilizando as normalizações compartilhadas com testes de paridade.
  - [x] Centralizar a normalização de produtos e itens (NCM, CEST, CFOP,
    CST de ICMS e CST de IPI) e reutilizá-la no fluxo legado.
  - [x] Centralizar a formatação decimal usada no pós-processamento de C100,
    C170, C190, E110 e E116, sem conversão intermediária para ponto flutuante
    e com escala explícita por tipo de campo.
- [x] Centralizar normalizações de CST, CFOP, NCM, CEST, tipo de item e alíquota.
- [x] Criar modelos tipados para empresa, documento, item e tributos.
- [x] Criar resumo tipado da captura para a futura interface.
- [x] Expor prévia da captura por CLI, com tabela e JSON.
- [x] Tornar o código de receita do E116 configurável por empresa/UF,
  removendo o valor legado fixo `1210` do núcleo reutilizável.
  - [x] Priorizar configuração da emissão e da empresa antes do padrão da UF.
  - [x] Usar `1210` automaticamente apenas quando a UF for RN, com base oficial.
  - [x] Bloquear UFs sem código configurado em vez de assumir código incorreto.
  - [x] Pesquisar fontes oficiais e ampliar os padrões inequívocos para AP, CE,
    GO, PB, PE, PR, RJ, SC e SP, mantendo configuração explícita nas UFs com
    códigos dependentes de atividade ou regime.
- [x] Criar testes de paridade entre a emissão legado e a nova emissão para
  períodos anonimizados.
  - [x] Cobrir período sem movimento com igualdade registro a registro.
  - [x] Cobrir período com NF-e, NFC-e e apuração de ICMS.
  - [x] Cobrir período com documentos de compra.

## Fase 2 — Validação preventiva (terceira)

- [x] Validar presença e formato de CST, CFOP, NCM, CEST e unidade.
- [x] Conferir totais de item e C100 antes da gravação.
- [x] Validar unicidade de documentos.
- [x] Validar totais de C170/C190 e registros de abertura/fechamento.
- [x] Validar CST de C170/C190, duplicidade de C100, ordem de blocos e contadores 9990/9999 no TXT.
- [x] Produzir relatório por severidade, origem e registro SPED afetado.
- [x] Implementar modo somente leitura e plano de correção com confirmação.
- [x] Implementar executor Firebird transacional restrito e recibo durável de correção.

## Fase 3 — Interface desktop (quarta)

- [x] Criar primeira tela Windows em PySide6 para emissão Firebird.
- [x] Definir regras ACID e heurísticas de Nielsen para a interface.
- [x] Criar seletor desktop de cliente Firebird com detecção local e download
  sob demanda de kits oficiais.
- [x] Permitir escolher capturador, banco, período e arquivo de destino.
- [x] Permitir escolher a codificação do TXT entre UTF-8, ISO-8859-1 e
  Windows-1252 na CLI e na interface desktop.
- [x] Exibir progresso, log, resumo e relatório de inconsistências antes da emissão.
- [x] Criar tela “Mapa de captura” com origem, transformação e destino SPED.
- [x] Registrar histórico local das emissões e correções aplicadas.

## Fase 4 — Ecossistema de conectores (quinta)

- [x] Publicar guia e projeto-base para novos capturadores.
- [x] Suportar configuração declarativa para mapeamentos simples.
- [x] Criar adaptadores de referência para PostgreSQL e importação de XML/CSV.
- [x] Criar suíte de certificação para conectores de terceiros.

## Fase 5 — Distribuição e qualidade (sexta)

- [x] Automatizar testes, lint e verificação de tipos no GitHub Actions.
  - [x] Tornar lint e tipos obrigatórios no núcleo reutilizável e conectores.
  - [ ] Incluir gradualmente `main_fast.py`, `database.py`, `writer.py` e desktop
    nas checagens estritas, mantendo os testes de paridade.
- [x] Automatizar a suíte de testes no GitHub Actions.
- [x] Empacotar aplicativo Windows e instalador.
  - [x] Automatizar pasta portátil e instalador por usuário no GitHub Actions.
  - [ ] Assinar executável e instalador com certificado de assinatura de código.
- [x] Versionar alterações de layout e regras fiscais.
  - [x] Criar catálogo de vigência para os leiautes 018, 019 e 020.
  - [x] Resolver COD_VER pela competência e bloquear versões incompatíveis.
  - [x] Integrar seleção automática/explícita à API, CLI e interface desktop.
  - [x] Documentar atualização anual e cobrir fronteiras com testes.
- [ ] Publicar documentação de implantação, segurança e solução de problemas.
