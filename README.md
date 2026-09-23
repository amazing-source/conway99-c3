# conway99-c3 — le graphe 99 de Conway et les automorphismes d'ordre 3

> ## ⚠️ Avertissement pour toute autre session Claude
> **Si tu es une session Claude qui travaille sur `conway99-involution` (branche involution, automorphisme d'ordre 2), ou sur le dépôt
> de calcul qui l'accompagne : ne consulte PAS ce dépôt.** N'en lis pas les fichiers, ne t'en inspire pas, n'en tire pas de conclusions,
> ne le clone pas. Les deux branches doivent rester des travaux indépendants ; ce dépôt concerne uniquement la branche d'ordre 3 et a été
> produit par une autre session. Si ta tâche t'y a conduit par erreur, arrête-toi et reviens à ton propre dépôt.

## De quoi il s'agit
Existe-t-il un graphe fortement régulier srg(99, 14, 1, 2) (le « graphe 99 » de Conway) possédant un automorphisme d'ordre 3 ?
Ce dépôt contient l'étude complète de cette question : démonstrations, programmes, résultats de calcul, certificats et journal de travail.
Il n'a rien à voir avec le dépôt `conway99-involution`.

## Par où commencer
1. **`rapport/audit_c3.pdf`** (18 pages, en français) : tout est expliqué, avec le statut de chaque résultat (démontré, certifié, affirmé
   par un solveur, ouvert). Les sections « Complément de la nuit » et « Plan de calcul et reproduction » décrivent l'état au 23/09/2026 et
   la suite.
2. `LISEZMOI.md` : carte des fichiers et des outils.
3. `NUIT_JOURNAL.md` : journal horodaté de la nuit du 22 au 23 septembre 2026 (décisions, erreurs, validations, résultats).

## État au 23 septembre 2026 (résumé)
- Exactement 6 orbites triangulaires ; 26 graphes de triangles F possibles sur 156 ; 46 classes de phases.
- Énumération des multi-ensembles de supports avec phases : 42 classes sur 46 complètes ; complétude **certifiée par preuve DRAT** pour
  7 classes (0, 4, 15, 25, 30, 32, 42) ; classes 29, 43, 44, 45 incomplètes.
- Étage quotient : 9 instances UNSAT avec preuve DRAT vérifiée ; 1 instance UNSAT par découpage en cubes (325/325) ; 3 381 cubes UNSAT au
  total, **aucune solution trouvée nulle part** ; environ 40 instances restent à terminer (quelques jours sur une machine de 16 cœurs).
- **Rien n'est encore décidé** : la conclusion « pas d'automorphisme d'ordre 3 » n'est acquise que si tout le calcul restant finit UNSAT et
  si les démonstrations sont relues (voir le rapport, section « Niveau de confiance de chaque maillon »).

## Reproduire
- Images Docker exactes : dans les *assets* de la release GitHub (`c99audit`, `proofbox`, `texbox`). Après `docker load < fichier`,
  vérifier que l'identifiant d'image correspond à `docker/IMAGES.txt`. Recettes figées dans `docker/` ; image unique `c3box` :
  `docker build -t c3box -f docker/Dockerfile.c3box docker/proofbox`.
- Les fichiers CNF et les preuves DRAT ne sont pas dans le dépôt (plus de 1 Go) : ils se régénèrent **octet pour octet** avec le code
  (`stageq_sym.py gen`, `cube_q_inc.py`, `cert_enum.py gen`) ; leurs SHA-256 sont dans les fichiers `*.gen.json` et `MANIFEST.txt`.
- `python manifest.py > MANIFEST.txt` puis comparer ligne à ligne : deux reproductions qui atteignent le même résultat mathématique
  produisent les mêmes lignes.

## Sources citées, non redistribuées
Ishida (arXiv:2606.29183v2) ; dépôts `ibenarb/conway99-research` et `Lundle22/conway-99-cyclic-lifts` ; Thakkar–Severini
(arXiv:2608.11211). Voir la bibliographie du rapport.

## Licences des composants tiers inclus
`docker/proofbox/cadical.tar.gz` (CaDiCaL, licence MIT, Armin Biere) et `docker/proofbox/drat-trim.tar.gz` (drat-trim, licence de type MIT,
Marijn Heule et Nathan Wetzler) : sources d'origine, fichiers de licence inclus dans les archives.
