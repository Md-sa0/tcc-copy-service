# Fontes acrescentadas na revisão de 6 de novembro de 2026

Conferência assistida por IA, separada da revisão pessoal solicitada ao aluno. As dez fontes anteriores e suas consultas estão em `fontes_e_buscas_original.md`. O artigo passou a ter 17 referências. Não há alegação de revisão sistemática ou leitura integral de livros cujo acesso foi parcial.

| Fonte | Endereço primário conferido | Uso e limite |
|---|---|---|
| Bang, Fu (2023), GPTCache | https://aclanthology.org/2023.nlposs-1.24/ ; DOI 10.18653/v1/2023.nlposs-1.24 | Cache semântico; autor, ano, páginas 212–218 e texto primário conferidos. Não transferir ganhos numéricos ao CopyLab. |
| Chen, Lingjiao; Zaharia, Matei; Zou, James (2024), FrugalGPT | https://lingjiaochen.com/papers/2024_FrugalGPT_TMLR.pdf | Primeira página identifica TMLR, dezembro de 2024; versão publicada adotada em vez de datar pelo preprint de 2023. Seleção adaptativa de modelos. |
| Rundgren, Anders; Jordan, Bret; Erdtman, Samuel (2020), RFC 8785 | https://www.rfc-editor.org/rfc/rfc8785.txt | JCS é especificação informativa. Seção 3.1 exige preservar strings; não atribuir conformidade JCS à serialização Python do projeto. |
| Unicode Consortium (2025), UAX #15 | https://www.unicode.org/reports/tr15/tr15-57.html | Revisão 57, Unicode 17.0.0, 30/07/2025. Referência versionada sobre NFC, não alegação de que o runtime usa exatamente essa versão do banco Unicode. |
| Peffers et al. (2007) | https://www.jmis-web.org/articles/765 ; DOI 10.2753/MIS0742-1222240302 | JMIS 24(3), 45–77. Seis atividades conferidas no resumo oficial; tentativa de PDF em repositório CERN retornou 403. Não alegar leitura integral nem adoção integral de procedimentos não consultados. |
| Wohlin et al. (2012) | https://link.springer.com/book/10.1007/978-3-642-29044-2 | Autores, editora, ano e DOI conferidos. Uso restrito à organização geral do processo descrita no conteúdo editorial acessível. Livro integral não obtido. |
| Georges, Buytaert e Eeckhout (2007) | https://users.elis.ugent.be/~leeckhou/papers/oopsla07-stat.pdf ; https://biblio.ugent.be/publication/417084 | Texto primário de 20 páginas no site do autor; registro universitário confirma ACM SIGPLAN Notices 42(10), 57–76. Variabilidade e rigor de benchmarking; não aplicar resultados de JVM a Python. |

## Reconferência específica solicitada

https://arxiv.org/abs/2501.10868v3 apresenta o título **JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models**, versão 3 de 27 de fevereiro de 2025. Esse é o título já usado na referência e mantido na revisão. O título anterior do preprint não foi usado.

## Consultas adicionais

Data de todas as consultas abaixo: 06/11/2026.

- `GPTCache semantic cache large language models 2023 paper` — incluído Bang.
- `FrugalGPT reducing costs improving performance large language models 2023 paper` — incluída publicação de 2024.
- `RFC 8785 JSON canonicalization unicode normalization UAX 15` — incluídos RFC e UAX versionado.
- `Georges Buytaert Eeckhout 2007 statistically rigorous Java performance evaluation` — incluído texto primário do autor.
- `Peffers Tuunanen Rothenberger Chatterjee 2007 design science research methodology six activities DOI` e `site.jmis-web.org Peffers 2007 design science research methodology` — incluída fundamentação das atividades, com acesso parcial declarado.
- `Wohlin Runeson Host Ohlsson Regnell Wesslen Experimentation Software Engineering 2012 Springer DOI` — incluído uso restrito ao processo descrito pela editora.
- `Hevner March Park Ram 2004 design science information systems research pdf seven guidelines` — explorado, não incluído; adotado Peffers para evitar referências meramente acumuladas.

O Apêndice B sintetiza decisões da revisão narrativa. A ausência de Hevner e Jain não é uma omissão de requisito obrigatório: a orientação oferecia alternativas para fundamentação metodológica e benchmarking; foram utilizados Peffers e Georges.
