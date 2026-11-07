# Registro de fontes e buscas do artigo CopyLab

Data da consulta: 5 de novembro de 2026. Revisão narrativa orientada pelo problema, sem protocolo de revisão sistemática. Este registro documenta as consultas e fontes utilizadas; não representa uma contagem exaustiva dos resultados do buscador. As fontes institucionais e os critérios extraídos delas estão em `00_mapa_das_diretrizes.md`.

## Consultas realizadas

- `JSONSchemaBench constrained decoding structured outputs Geng 2025 arxiv`
- `Efficient Guided Generation for Large Language Models Willard Louf 2023 arxiv`
- `large language models advertising text generation ecommerce product descriptions evaluation paper`
- `site.usenix.org NSDI 2013 scaling memcache facebook lease thundering herd`
- `site.ai.google.dev/gemini-api/docs/structured-output "semantic"`
- `Hevner March Park Ram Design Science Information Systems Research 2004 artifact evaluation`
- `site.misq.umn.edu design science information systems research hevner 2004`

As duas últimas consultas exploraram uma classificação metodológica que não foi adotada como fundamento no artigo. O trabalho de Hevner não foi incluído nas referências. O guia de escrita fornecido pela faculdade foi tratado como orientação de elaboração, sem atribuir sua leitura à obra original de Wazlawick. Não se presumiu leitura de livros apenas mencionados nos materiais.

## Fontes científicas empregadas

1. **Koto, Lau e Baldwin (2022)**. *Can Pretrained Language Models Generate Persuasive, Faithful, and Informative Ad Text for Product Descriptions?* ACL Anthology, ECNLP, p. 234–243. [Registro e PDF](https://aclanthology.org/2022.ecnlp-1.27/). DOI: 10.18653/v1/2022.ecnlp-1.27. Utilização: diferenciar fidelidade, informatividade e persuasão; não foi transferido resultado quantitativo desse estudo ao CopyLab.
2. **Willard e Louf (2023)**. *Efficient Guided Generation for Large Language Models*, versão 4. [Registro](https://arxiv.org/abs/2307.09702v4), [PDF](https://arxiv.org/pdf/2307.09702v4). DOI: 10.48550/arXiv.2307.09702. Utilização: geração guiada por restrições e distinção em relação à validação posterior. O CopyLab não implementa o decodificador proposto.
3. **Geng et al. (2025)**. *JSONSchemaBench: A Rigorous Benchmark of Structured Outputs for Language Models*, versão 3. [Registro](https://arxiv.org/abs/2501.10868v3), [PDF](https://arxiv.org/pdf/2501.10868v3). DOI: 10.48550/arXiv.2501.10868. Utilização: eficiência, cobertura e qualidade como dimensões distintas. Utilizou-se o título da versão 3, não o título anterior do preprint. O benchmark não foi executado no CopyLab.
4. **Liu et al. (2025)**. *LLMs for Customized Marketing Content Generation and Evaluation at Scale*. Autores: Haoran Liu, Amir Tahmasbi, Ehtesham Samhaque e Purak Jain. [Amazon Science](https://www.amazon.science/publications/llms-for-customized-marketing-content-generation-and-evaluation-at-scale), [PDF](https://cdn.amazon.science/50/cd/89210b7449df8dc810b79369da1b/llms-for-customized-marketing-content-generation-and-evaluation-at-scale.pdf). Utilização: contrastar avaliação publicitária e avaliação operacional; não foram atribuídos ganhos comerciais ao CopyLab.
5. **Nishtala et al. (2013)**. *Scaling Memcache at Facebook*. USENIX NSDI, p. 385–398. [Registro](https://www.usenix.org/conference/nsdi13/technical-sessions/presentation/nishtala), [PDF](https://www.usenix.org/system/files/conference/nsdi13/nsdi13-final170_update.pdf). Utilização: coordenação de solicitações após ausência de cache. Não se equiparou aquele sistema ao bloqueio Redis local.

## Documentação e especificação

6. **Google**. [Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output). Schema e necessidade de validação semântica. O conteúdo foi recuperado diretamente do endereço oficial quando o mecanismo de leitura web não o apresentou.
7. **Pydantic**. [Strict mode](https://docs.pydantic.dev/latest/concepts/strict_mode/). Modos de validação e limites da redução de coerção. A documentação não substitui a inspeção da configuração efetiva dos modelos do projeto.
8. **Redis**. [Distributed locks with Redis](https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/). Aquisição condicional, prazo e identificação de proprietário. O projeto usa liberação Lua condicionada; não foi descrito como implementação de Redlock.
9. **FastAPI**. [Concurrency and async / await](https://fastapi.tiangolo.com/async/). Distinção entre concorrência e paralelismo. A documentação não foi usada como evidência de desempenho medido.
10. **NIST (2015)**. [Secure Hash Standard, FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final). [DOI](https://doi.org/10.6028/NIST.FIPS.180-4). Especificação de SHA-256. A norma não define a equivalência de atributos de produto, estabelecida no código.

## Critérios e limites

Foram selecionadas fontes primárias acessíveis com relação direta ao problema. Textos agregadores não foram usados como fundamento científico. Documentação oficial sustenta descrições técnicas; resultados do CopyLab derivam exclusivamente dos registros próprios. Não há alegação de revisão exaustiva, novidade universal, avaliação humana do conteúdo ou leitura integral de toda a bibliografia mencionada nas fontes.


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
