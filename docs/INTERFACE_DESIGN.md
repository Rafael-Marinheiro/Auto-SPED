# Design da interface — Auto-SPED

## Fluxo principal

```text
Escolher fonte e período
        ↓
Prévia da captura (somente leitura)
        ↓
Validar dados e arquivo de referência
        ↓
Revisar correções sugeridas
        ↓
Confirmar plano de correção
        ↓
Gerar SPED → validar TXT → abrir resultado
```

## Regras ACID para operações de correção

| Propriedade | Decisão de interface e serviço |
| --- | --- |
| Atomicidade | Um plano é executado inteiro em uma transação; qualquer falha aciona rollback. |
| Consistência | A interface mostra pré-condição, valor atual, proposta, regra fiscal e validação pós-gravação. |
| Isolamento | Uma execução bloqueia novos planos para a mesma fonte/período e mostra o estado da transação. |
| Durabilidade | Após commit, a aplicação guarda recibo com ID de transação, plano, usuário, horário e resultado. |

Regras adicionais:

- O modo padrão é **somente leitura**.
- A aplicação nunca corrige automaticamente um banco.
- Cada proposta exige justificativa, pré-condição e confirmação explícita.
- A confirmação usa o identificador do plano revisado.
- A geração do SPED sempre usa nova leitura após o commit.

## Heurísticas de Nielsen aplicadas

| Heurística | Aplicação no Auto-SPED |
| --- | --- |
| Visibilidade do estado | Progresso por etapa, contagem de documentos, log e estado da transação. |
| Correspondência com o mundo real | Termos fiscais como C100, CST, CFOP, nota, item e competência. |
| Controle e liberdade | Cancelar geração, descartar plano e voltar à prévia sem gravar. |
| Consistência | Mesma classificação de severidade em CLI, interface e relatórios. |
| Prevenção de erros | Pré-validação antes de gerar e confirmação antes de alterar banco. |
| Reconhecimento | Origem, campo, valor atual e destino SPED no mesmo painel. |
| Flexibilidade | Atalhos para revalidar, filtrar por severidade e exportar JSON. |
| Design minimalista | Detalhes técnicos ficam em “Ver origem/regra”. |
| Recuperação de erros | Registro, campo, origem, causa e ação sugerida em cada mensagem. |
| Ajuda contextual | Ajuda para CST, CFOP, registros SPED e regras de correção. |

## Critérios de aceite da primeira tela

- Não permite gravação antes de revisão e confirmação do plano.
- Exibe período, fonte, quantidade de documentos e total capturado.
- Mostra erros por severidade com origem e destino SPED.
- Mantém histórico local de geração e recibos de correção.
