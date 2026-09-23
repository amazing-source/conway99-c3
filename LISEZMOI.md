# Branche C3 du graphe de Conway srg(99,14,1,2) — dossier de recherche

**Document de référence : `rapport/audit_c3.pdf`** (audit complet du 22 septembre 2026 : ce qui est démontré, certifié, calculé, négatif,
les erreurs corrigées, et ce qu'il faut pour aller au bout). `NOTE_C3_2026-09-22.md` est une note intermédiaire, remplacée par le rapport.

Ce dossier n'est dans aucun dépôt git (rien n'a été poussé sur GitHub).

## Démarrer
- Vérifications rapides sans solveur : `python check_all.py` (bibliothèque standard), `python audit_verify.py` (networkx).
- Validation des modèles sur des graphes réels : `validate_quotient.py`, `validate_full_model.py`, `validate_builder.py`, `validate_cnf.py`.
- Certification DRAT d'un problème : `python cert_q.py stageQ_runs/<nom>.in.json 0 gen` puis, dans l'image `proofbox`, `sh cert_check.sh <nom> 1800`.
- Commandes complètes et images Docker : annexe « Reproduction » du rapport. Empreintes SHA-256 : `rapport/INVENTAIRE.txt`.

## Contenu
| Fichiers | Rôle |
|---|---|
| `cpsat_aggregate*`, `farkas*`, `check_all.py` | classification des 156 graphes F (26 possibles), certificats de Farkas |
| `level2_phased.py`, `level25.py`, `reduce_classes.py`, `classes_reduced.json` | niveau des phases (318 → 125 → 46 classes) |
| `enum_all.*`, `enum_nofilter.py` | énumération des incidences B (35 classes complètes → 33 problèmes distincts ; 11 classes incomplètes) |
| `quotient_model.py`, `run_one_q.py`, `sweep_q.py`, `stageQ_runs/` | étage quotient (33 problèmes) |
| `cert_q.py`, `cert_check.sh`, `cert_all.sh`, `certs/` | certification DRAT (CaDiCaL 3.0.1 + drat-trim) |
| `full_model.py`, `solve_class.py`, `solve_fixedB.py` | modèle complet au niveau des sommets (validé ; aucun résultat tiré) |
| `spectral_test.py`, `spectral_results.json` | condition spectrale (résultat négatif) |
| `audit_verify.py` | vérificateur indépendant écrit pendant l'audit |
| `rapport/` | rapport LaTeX/PDF, tables générées depuis les résultats, inventaire |

## Ajouts de la nuit du 22 au 23 septembre (détail : rapport/audit_c3.pdf §« Complément de la nuit », journal NUIT_JOURNAL.md)
- `lean_encoding.py` : encodage compact de l'étage Q (totalizers tronqués), validé par `validate_lean.py` ; 20 à 30 fois plus rapide.
- `stageq_sym.py` : cassage de symétrie complet (lex-leader sous Aut(F) et supports), validé par `validate_symlex.py`.
- `enum_supports_phased.py` : multi-ensembles de supports compatibles LQ et réalisables par les phases d'une classe (validé : `validate_enum_phased.py`).
- `make_phased_instances.py` : instances de l'étage Q, une par orbite sous Aut(F).
- Cube-and-conquer : `cube_q_inc.py` (un solveur par instance, cubes sous hypothèses, découpage récursif), `cube_runner_inc.sh`
  (file dynamique `cubes/LIST.txt`, un runner par cœur, environ 300 Mo chacun), validé par `validate_inc.py` et `validate_split.py`.
  Résultats : `cubes/<instance>/results.txt`, `subcubes.txt`. Reprise : relancer les runners ; marqueur `cubes/<instance>/FROM_SPLIT`.
- Certification : `cert_sym.sh` (CNF régénérée + CaDiCaL 3.0.1 natif + preuve DRAT binaire + drat-trim), synthèse `certs/SUMMARY_SYM.txt`.
- Ordre de grandeur du travail restant : plusieurs centaines d'heures-CPU -> machine de calcul (32 Go) ou cluster.

## Ajouts du matin du 23 septembre
- `cert_enum.py` : certifie qu'une énumération de supports est complète (réencodage CNF du modèle avec phases + clauses bloquantes ;
  CaDiCaL + DRAT + drat-trim). Validé dans les deux sens (évaluateur indépendant ; chaque multi-ensemble débloqué redonne SAT).
  Certifiées : classes 0, 4, 15, 25, 30, 32, 42 (`certs/SUMMARY_ENUM.txt`). Les autres : `sh cert_enum_all.sh` dans l'image `c3box`.
- `compare_phased_old.py` : l'ancienne et la nouvelle énumération concordent sur 42 classes (3 écarts, tous expliqués).
- `manifest.py` -> `MANIFEST.txt` : résultats sous forme canonique hachée, pour comparer deux reproductions octet pour octet.
- `docker/` : images exactes exportées (`*.image.tar.gz`, `IMAGES.sha256`, identifiants dans `IMAGES.txt`), recettes figées,
  image unique `c3box` (Python + CaDiCaL natif + drat-trim ; `docker/Dockerfile.c3box`).
- Arrêt sur le portable le 23/09 à 10 h 14 : état et reprise décrits dans `rapport/audit_c3.pdf` (sections « Complément de la nuit » et
  « Plan de calcul et reproduction »).
