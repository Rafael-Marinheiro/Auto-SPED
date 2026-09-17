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
- [x] Criar o caso de uso de geração independente da fonte.
- [x] Parametrizar o fluxo mensal homologado por banco, período e saída.
- [ ] Extrair, por partes, as normalizações homologadas de `main_fast.py` para
  serviços testáveis.
- [x] Centralizar normalizações de CST, CFOP, NCM, CEST, tipo de item e alíquota.
- [ ] Criar modelos tipados para empresa, documento, item e tributos.
- [ ] Criar testes de paridade entre a emissão legado e a nova emissão para
  períodos anonimizados.

## Fase 2 — Validação preventiva (terceira)

- [x] Validar presença e formato de CST, CFOP, NCM, CEST e unidade.
- [x] Conferir totais de item e C100 antes da gravação.
- [x] Validar unicidade de documentos.
- [ ] Validar totais de C170, C190 e registros de abertura/fechamento.
- [ ] Produzir relatório por severidade, origem e registro SPED afetado.
- [ ] Implementar modo somente leitura e modo de correção com confirmação.

## Fase 3 — Interface desktop (quarta)

- [ ] Criar interface Windows em PySide6.
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
- [ ] Empacotar aplicativo Windows e instalador.
- [ ] Versionar alterações de layout e regras fiscais.
- [ ] Publicar documentação de implantação, segurança e solução de problemas.
