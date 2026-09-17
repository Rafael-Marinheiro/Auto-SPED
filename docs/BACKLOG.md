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
- [ ] Extrair, por partes, as normalizações homologadas de `main_fast.py` para
  serviços testáveis.
- [x] Centralizar normalizações de CST, CFOP, NCM, CEST, tipo de item e alíquota.
- [x] Criar modelos tipados para empresa, documento, item e tributos.
- [x] Criar resumo tipado da captura para a futura interface.
- [x] Expor prévia da captura por CLI, com tabela e JSON.
- [ ] Criar testes de paridade entre a emissão legado e a nova emissão para
  períodos anonimizados.

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

- [ ] Criar interface Windows em PySide6.
- [x] Definir regras ACID e heurísticas de Nielsen para a interface.
- [ ] Permitir escolher capturador, banco, período e arquivo de destino.
- [ ] Exibir progresso, log, resumo e relatório de inconsistências.
- [ ] Criar tela “Mapa de captura” com origem, transformação e destino SPED.
- [ ] Registrar histórico local das emissões e correções aplicadas.

## Fase 4 — Ecossistema de conectores (quinta)

- [ ] Publicar guia e projeto-base para novos capturadores.
- [ ] Suportar configuração declarativa para mapeamentos simples.
- [ ] Criar adaptadores de referência para PostgreSQL e importação de XML/CSV.
- [ ] Criar suíte de certificação para conectores de terceiros.

## Fase 5 — Distribuição e qualidade (sexta)

- [ ] Automatizar testes, lint e verificação de tipos no GitHub Actions.
- [x] Automatizar a suíte de testes no GitHub Actions.
- [ ] Empacotar aplicativo Windows e instalador.
- [ ] Versionar alterações de layout e regras fiscais.
- [ ] Publicar documentação de implantação, segurança e solução de problemas.
