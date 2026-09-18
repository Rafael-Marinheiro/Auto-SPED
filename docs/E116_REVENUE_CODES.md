# Códigos de receita do E116 por UF

O campo `COD_REC` é estadual. Este catálogo cobre somente a obrigação `000`
(ICMS próprio a recolher) na apuração normal mensal. Regimes especiais,
atividade específica, substituição tributária, FECOP, DIFAL, importação e
débitos especiais podem exigir outro código.

## Padrões automáticos verificados

Pesquisa revisada em 17/09/2026. A opção informada na emissão ou no cadastro
da empresa sempre prevalece sobre estes padrões.

| UF | Código | Descrição oficial resumida | Fonte oficial |
|---|---:|---|---|
| AP | 1111 | ICMS normal — declaração | [SEFAZ/AP](https://sefaz.portal.ap.gov.br/conteudo/orientacoes/codigos-de-receitas) |
| CE | 1015 | ICMS regime mensal de apuração | [SEFAZ/CE](https://sefazlegis.sefaz.ce.gov.br/api/openFile?id=61b80fab-6f46-4663-a08b-5ccdaf5e4052) |
| GO | 108 | ICMS normal | [Economia/GO](https://orientacaotributaria.economia.go.gov.br/spo-web/perguntasfrequentes/perguntafrequente/20469) |
| PB | 1101 | ICMS normal | [SEFAZ/PB](https://www.sefaz.pb.gov.br/info/79-servicos/1297-emissao-do-dar) |
| PE | 005-1 | ICMS normal | [SEFAZ/PE](https://www.sefaz.pe.gov.br/Servicos/Programa-de-Conformidade-e-Autorregularizacao-Coopera/Paginas/validacao-preliminar-EFD.aspx) |
| PR | 1015 | Regime mensal de apuração | [Receita/PR](https://atendimento.fazenda.pr.gov.br/sacsefa/portal/assuntosReferente/12) |
| RJ | 021-3 | ICMS normal | [SEFAZ/RJ](https://portal.fazenda.rj.gov.br/fisco-facil/wp-content/uploads/sites/28/2023/09/manual-Fisco-Facil-versao11.pdf) |
| RN | 1210 | ICMS regime mensal de apuração | [Diário Oficial/RN](https://webdisk.diariooficial.rn.gov.br/Jornal/12022-08-19.pdf) |
| SC | 1449 | ICMS normal | [SEF/SC](https://legislacao.sef.sc.gov.br/html/portarias/2024/port_24_017.htm) |
| SP | 046-2 | Regime periódico de apuração | [SEFAZ/SP](https://legislacao.fazenda.sp.gov.br/Paginas/pcat1472009.aspx) |

## UFs que exigem configuração da empresa

Para `AC`, `AL`, `AM`, `BA`, `DF`, `ES`, `MA`, `MG`, `MS`, `MT`, `PA`, `PI`,
`RO`, `RR`, `RS`, `SE` e `TO`, a ferramenta não assume um código. A pesquisa
não encontrou um padrão oficial único e inequívoco aplicável a toda empresa em
apuração normal mensal, ou a tabela distingue atividade, regime ou modalidade.

Exemplos confirmados dessa ambiguidade:

- ES separa comércio (`121-0`), indústria (`122-8`), energia, comunicação e
  transporte na [tabela oficial](https://sefaz.es.gov.br/Media/Sefaz/Receita%20Estadual/TABELA%20DE%20C%C3%93DIGOS%20DA%20RECEITA%20ATUALIZADA_13%2007%2021.pdf).
- MG lista vários códigos possíveis para “ICMS Normal” na
  [tabela da SEF/MG](https://www.fazenda.mg.gov.br/empresas/impostos/icms/tabela.html).
- RS separa modalidade geral de comércio (`0221`) e indústria (`0222`) no
  [Apêndice XVI](https://receita.fazenda.rs.gov.br/upload/20161111103532apendice_xvi___in_re_08113_72810.pdf).
- AC publica códigos diferentes por atividade no seu
  [guia da EFD](https://sefaz.ac.gov.br/2021/?mdocs-file=1813).

Nessas UFs, informe o código na tela/CLI ou exponha no capturador um dos campos
`COD_REC_E116`, `E116_COD_REC` ou `COD_REC` nos dados da empresa.
