# Journal de nuit — recherche C3 autonome (à relire à chaque reprise)

L'utilisateur dort. Consigne : travailler sans s'arrêter, **sans poser de questions**, reprendre automatiquement après la limite d'utilisation.
Priorité : réduire la structure de recherche (maths), puis calculer ; sinon longues sessions de réflexion.

## Règles permanentes
- **Rien sur git / GitHub.** Tout reste dans `Desktop/c3_recherche_annexe/`.
- **PC portable 15 Go** : au plus 2 CaDiCaL (1,3 Go chacun) en parallèle ; tâches CP-SAT légères (~150 Mo) ok. **Avant tout lancement : RAM libre >= 1,5 Go**
  (PowerShell : Get-CimInstance Win32_OperatingSystem | FreePhysicalMemory). A 02h15 la RAM libre est tombée à 0,4 Go avec 3 CaDiCaL -> sqL3 arrêté.
- **Aucun UNSAT n'est retenu** sans : (a) validation du code exact (contrôle planté / graphe réel), (b) de préférence un certificat (Farkas, DRAT via `cert_q.py`+`cert_check.sh` dans l'image `proofbox`, ou recherche exhaustive simple).
- Écrire les `.py/.tex` avec l'outil Write (pas de heredoc Python pour du LaTeX). Découper un script sur `"\nif __name__"`, jamais `'if __name__'`.
- Les processus lancés en arrière-plan peuvent être tués si la mémoire manque : garder chaque tâche ≤ 3 Go.
- Consigner chaque résultat ici (section Résultats) avec date/heure et statut.

## État au 23/09 ~01h
- Rapport d'audit : `rapport/audit_c3.pdf` (à mettre à jour en fin de nuit avec les nouveaux résultats).
- Étage quotient : 33 problèmes (35 classes complètes). 8 UNSAT certifiés DRAT.
- **Nouveau** : relaxation linéaire LQ (`linear_relaxation.py`) : 15/33 infaisables (les 8 + 7 nouveaux : m04776_s0000/s0002/s0003, m04905_s0004/s0005, m05033_s0008, m15426_s0017).
  13 d'entre eux par une seule ligne (`lq_local.py`, recherche exhaustive sans solveur) ; m16927_s0018/s0023 globaux (déjà DRAT).
- Restent ouverts (supports) : m04776_s0001, m04905_s0006, m04907_s0007, m05033_s0012, m06717_s0014, m12295_s0015, m15426_s0016,
  m16927_s0019..s0022, m20723_s0024, m21041_s0025, m21045_s0026, m23221_s0027, m23431_s0028, m26850_s0029, m29481_s0032 (18).
- Négatifs : test par motif F (`motif_v2.py`) ne tue aucun F (21 faisables, 5 indécis) ; test de phases local (`phase_lnc.py`) ne tue rien sur 15 classes.
- Littérature lue : ibenarb (τ≡0 mod 3, lemme B, pas de C4 dans le 2-facteur, 652 Go de preuves pour 1 type), Lundle22 (critère mod π³),
  Thakkar–Severini (rien de neuf pour C3), SMS (pas adapté : multigraphe/partition), cube-and-conquer (gains ×2–3).

## File de tâches (dans l'ordre)
1. Valider `phase_global.py` (contrôle planté `validate_phase_global.py`), puis le lancer sur les classes complètes aux supports ouverts,
   en commençant par celles qui ont peu de B phasés (39,40,41,36,37,38,15,14,33,9,24,8,1,16,21,17,23,28,31,26,34,35,7,10,11,18,19,12,13,20,22,2,3,30,0).
2. Tout nouvel UNSAT → certificat (Farkas/exhaustif/DRAT).
3. Étage quotient long (≥ 1 h) sur les supports encore ouverts, 2 à la fois, avec les contraintes LQ ajoutées en clauses unitaires si utile.
4. Réflexion : classes clairsemées (11 classes incomplètes) — formulation supports+C avec LQ ; exploiter lemme B / 2-facteur ; critère de Lundle22.
5. En fin de nuit : mettre à jour `rapport/audit_c3.tex` (section résultats nouveaux), recompiler (image `texbox`), régénérer tables/inventaire.

## Résultats de la nuit
(à compléter au fil de l'eau)

### 01h — réflexion : contenu linéaire épuisé
- LQ contient tout le linéaire : les sommes de C^2 contre les vecteurs de W = span(B^T, 1) se réduisent à des identités
  (vérifié : somme simple -> 174 = 174 ; somme pondérée par s_Z(j) -> identité via C M = M K). Le reste est quadratique, dans W^perp.
- Dans W^perp (dim 21-22) : C = X_W + 7E - 4P_perp, E projecteur de rang 12 inconnu => rang_F7(C + 4P_perp - X_W) <= 12 (filtre de générateur).
- Mod 2 : doubles disparaissent, C1^2 + C1 = B^T B (mod 2) sur les simples.
- Seule information non linéaire bon marché restante : les PHASES (bloc triangle x indépendant au niveau des sommets) -> phase_global.py.

### ~01h30 — phase_global.py validé
- Contrôle planté (symétrie psi -> -psi) : 8/8 acceptés (densité faible, 120 s), 6/10 + 4 indécis (dense, 90 s), **jamais de faux « infaisable »**.
- Indécis = non tué (conservateur). Lancé sur deux files : A = 39,40,41,36,37,38,15,14,33,9,24,8,1,16,21,17 ; B = 23,28,31,26,34,35,7,10,11,18,19.
  Sorties : phase_global_A.log / phase_global_B.log (+ JSON phase_global_<liste>.json).

### ~01h40 — calculs détachés en cours (docker run -d, survivent aux coupures ; vérifier avec `docker ps`)
- pgA / pgB : phase_global (voir plus haut). Mémoire ~70 Mo chacun.
- sqL1 : étage Q 1 h/problème : m16927_s0019..s0022.  sqL2 : m05033_s0012, m12295_s0015, m04776_s0001, m04905_s0006.
  Sorties : stageQ_long/<nom>.json + stageQ_long/progress.log (script stageq_long.sh ; runner run_one_q_long.py).
- Budget : 4 cœurs, < 4 Go. Ne rien ajouter tant que ces 4 tournent, sauf tâche légère 1 cœur.

### ~01h55
- row_counts.py : 35k à 2M lignes possibles par orbite (étiquetées) -> générateur ligne par ligne naïf pas viable sans élagage quadratique fort.
- phase_global : classes 39, 40 indécises en 60 s (1 B phasé chacune) -> pas de gain rapide sur les classes denses symétriques.
- esA : enum_supports_lq.py (supports passant LQ, par graphe F) sur masques 28 puis 16420 -> enum_supports_lq_<mask>.log/.json.

### ~02h10 — PERCÉE classes clairsemées
- lq_local_crosscheck.py : 891 lignes, 0 désaccord entre DP exhaustive et CP-SAT indépendant -> les 13 tués « locaux » sont solides.
- **enum_supports_lq masque 28 (K1,3, classe 42, incomplète) : COMPLET en 59 s, 1 seul multi-ensemble de supports passant LQ**
  (identique à celui de l'ancienne énumération). -> problème quotient m00028_sL0 lancé (sqL3, 1 h).
- esB : enum_supports_lq sur 8290 9313 13452 29448 30992 26896 16384 16388 0 (enchaînés). esA : 16420 en cours.
- À FAIRE : pour chaque masque complet par esA/esB, créer les problèmes m<mask>_sL<k> et les passer à l'étage Q (+ LQ déjà satisfait).

### ~02h15 — mémoire
- RAM libre 0,4 Go avec 3 CaDiCaL + 4 CP-SAT -> sqL3 (m00028_sL0) arrêté, À RELANCER quand sqL1 ou sqL2 a fini (file : m00028_sL0 puis supports clairsemés).
- 02h20 : pgA/pgB relancés en pgA2/pgB2 à 15 s par B phasé (balayage) ; logs phase_global_A2.log / _B2.log
- 02h25 : masque 16420 (3K2, classe 27) : énumération LQ des supports COMPLÈTE, 4 multisets (cohérent : les 2 autres de l'ancienne liste échouent à LQ).
  Problèmes m16420_sL0..3 créés. **File d'attente étage Q : stageQ_long/QUEUE.txt** (lancer via `sh stageq_long.sh 3600 <noms>` dès qu'un CaDiCaL finit ; max 2).
- 02h35 : lqb.py (LQ + budget B d'ibenarb étendu aux supports) lancé sur tous les problèmes ouverts (conteneur lqb, log lqb.log)
- 02h45 : masque 8290 (classe 25) : LQ supports COMPLET, 2 multisets ; cohérence vérifiée ; m08290_sL0..1 en file
- 03h00 : support_phase_check.py (le multiset de supports est-il réalisé par un B phasé de niveau 2.5 d'une classe du graphe ?) :
  m00028_sL0, m16420_sL0..3, m08290_sL0 réalisables ; **m08290_sL1 MORT** (aucune classe ; CP-SAT, à certifier). Retiré de la file.
  Bilan clairsemées : classe 42 -> 1 problème, classe 27 -> 4, classe 25 -> 1 (listes complètes).
- [00:34] NOTE : les heures notées plus haut (01h..03h) étaient estimées et fausses ; à partir d'ici horodatage = horloge système (date).
- [00:40] masque 9313 (classe 32) : LQ supports COMPLET, 2 multisets ; cohérent ; m09313_sL1 MORT (phases) ; m09313_sL0 en file. Classe 32 -> 1 problème.
- [00:41] **m08290_sL1 et m09313_sL1 : morts CERTIFIÉS** (vecteur de Farkas entier, revérifié en exact ; farkas_phase.py -> farkas_phase_results.json).
- [00:45] masque 13452 (classe 5) : LQ supports COMPLET, 1 multiset (les 6 autres de l'ancienne liste échouent à LQ) ; m13452_sL0 RÉALISABLE (phases) -> en file.
- [00:50] masque 29448 (classe 6) : LQ supports COMPLET, 1 multiset (9 autres échouent à LQ) ; m29448_sL0 RÉALISABLE -> en file.
- [00:50] **NOUVEL OUTIL stageq_sym.py : cassage de symétrie COMPLET de l'étage Q.**
  Symétries d'un problème (F, multiset de supports) : permutations pi des 6 triangles avec pi(F)=F et pi(multiset)=multiset, prolongées aux 27 orbites
  indépendantes (appariement ordonné des supports égaux). Comptes : m23221_s0027 71 (groupe d'ordre 72), m16420_sL* 23, m21041/m23431/m00028_sL0 11,
  m12295 7, m16927_*, m15426, m21045, m26850 3, les autres 0-1. Auparavant seules les jumelles (supports identiques) étaient cassées.
  Contrainte ajoutée : chaîne(Q) <=lex chaîne(Q^sigma) pour chaque sigma (chaîne = Q 33x33 complète lue ligne par ligne, 0<1<2).
  VALIDITÉ (preuve) : soit Q0 le minimum lex de l'orbite d'une solution sous le groupe engendré par les sigma ET les transpositions de jumelles.
  (a) Q0 <= Q0^sigma pour tout sigma : minimalité. (b) les contraintes jumelles (ligne_i <=lex ligne_j hors colonnes i,j, i<j jumelles) : sinon soit c la
  1re colonne où elles diffèrent ; si c<i, la ligne c de Q0^(ij) est plus petite en colonne i (lignes <c inchangées car Q0[k][i]=Q0[k][j] pour k<c) ;
  si c>i, les lignes <i sont inchangées et la ligne i diffère d'abord en c, plus petite. Contradiction dans les deux cas. Donc les deux familles
  sont compatibles.  Témoin : version relâchée (équations Gram indép x indép retirées) de m23221_s0027 avec les 71 contraintes -> SAT (pas de mort parasite).
- [00:50] **Mémoire : solve_stream.py** (clauses lues du disque une par une, pas de liste Python) : pic 234 Mo au lieu d'environ 1,4 Go.
  Décodage vérifié sur le témoin relâché : sommes de lignes 14, symétrie, Gram diagonal et lignes triangles exacts, 2 doubles par ligne ; seules les
  équations retirées sont violées (attendu). (cadical natif de proofbox inutilisable dans c99audit : glibc 2.38 requise.)
- [00:52] sqL2 ARRÊTÉ (m05033_s0012 à ~27 min, 0 symétrie ; refait dans la nouvelle file). Mémoire VM Docker : 7,8 Go au total, 4,75 dispo.
  Lancés : symgen (stageq_sym_gen.sh : génère les CNF une par une, dans l'ordre de priorité) + symS1, symS2 (stageq_sym.sh 3600 : réclament les
  instances par mkdir atomique). Liste = stageQ_sym/LIST.txt (27 instances, les plus symétriques d'abord). Résultats : stageQ_sym/progress.log.
  La file stageQ_long/QUEUE.txt est REMPLACÉE par cette liste. Quand sqL1 finit m16927_s0019 : l'arrêter et ajouter symS3, symS4.
- [00:54] RAM Windows libre 0,7 Go (2 solveurs sym ~0,8 Go chacun + sqL1 1,4 Go) -> sqL1 ARRÊTÉ (m16927_s0019 à 29 min ; refait dans la file sym). Solveur sym réel : ~0,8 Go (5 M clauses), pas 0,25 Go.
- [00:59] esB : masques 30992 (classe 4) et 26896 (classe 29) UNKNOWN à 300 s, 1 worker, 0 support trouvé. -> esC : relance 6 workers, 1800 s/résolution (enum_supports_lq_<m>_w6.log). esB continue sur 16384 16388 0.
- [00:59] lean_encoding.py : totalizer bidirectionnel tronqué à r+1 (au lieu de CardEnc.equals, quasi O(n^2) pour la moitié >= r). Validation validate_lean.py en cours (exhaustif petits n, BvLS, tour 3x3, 2 UNSAT certifiés, témoin SAT).
- [01:02] **validate_lean.py : PASS** (5116 cas exhaustifs de tot_equals ; BvLS 81T/81I planté SAT + évalué, corrompu UNSAT, ancien et nouveau encodage ;
  tour 3x3 k=4 SAT vérifié, k=5 UNSAT ; m05033_s0009 UNSAT en 2,8 s (ancien : 60 s natif) et m29481_s0030 UNSAT en 8,0 s (ancien : 260 s natif),
  clauses 4,7 M -> 1,1 M ; témoin relâché SAT + évalué). **Accélération x20-x30 sur les UNSAT certifiés.**
- [01:02] Pipeline sym basculé sur l'encodage compact (stageq_sym.py LEAN=True). symS1/S2 (ancien encodage, 15 min) et lqb (tout UNKNOWN) arrêtés.
  CNF sym+lean : 1,18-1,41 M clauses ; solveur 200-350 Mo. Relancé : symgen + symS1..symS6 (3600 s/instance, 27 instances, LIST.txt).
- [01:06] **validate_symlex.py : PASS** (fonctions de production stageq_sym.symmetries/add_perm_lex + add_lex_twins + lean ; 60 petits modèles
  énumérés exhaustivement, groupe complet des données fixées par force brute) : 4044 orbites de solutions, 0 orbite perdue, le min lex de chaque orbite
  toujours conservé ; 36 modèles avec symétries sigma actives et solutions (jusqu'à 13950 solutions / 3558 orbites). -> le cassage complet est sûr.
- [01:06] masque 16384 (classe 44) : UNKNOWN à 300 s, 0 support. Aut(F) des masques restants : 30992 -> 12, 26896 -> 120, 16384 -> 48,
  16388 -> 16, 0 -> 720. **enum_supports_sym.py** : lex-leader sous Aut(F) sur le vecteur des multiplicités de supports (sûr : le lex-max de chaque
  orbite le satisfait) -> un représentant par orbite. Conséquence : le test de phases doit essayer toutes les images pi(mu) avant de déclarer MORT.
  Validation en cours (vES) : comparaison avec les listes complètes des masques 28 16420 8290 9313 13452 29448.
- [01:07] pgA2/pgB2 ARRÊTÉS : 145 B phasés balayés à 15 s, 0 faisable, 0 tué, tout indécis (piste sans effet). esD : enum_supports_sym 26896 (Aut 120), 2 workers, 1800 s.
- [01:09] masque 16388 (classe 43) UNKNOWN à 300 s (1 worker). esC masque 30992 (6 workers) : 39 multisets trouvés en 527 s (1 worker : 0 en 300 s) -> classe 4 vivante au niveau LQ, liste longue attendue. enum_supports_sym masque 28 : 1 canonique, complet (135 s).
- [01:10] Vérifié : « pas de C4 dans L » et « lemme B » sont IMPLIQUÉS par l'étage Q (Gram U1U3 >= 8 > 6 ; Gram(a,b) saturé par 2+4 puis sommes de lignes). Rien à ajouter au modèle.
- [01:11] ansatz_q.py : recherche de solutions invariantes sous une symétrie sigma (SAT => étage Q SAT) sur m23221_s0027 (F = K3,3, supports = paires : 18 même côté (x3), 9 croisées), m16420_sL0, m23431_s0028 ; conteneur ansz, log ansatz.log.
- [01:22] esB fini : masque 0 (F vide, classe 45) UNKNOWN à 300 s. esE : enum_supports_sym sur 0 (Aut 720), 16384 (48), 16388 (16), 1 worker, 1800 s. ansatz m23221_s0027 : pas de solution invariante sous 2 sigma d'ordre 6 (UNSAT 10 s, 4 s).
- [01:23] ansatz m23221_s0027 : 5 sigma d'ordre 6 testés, tous UNSAT (4-216 s) -> relancé avec 1 représentant par type de cycle, ordres 3 puis 2 d'abord (ansatz.log ; ancien : ansatz_order6.log).
- [01:24] stage_p.py prêt (si un étage Q sort SAT : cherche les phases pour ce Q ; modèle sommet validé full_model + sum_psi z = Q_UV + jauge sur arbre couvrant ; relevé 99x99 vérifié exactement). Auto-test : tour 3x3 T et I SAT + relevé ok, Q corrompu UNSAT.
- [01:25] RAM Windows 0,82 Go : ansz (pysat + liste Python + copie multiprocessing) à 957 Mo -> arrêté, ansatz_q.py passé en CNF disque + solve_stream (comme les solveurs sym), relancé (-m 900m).
- [01:38] **validate_enum_sym.py : PASS** (6 masques : orbites des anciennes listes complètes = représentants canoniques, un par orbite). Découverte : m16420_sL3 ~ sL0 et sL2 ~ sL1 (isomorphes sous Aut F) -> runs sL2, sL3 arrêtés (doublons), 2 solveurs libérés pour la suite de la file.
- [01:38] **Doublons par isomorphisme (Aut F)** sur les 44 fichiers d'instances : m04776_s0000~s0002, m04905_s0004~s0005, m16927_s0018~s0023,
  m29481_s0030~s0031 (morts des deux côtés, cohérent), m16927_s0019~s0022, m16927_s0020~s0021 (ouverts), m16420_sL0~sL3, sL1~sL2.
  => les 33 instances d'origine = 27 distinctes ; ouvertes d'origine : 18 -> **16 distinctes**. m16927_s0021, s0022 retirés de la file sym.
  Contrôle de cohérence : chaque paire isomorphe a le même statut LQ / étage Q.
  Ouverts distincts actuels : 16 d'origine + 7 clairsemés (m00028_sL0, m16420_sL0, sL1, m08290_sL0, m09313_sL0, m13452_sL0, m29448_sL0) = 23,
  + classes incomplètes : 4 (30992, énumération en cours, >= 91 multisets), 29 (26896), 43 (16388), 44 (16384), 45 (0).
- [01:40] **m16420_sL0 : UNSAT** (étage Q, encodage compact + symétrie complète, 2273 s, pysat CaDiCaL 1.9.5, worker symS2). m16420_sL3 isomorphe -> même verdict. Certification DRAT lancée (cert_sym.sh -> CaDiCaL 3.0.1 natif, preuve binaire, drat-trim ; certs/SUMMARY_SYM.txt).
- [01:41] esD : masque 26896 (K1,5) sym UNKNOWN à 1800 s, 0 multiset. Ajout add_twin_lex (lex des lignes de C pour supports égaux, conditionnel) dans enum_supports_sym.py (--twins) ; validation vES2 sur les 6 masques complets. ansatz m23221_s0027 : ordre 3 (2e type) UNKNOWN 900 s.
- [01:52] Piste NÉGATIVE : --twins (lex conditionnel des lignes de C) rend CP-SAT beaucoup plus lent (masque 28 : UNKNOWN à 600 s, 0 trouvé ; sans : complet en 135 s). vES2 arrêté ; option laissée dans le code, non utilisée.
- [01:52] symS7 ajouté (7 solveurs étage Q).
- [01:53] masque 0 (F vide) sym UNKNOWN à 1800 s, 0 trouvé (esE passe à 16384). Constat : le lex-leader rend les solutions rares -> dur à TROUVER pour CP-SAT ; 30992 débloqué par la version non réduite à 6 workers (183 multisets). esF : 26896 non réduit, 2 workers, 1800 s. Preuve DRAT m16420_sL0 : 42 Mo à 12 min.
- [02:00] ansatz m23221_s0027 terminé (8 types de sigma) : 6 UNSAT (ordres 2,3,4,6 ; 8-216 s), 2 UNKNOWN à 900 s (un ordre 3, un ordre 2). Aucune solution invariante trouvée -> pas d'indice que l'étage Q soit SAT. Passe à m16420_sL0 (déjà UNSAT, rapide) puis m23431_s0028.
- [02:02] m23221_s0027 : UNKNOWN à 3600 s (sym complète + compact). -> stageQ_sym/HARD.txt (file des dures : passe longue CaDiCaL 3.0.1 natif + preuve DRAT, ou découpage en cubes sur les 2 doubles d'une ligne, quand du CPU se libère).
- [02:02] m16420_sL1 UNKNOWN à 3600 s (sL0 : UNSAT à 2273 s) -> HARD. ansz arrêté (ansatz m16420_sL0 inutile, déjà UNSAT). Passe longue m16420_sL1 : cert_sym.sh 14400 (CaDiCaL 3.0.1 natif, preuve DRAT binaire, drat-trim si UNSAT) ; log cert_sym_hard.log.
- [02:03] m21041_s0025 UNKNOWN à 3600 s -> HARD.
- [02:06] esE arrêté (16384 sym : sans espoir à 1 worker). NOUVEL OUTIL enum_supports_phased.py : par classe, multisets de supports LQ-compatibles ET réalisés par un B phasé de niveau 2.5 de la classe (un seul CP-SAT ; remplace enum_supports_lq + support_phase_check). Validation vEP sur les classes 42 25 32 30 15 0 (réponses connues par l'ancien pipeline). cube_q.py écrit (cubes {w_ZA = w_ZB = 1}, 325 par instance, reprise possible) pour les dures.
- [02:21] **validate_enum_phased.py : PASS** (classes 42 25 32 30 15 0 : ensembles identiques aux réponses de l'ancien pipeline, complets, 17-296 s). esF arrêté ; lancés ep29 (classe 29 / masque 26896, 2 workers) et ep4 (classe 4 / masque 30992, 1 worker).
- [02:23] esC ARRÊTÉ (30992 sans phases : 276 multisets LQ trouvés en 83 min, plafond 500 : liste jamais complète ; remplacé par l'énumération avec phases de la classe 4). ep4 relancé avec 6 workers (1800 s/résolution, plafond 1000).
- [02:38] m00028_sL0 et m23431_s0028 UNKNOWN à 3600 s -> HARD (5 dures : m23221_s0027, m16420_sL1, m21041_s0025, m00028_sL0, m23431_s0028). ep4 (classe 4 avec phases) : 51 multisets en 763 s. Test de coût des cubes : cube_q.py m23221_s0027 (1 cœur, 600 s/cube).
- [02:40] m12295_s0015 UNKNOWN à 3600 s -> HARD (6).
- [02:41] **CUBES EFFICACES** : m23221_s0027, Z=6, cubes {w_6A = w_6B = 1} : les 4 premiers UNSAT en 14-19 s (chargement compris) ; 325 cubes
  ~ 1,5 h CPU au total au lieu d'un run monolithique qui n'aboutit pas en 1 h. 6 dures / 9 traitées en monolithique -> CHANGEMENT DE STRATÉGIE :
  tout en cubes. File monolithique fermée (plus aucune nouvelle réservation ; les 7 en cours finissent), symgen arrêté.
  cube_runner.sh (réservation atomique par instance, cube_q.py K=1, 1800 s/cube) ; file cubes/LIST.txt = 5 dures (hors m23221 déjà en cubeT)
  + 9 jamais lancées ; lancés cubeR1, cubeR2. Résultats : cubes/<nom>/results.txt, synthèse cubes/PROGRESS.txt.
  Validité : les cubes couvrent tout (chaque orbite indépendante a exactement deux doubles, lemme entries (c)) ; base CNF identique à la file sym.
- [02:52] **Classe 4 (masque 30992) COMPLÈTE avec phases : 96 multisets** (LQ seul : > 276 sans fin) en 1556 s (6 workers)
  -> 18 orbites sous Aut(F) (|Aut| = 12) -> instances m30992_sP0..sP17 (make_phased_instances.py), ajoutées à la file cubes. cubeR3..R6 lancés.
- [02:52] classe 29 (26896, K1,5) avec phases : UNKNOWN à 1800 s, 0 trouvé (2 workers) -> relancé 4 workers, 3600 s/résolution.
- [02:53] m16420_sL0 : CaDiCaL 3.0.1 NATIF sur la CNF régénérée -> UNSAT aussi (58 min) = confirmation indépendante (autre version) ; drat-trim en cours sur la preuve binaire de 134 Mo.
- [02:53] m15426_s0016 UNKNOWN à 3600 s -> file cubes. Cubes : tous UNSAT jusqu'ici (max 23 s) ; ~50/325 pour m16420_sL1, m21041_s0025, m23221_s0027.
  cube_runner2.sh (file dynamique relue après chaque instance) ; cubeR7 lancé. À chaque sortie d'un symS : ajouter l'instance si UNKNOWN + lancer un runner2.
- [02:54] **ALERTE MÉMOIRE** : Claude Code a arrêté 2 shells de fond côté hôte (boucle de relais symS -> cubes, et shell de la passe longue m16420_sL1)
  pour mémoire critique. Cause probable : 7 runners de cubes démarrés presque ensemble, chacun générant sa CNF de base en Python (pic de plusieurs centaines
  de Mo chacun). Les CONTENEURS continuent (passe longue sL1 + drat-trim sL0 dans leurs conteneurs, résultats dans certs/*.log). NE PAS relancer ces
  shells. Désormais : pas de nouveau runner ; quand un symS sort, ajouter à la main son instance UNKNOWN à cubes/LIST.txt (les runners dynamiques la prendront).
  RAM après pic : 1,07 Go Windows, 3,1 Go dispo dans la VM ; 9 processus cubes + 6 symS + ep29 + 2 certifs.
- [02:55] cubeR7, cubeR8 arrêtés (marge mémoire, CPU sursouscrit) ; leurs réservations libérées (reprise automatique via results.txt par un autre runner).
- [03:02] m16927_s0019, m16927_s0020 UNKNOWN à 3600 s -> file cubes ; symS1/S3 remplacés par cubeR7 (runner2), cubeR8 dans 90 s.
- [03:04] m21045_s0026 UNKNOWN à 3600 s -> file cubes (pas de nouveau runner : marge mémoire ; les runners dynamiques R7/R8 le prendront).
- [03:28] **m16420_sL0 : UNSAT CERTIFIÉ** (CNF compacte + symétrie complète, sha256 a706468daf92ee33 ; CaDiCaL 3.0.1 natif UNSAT en 3515 s ;
  preuve DRAT binaire 129 Mo ; drat-trim : s VERIFIED en 2852 s, 587320/3677106 lemmes dans le noyau, 0 RAT). m16420_sL3 isomorphe : même verdict.
  => classe 27 (masque 16420, 3K2) : il ne reste que m16420_sL1 (cubes en cours + passe longue native).
- [03:39] m04776_s0001, m26850_s0029 UNKNOWN à 3600 s -> file cubes (symS4/S5 non remplacés : RAM 0,9 Go).
- [03:40] m04905_s0006 UNKNOWN à 3600 s -> file cubes. File monolithique TERMINÉE : 1 UNSAT (m16420_sL0), 2 doublons arrêtés, tout le reste UNKNOWN à 1 h -> cubes.
- [03:47] Cube récalcitrant : m21041_s0025 (Z=6 ; A=13, B=17) UNKNOWN à 1800 s -> cubes/HARD_CUBES.txt (sous-cubes plus tard).
- [03:48] Cube récalcitrant : m23221_s0027 (Z=6 ; 15, 22) UNKNOWN à 600 s (limite de cubeT) -> HARD_CUBES.
- [03:58] **validate_inc.py : PASS** : témoin relâché, 325 cubes, verdicts identiques incrémental (hypothèses + budget) vs solveur neuf + clauses
  unitaires (29 SAT, 296 UNSAT, 0 désaccord ; chaque modèle SAT revérifié clause par clause) ; 4 vrais cubes m16420_sL1 identiques.
  Explication de la vitesse : les cubes faciles se résolvent en ~0 s ; les 15-20 s/cube de cube_q.py étaient le RECHARGEMENT de 1,4 M clauses.
  -> BASCULE : runners cube_q.py arrêtés (cubeR1-8, cubeT) ; cube_runner_inc.sh (1 solveur par instance, budgets 5k/50k/500k conflits,
  reprise depuis results.txt, cubes UNKNOWN retentés). Bilan cubes non incrémentaux : ~1300 cubes, tous UNSAT sauf 2 UNKNOWN (HARD_CUBES).
- [04:08] 8 runners incrémentaux cubeI1-8 lancés (budget 5000). Passe 1 : m16420_sL1 -> 17 cubes indécis, m21041_s0025 -> 12 (puis budgets 50k, 500k). RAM Windows 1,25 Go.
- [04:25] cubeI9, cubeI10 ajoutés ; ep43 lancé (classe 43 / masque 16388, avec phases, 2 workers, 3600 s). Classe 29 : 8 multisets trouvés (énumération en cours).
- [04:39] m21041_s0025 : passe 50k -> 12 cubes toujours indécis. cube_q_inc.py étendu : 3e passe = DÉCOUPAGE récursif (orbite V avec un seul double supposé -> son 2e double W parcourt les 25 autres : recouvrement complet ; profondeur 2, budgets 10B puis 30B aux feuilles). Validation validate_split.py sur le témoin relâché (budget 3 pour forcer le découpage). Les runners en cours utilisent encore l'ancienne 3e passe (100B) ; ils prendront le nouveau code à l'instance suivante.
- [04:40] **2e ALERTE MÉMOIRE** : shell hôte de validate_split arrêté par Claude Code (Windows : 0,89 Go libres, vmmemWSL = 5 Go). Pas de relance du shell.
  cubeI9, cubeI10 arrêtés, réservations libérées. PLAFOND désormais : 8 runners de cubes + ep29 + ep43 + passe longue sL1, rien de plus.
  Le conteneur vsplit continue (il écrit cubes/m23221_s0027_relaxed/results_incval.txt) : refaire la comparaison ensuite.
- [04:48] **validate_split.py : PASS** (2e essai, 60 DERNIERS cubes du témoin relâché, budget 1 conflit) : 11 cubes tranchés par le découpage
  récursif (7 SAT trouvés au fond de l'arbre, 1 UNSAT), 49 en passe 1, 3 UNKNOWN (budget), 0 désaccord avec les solveurs neufs, 2819 nœuds de sous-cubes.
  (1er essai sur les 60 premiers cubes : 60/60 d'accord mais aucun découpage exercé -> test refait.) RAM Windows 0,5-0,9 Go, VM stable (3,5 Go dispo dedans).
- [04:53] Les runners lancés avant l'extension utilisent l'ANCIENNE 3e passe (500k conflits/cube : des heures). Ajout de --from-split + relay_split.sh ; cubeI2 (m21041_s0025, en ancienne passe 3, 12 cubes) remplacé par cubeS2 (découpage direct, puis runner normal). Les autres seront relayés à la fin de leur passe 50k.
- [05:04] m16420_sL1 : passe 50k -> 16 indécis ; cubeI1 relayé par cubeS1 (découpage direct).
- [05:23] m21041_s0025 : une feuille de profondeur 2 UNKNOWN (budget x3) ; m16420_sL1 : 48 sous-cubes UNSAT, 0 inconnu. Profondeur de découpage portée à 4 pour les prochaines exécutions (plus efficace que l'augmentation de budget sur le témoin). Classe 29 : 10 multisets ; classe 43 : 2.
- [05:30] m23431_s0028 : passe 50k -> 17 indécis ; cubeI4 relayé par cubeS4 (découpage direct, profondeur 4).
- [05:42] m06717_s0014 : passe 50k -> 19 indécis ; cubeI8 relayé par cubeS8 (découpage direct).
- [05:43] RAM Windows 0,3-0,4 Go : vmmemWSL a grossi à 5,4 Go (relais = nouveaux conteneurs ; WSL ne rend pas la mémoire). RÈGLE : plus AUCUN nouveau conteneur cette nuit ; cache de pages VM vidé ; les runners à ancien code (I3, I5, I6, I7) resteront tels quels (ancienne passe 3 à 500k) plutôt que d'être relayés.
  (relay_inplace.sh écrit puis supprimé : la boucle du runner est le PID 1 du conteneur, la tuer arrête le conteneur.)
- [05:52] BILAN CUBES (UNSAT distincts / 325) : m21041_s0025 313, m16420_sL1 311, m06717_s0014 306, m20723_s0024 306 (en attente),
  m04907_s0007 301, m12295_s0015 294, m05033_s0012 291, m00028_sL0 290, m23221_s0027 178 (en attente). Aucun cube SAT.
  Système lent (pagination : Windows 0,6 Go libres, vmmemWSL 5,4 Go) ; commandes courtes seulement.
- [05:57] 3e alerte mémoire (commande d'état arrêtée par Claude Code). Passe longue native m16420_sL1 ARRÊTÉE (doublon des cubes : 311/325 déjà UNSAT), preuve partielle supprimée. WSL ne rend PAS la mémoire (vmmemWSL 5,38 Go stable après arrêt + drop_caches) ; redémarrer WSL tuerait tout -> non. État figé, commandes légères seulement.
- [06:05] m12295_s0015 (29 indécis) et m04907_s0007 (24) : passe 50k finie -> relais SANS nouveau conteneur (relay_marker.sh : marqueur FROM_SPLIT, seul le python du runner est tué, réservation libérée, instance en tête de file ; la boucle du même conteneur la reprend avec le code actuel).
- [06:15] Classe 43 (masque 16388) avec phases : 2 multisets trouvés puis UNKNOWN (3600 s sans 3e) -> liste INCOMPLÈTE (partielle dans enum_supports_phased_c43.json). Non relancée (règle : pas de nouveau conteneur).
- [06:27] m05033_s0012 : passe 50k -> 34 indécis ; relais sur place (cubeI7, marqueur FROM_SPLIT).
- [06:40] DÉCOUPAGE : 6 cubes durs traités -> 5 UNSAT (195-2725 s chacun), 1 UNKNOWN (m16420_sL1 cube (11,32), fait en profondeur 2 avant le passage à 4 : à reprendre).
  ESTIMATION : ~380 cubes durs restants (m23221 ~147, m29481 38, m00028 ~35, m05033 34, m12295 29, m04907 24, m20723 21, m06717 18, m23431 16,
  m21041 12, m16420_sL1 11) x ~30-45 min = ~200 heures-CPU au rythme actuel -> machine de calcul du projet (7800X3D, 32 Go) sur plusieurs jours, ou cluster.
- [06:42] m00028_sL0 : passe 50k -> 27 indécis ; relais sur place (cubeI3). Tous les runners sont désormais en mode découpage (profondeur 4 pour les relais récents).
- [07:03] **m00028_sL0 : UNSAT par cube-and-conquer** (Z=21 ; 325/325 cubes UNSAT, recompte indépendant : 0 manquant ; 298 en passes 1-2,
  27 cubes durs fermés par découpage, 675 sous-cubes). C'était l'UNIQUE instance de la classe 42 (masque 28, F = K1,3)
  => **classe 42 exclue à l'étage quotient** (statut S : solveur ; certification DRAT par cube/sous-cube à faire sur la machine de calcul).
- [07:13] Rapport : rapport/nuit.tex inclus dans audit_c3.tex (avant l'annexe), bilan du matin ajouté ; compilé (texbox, 3 passes) : audit_c3.pdf, 15 pages, 0 erreur, 0 référence indéfinie, 3 petits débordements.
- [07:23] Découpage : 41 cubes durs fermés UNSAT (18 à 06:52), 1 UNKNOWN, 0 SAT ; accélération (clauses apprises réutilisées). Classe 29 : 18 multisets.
- [07:53] Découpage : 44 cubes durs UNSAT, 1 UNKNOWN, 0 SAT. m23221_s0027 : passe 50k -> 10 indécis, en découpage. Classe 29 : 20 multisets.
- [08:23] Découpage : 45 cubes durs UNSAT, 1 UNKNOWN, 0 SAT. Classe 29 : 23 multisets. RAM Windows 0,87 Go, 9 conteneurs stables.
- [08:51] Réponse à l'utilisateur (confiance, calcul, reproduction). Ajouts : docker/ (Dockerfiles figés, proofbox portable testé, images exactes exportées + SHA-256 + IDs), manifest.py -> MANIFEST.txt (résultats canoniques hachés ; SHA identiques entre méthodes indépendantes sur 5 masques), CNF identique à l'octet sur 2 graines de hachage, section rapport/plan_calcul.tex (18 p.). Correction : 3377 cubes UNSAT (et non ~3700).
- [08:53] m16420_sL1 : 324/325 cubes UNSAT, 1 OPEN (cube (11,32), fait en profondeur 2) -> remis en tête de file avec FROM_SPLIT (profondeur 4). CP-SAT 9.15 expose output_lrat_proof / check_lrat_proof / output_drat_proof : test en cours pour certifier les énumérations.
- [09:00] **Certification des énumérations** : CP-SAT ne fournit pas de preuve exploitable (test : infaisabilité prouvée en présolve par symétries et
  réductions duales, aucune preuve émise). NOUVEL OUTIL cert_enum.py : réencodage CNF complet du modèle d'énumération avec phases
  (supports triés, G0, TY, lignes, doubles, L1, C3, colonnes phasées one-hot, égalités résiduelles, triplets, tri des colonnes des orbites de même support),
  multisets trouvés bloqués. VALIDATION dans les deux sens : classe 15 (4,6 M clauses) : débloquée SAT (évaluateur indépendant 0 violation, multiset = #0),
  bloquée UNSAT ; classe 0 : chacun des 4 débloqué seul -> SAT avec exactement ce multiset (0 violation), les 4 bloqués -> UNSAT. DRAT en cours (15 puis 0).
- [09:10] **ÉNUMÉRATION CERTIFIÉE : classe 15** complète (1 multiset) : CNF sha256 6e4274b135ed5b96, CaDiCaL 3.0.1 UNSAT 272 s, preuve DRAT 30 Mo, drat-trim VERIFIED 224 s. Premier maillon « complétude d'énumération » certifié ; classe 0 en cours.
- [09:16] **ÉNUMÉRATION CERTIFIÉE : classe 0** complète (4 multisets) : CNF sha256 f791a54edc40d441, UNSAT 202 s, preuve 27 Mo, drat-trim VERIFIED 174 s. Suite : génération des CNF des classes 42 25 32 30 4 (conteneur genE), puis DRAT.
- [09:27] CNF d'énumération générées (genE) ; certE lancé : DRAT des classes 42 25 32 30 4.
- [09:28] epAll : réénumération avec phases (1 worker, 1800 s/résolution) des classes : 1 2 3 5 6 7 8 9 10 11 12 13 14 16 17 18 19 20 21 22 23 24 26 27 28 31 33 34 35 36 37 38 39 40 41 43 44 45 (préalable à leur certification).
- [09:54] **ÉNUMÉRATION CERTIFIÉE : classe 42** (1 multiset ; CNF b096ddbee272e204, UNSAT 863 s, preuve 76 Mo, VERIFIED 611 s). Réénumération : classes 1-3, 5-11 complètes (1 multiset chacune). Construction de l'image unique c3box (python + CaDiCaL natif + drat-trim).
- [10:08] Image c3box construite (python + CaDiCaL 3.0.1 + drat-trim), CNF identique à l'octet (a706468daf92ee33). cert_enum_all.sh : certification en chaîne de toutes les énumérations complètes (à lancer quand certE aura fini).
- [10:16] **OPTION A (choix de l'utilisateur, qui reprend son PC)** : 8 runners de cubes et ep29 (classe 29, 31 multisets déjà enregistrés) ARRÊTÉS ;
  instances en cours au moment de l'arrêt : cubes/STOPPED_*.txt ; toutes les réservations libérées (reprise via results.txt + marqueurs FROM_SPLIT).
  Restent : certE (preuves des énumérations 25, 32, 30, 4) et epAll (réénumération, 1 cœur). Mesures : CPU 11-30 %, RAM libre 1,5 Go / 15,4
  (VM Docker 4,5 Go, se vide lentement). cert_enum_all.sh NON lancé (laissé pour le PC de calcul).
- [10:18] **ÉNUMÉRATION CERTIFIÉE : classe 25** (1 multiset ; CNF 4a955e8e9e58b6b9, UNSAT 1179 s, preuve 84 Mo, VERIFIED 330 s). Certifiées : 0, 15, 25, 42.
- [10:19] Tâche planifiée de nuit (cron a7e8b3b5) SUPPRIMÉE (l'utilisateur est réveillé). Chiffres à l'arrêt : 3381 cubes UNSAT, 0 SAT.
  compare_phased_old.py : 30 classes comparées entre l'ancienne chaîne (B phasé + LQ) et enum_supports_phased : 27 identiques, 3 écarts attendus
  (classe 4 : 18 représentants par symétrie des 96 ; classes 25 et 32 : m08290_sL1 et m09313_sL1 exclus par les phases, Farkas). Toutes les classes
  réénumérées ont 1 multiset, sauf 0 (4) et 4 (96).
- [10:22] **ÉNUMÉRATION CERTIFIÉE : classe 32** (CNF 4cfb3bd63aa6c23d, UNSAT 180 s, preuve 61 Mo, VERIFIED 79 s). Certifiées : 0, 15, 25, 32, 42.
- [10:25] **ÉNUMÉRATION CERTIFIÉE : classe 30** (CNF c2e9662631bbf6cc, UNSAT 140 s, preuve 45 Mo, VERIFIED 67 s). Certifiées : 0, 15, 25, 30, 32, 42. Reste la classe 4 (96 multisets).
- [10:28] **ÉNUMÉRATION CERTIFIÉE : classe 4** (96 multisets, liste complète ; CNF 32d5e21000cfa5d5, UNSAT 120 s, preuve 23 Mo, VERIFIED 38 s).
  Énumérations certifiées DRAT : classes 0, 4, 15, 25, 30, 32, 42 (7 sur 46).
- [10:28] epAll arrêté au début de la classe 43 (43, 44, 45 : pour le PC de calcul). Réénumération avec phases : 42 classes sur 46 COMPLÈTES
  (1 multiset chacune sauf 0 et 27 : 4, et 4 : 96) ; incomplètes : 29 (31 trouvés), 43 (2), 44, 45. compare_phased_old.py sur les 42 :
  39 identiques + 3 écarts expliqués (classe 4 : représentants ; 25 et 32 : exclusions par phases certifiées Farkas).
- [10:32] CLÔTURE sur le portable : rapport recompilé (18 p., 0 erreur), MANIFEST.txt régénéré, LISEZMOI complété, surveillance arrêtée,
  conteneurs de la recherche supprimés (testhunch-postgres-1, autre projet, laissé). Arrêt de Docker/WSL pour libérer la mémoire (demandé par l'utilisateur).
- [10:33] Docker Desktop arrêté (docker desktop stop), puis wsl --shutdown (seule distribution : docker-desktop). VM WSL disparue, RAM libre 6,6 Go / 15,4 (0,8-1,5 Go avant), CPU 17-21 % (Windows seul). Plus aucun calcul, aucune surveillance, aucune tâche planifiée.
- [11:05] Publication (demande de l'utilisateur) : dépôt PRIVÉ github.com/amazing-source/conway99-c3 (commits sous 206353265+amazing-source@users.noreply.github.com), release v2026-09-23 avec les images Docker exactes (tailles identiques à l'octet). README : avertissement explicite, les sessions de conway99-involution ne doivent pas consulter ce dépôt.
