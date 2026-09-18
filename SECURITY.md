# Política de segurança

## Versões suportadas

Durante a fase 0.x, somente a versão mais recente da branch `main` e o último
artefato/tag homologado recebem correções de segurança. O projeto ainda não
oferece SLA público.

## Relato de vulnerabilidades

Não publique detalhes exploráveis nem dados fiscais em uma issue. Use o recurso
privado **Report a vulnerability** da aba **Security** do GitHub quando ele
estiver disponível. Se não estiver, abra uma issue sem detalhes apenas para
solicitar um canal privado ao mantenedor.

Inclua versão/commit, impacto, pré-condições e passos mínimos com dados
anonimizados. Não anexe banco, SPED, XML, credenciais, logs reais ou chaves de
acesso.

## Operação segura

Leia o [guia de segurança operacional](docs/SECURITY.md) antes de implantar. Os
binários atuais não são assinados e o download de kits Firebird ainda não fixa
checksums no catálogo; essas limitações devem ser consideradas na distribuição.
