---
layout: default
---

<!--Text can be **bold**, _italic_, or ~~strikethrough~~.-->

<!--#[Link to another page](another-page).-->

<!--There should be whitespace between paragraphs.

There should be whitespace between paragraphs. We recommend including a README, or a file with information about your project.-->

<!--# [](#header-1)Exploring the Use of Automated API Migrating Techniques in Practice: An Experience Report on Android-->

## [](#header-2)Abstract
In recent years, open source software libraries have allowed developers to build robust applications by consuming freely available application program interfaces (API). However, when these APIs evolve, consumers are left with the difficult task of migration. Studies on API migration often assume that software documentation lacks explicit information for migration guidance and is impractical for API consumers. Past research has shown that it is possible to present migration suggestions based on historical code-change information. On the other hand, research approaches with optimistic views of documentation have also observed positive results. Yet, the effectiveness of both approaches has not been evaluated on large scale practical systems, leading to a need to affirm their validity. This paper reports our recent practical experience when leveraging approaches that are based on documentation and historical code changes, when migrating the use of Android APIs in FDroid apps. Our experiences suggest that migration through historical code-changes presents various challenges and that API documentation is undervalued. In particular, the majority of migrations from removed or deprecated Android APIs to newly added APIs can be suggested by a simple keyword search in the documentation. More importantly, during our practice, we experienced that the challenges of API migration lie beyond migration suggestions, in aspects such as coping with parameter type changes in new API. Future research may aim to design automated approaches to address the challenges that are documented in this experience report.



You can find the migration extraction scripts produced for this study in this repository.
[Here](https://github.com/LamotheMax/SEIP_2018_Android_API_Study/releases)
