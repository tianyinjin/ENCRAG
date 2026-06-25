# PixelRAG direct retrieval vs query_candidates

- PixelRAG file: `E:\CodexWorkspace\RAG_reading\pixelrag_visual_experiment\runs\pixelrag.json`
- Candidate file: `E:\CodexWorkspace\RAG_reading\pixelrag_visual_experiment\query_candidates.json`
- Compared questions: **30**
- Target page found in top-5: **22/30 (73.3%)**
- MRR@5: **0.589**
- Rank distribution: rank 1: 15, rank 2: 3, rank 3: 2, rank 4: 2, rank 5: 0

## By category
- text: 16/21 (76.2%)
- scanned: 5/8 (62.5%)
- table: 1/1 (100.0%)

## Per-question result
| # | candidate | run | result | target page | top PixelRAG hit |
|---:|---|---|---|---|---|
| 1 | VIS-001 | Q001 | FOUND @ 2 | fiche technique a400m.pdf p.12 | Fiche technique Reaper.pdf p.5 (0.563) |
| 2 | VIS-002 | Q002 | FOUND @ 1 | chiffres clés données 2022_tdm_v0_260224.pdf p.10 | Chiffres clés données 2022_TDM_v0_260224.pdf p.10 (0.447) |
| 3 | VIS-003 | Q003 | FOUND @ 1 | colsbleus_3126_pdfweb_page.pdf p.46 | COLSbleus_3126_PDFweb_PAGE.pdf p.46 (0.569) |
| 4 | VIS-004 | Q004 | MISS | 20190909_np_emat-np_le508717-synthese-annuelle-du-retex-cycle-2018-2019-2.pdf p.2 | 20160426_np_cicde_084_lettre_synthese_croisee_gb-fr_operations_face_epid.pdf p.2 (0.610) |
| 5 | VIS-005 | Q005 | MISS | caia-125-bd-ok.pdf p.103 | CDSE_VIGINUM_Guide_sensibilisation_entreprises_FR_12-25.pdf p.11 (0.444) |
| 6 | VIS-006 | Q006 | FOUND @ 1 | 20181019_np_dpid_note-278-vidéoprotection-sur-la-voie-publique.pdf p.2 | 20181019_NP_DPID_Note-278-vidéoprotection-sur-la-voie-publique.pdf p.2 (0.535) |
| 7 | VIS-007 | Q007 | FOUND @ 1 | fiche technique reaper.pdf p.9 | Fiche technique Reaper.pdf p.9 (0.548) |
| 8 | VIS-008 | Q008 | FOUND @ 1 | obsdrones - bulletin de veille n3 - mai juin 2024.pdf p.16 | ObsDrones - Bulletin de veille n3 - Mai Juin 2024.pdf p.16 (0.408) |
| 9 | VIS-009 | Q009 | MISS | 20221012_np_emat_grat-2022.pdf p.1 | CDSE_VIGINUM_Guide_sensibilisation_entreprises_FR_12-25.pdf p.25 (0.373) |
| 10 | VIS-010 | Q010 | MISS | 20160108_np_cicde_004-lettre-grands-evenements-2.pdf p.3 | 20160108_NP_CICDE_004-Lettre-grands-evenements-2.pdf p.4 (0.405) |
| 11 | VIS-011 | Q011 | FOUND @ 1 | pec_livre-blanc-innovation_2025.pdf p.33 | PEC_LIVRE-BLANC-INNOVATION_2025.pdf p.33 (0.514) |
| 12 | VIS-012 | Q012 | FOUND @ 1 | etudepecapec_vfinale.pdf p.16 | EtudePECAPEC_VFinale.pdf p.16 (0.491) |
| 13 | VIS-013 | Q013 | FOUND @ 2 | fiche technique a330.pdf p.5 | ObsDrones - Bulletin de veille n6 - novembre-décembre 2024.pdf p.17 (0.462) |
| 14 | VIS-014 | Q014 | FOUND @ 2 | 20250612_tlp-clear_viginum_fcdo_eeas_rapport_technique_african_initiative_fr.pdf p.1 | 20250507_TLP-CLEAR_NP_SGDSN_VIGINUM_Rapport technique_Storm-1516.pdf p.1 (0.597) |
| 15 | VIS-015 | Q015 | FOUND @ 1 | unmanned_vehicles_size.pdf p.1 | unmanned_vehicles_size.pdf p.1 (0.517) |
| 16 | VIS-016 | Q016 | FOUND @ 1 | obsdrones - bulletin de veille n1 - janvier février 2024.pdf p.16 | ObsDrones - Bulletin de veille n1 - Janvier Février 2024.pdf p.16 (0.522) |
| 17 | VIS-017 | Q017 | FOUND @ 1 | communiqué_a_la dga commande cinq avions de surveillance albatros à dassault aviation.pdf p.2 | Communiqué_A_La DGA commande cinq avions de surveillance Albatros à Dassault Aviation.pdf p.2 (0.621) |
| 18 | VIS-018 | Q018 | MISS | bem-48.pdf p.21 | bem-48.pdf p.73 (0.381) |
| 19 | VIS-019 | Q019 | FOUND @ 1 | cdse_viginum_guide_sensibilisation_entreprises_fr_12-25.pdf p.23 | CDSE_VIGINUM_Guide_sensibilisation_entreprises_FR_12-25.pdf p.23 (0.521) |
| 20 | VIS-020 | Q020 | FOUND @ 4 | obsdrones - bulletin de veille n4 - juillet aout 2024.pdf p.16 | Stratégie nationale de lutte contre les manipulations de l'information_FR.pdf p.7 (0.455) |
| 21 | VIS-021 | Q021 | FOUND @ 3 | rnce_19_juillet_2023.pdf p.1 | 20190909_NP_EMAT-NP_LE508717-SYNTHESE-ANNUELLE-DU-RETEX-CYCLE-2018-2019-2.pdf p.2 (0.414) |
| 22 | VIS-022 | Q022 | FOUND @ 1 | 171110_np_arm-dpid_286-no-homologation-des-systemes-de-protection-de-site.pdf p.2 | 171110_np_arm-dpid_286-no-homologation-des-systemes-de-protection-de-site.pdf p.2 (0.540) |
| 23 | VIS-023 | Q023 | FOUND @ 1 | 20260122_np_tlp-clear_sgdsn_viginum_moi.pdf p.1 | 20260122_NP_TLP-CLEAR_SGDSN_VIGINUM_MOI.pdf p.1 (0.389) |
| 24 | VIS-024 | Q024 | MISS | 20250207_np_sgdsn_viginum_rapport menace informationnelle ia_vf.pdf p.1 | CDSE_VIGINUM_Guide_sensibilisation_entreprises_FR_12-25.pdf p.28 (0.394) |
| 25 | VIS-025 | Q025 | FOUND @ 3 | obsdrones - bulletin-de-veille-n05-septembre-octobre.pdf p.16 | ObsDrones - bulletin de veille n4 - Juillet Aout 2024.pdf p.16 (0.474) |
| 26 | VIS-026 | Q026 | MISS | 20230125_np_dpid-dame_extrait-memento-zicad.pdf p.20 | 20230125_NP_DPID-DAME_Extrait-memento-ZICAD.pdf p.19 (0.444) |
| 27 | VIS-027 | Q027 | FOUND @ 4 | obsdrones - bulletin de veille n2 - mars avril 2024.pdf p.16 | bem-48.pdf p.21 (0.450) |
| 28 | VIS-028 | Q028 | MISS | 2011113_igi 1300_protection du secret de la defense nationale_np.pdf p.145 | bem-48.pdf p.5 (0.402) |
| 29 | VIS-029 | Q029 | FOUND @ 1 | feuille de route stratégique osiic 2024-2027 np v1.0.pdf p.1 | Feuille de route stratégique OSIIC 2024-2027 NP v1.0.pdf p.1 (0.716) |
| 30 | VIS-030 | Q030 | FOUND @ 1 | 20160311_np_cicde_057_lettre_retex_lutte_prevention_contre_grands_fleaux.pdf p.6 | 20160311_NP_CICDE_057_Lettre_RETEX_Lutte_prevention_contre_grands_fleaux.pdf p.6 (0.509) |

## Misses
- VIS-004 / Q004: target `20190909_np_emat-np_le508717-synthese-annuelle-du-retex-cycle-2018-2019-2.pdf p.2`, top hit `20160426_np_cicde_084_lettre_synthese_croisee_gb-fr_operations_face_epid.pdf p.2 (0.610)`. Question: Quel organisme est indiqué comme destinataire de la copie ?
- VIS-005 / Q005: target `caia-125-bd-ok.pdf p.103`, top hit `CDSE_VIGINUM_Guide_sensibilisation_entreprises_FR_12-25.pdf p.11 (0.444)`. Question: Quels sont les cinq domaines d’activité présentés dans les vignettes en bas de l’affiche ?
- VIS-009 / Q009: target `20221012_np_emat_grat-2022.pdf p.1`, top hit `CDSE_VIGINUM_Guide_sensibilisation_entreprises_FR_12-25.pdf p.25 (0.373)`. Question: Quelle année est affichée en grands chiffres près du coin supérieur droit ?
- VIS-010 / Q010: target `20160108_np_cicde_004-lettre-grands-evenements-2.pdf p.3`, top hit `20160108_NP_CICDE_004-Lettre-grands-evenements-2.pdf p.4 (0.405)`. Question: Quelles sont les trois conditions indiquées comme nécessaires à la réussite de la participation des armées à la sécurité des grands événements ?
- VIS-018 / Q018: target `bem-48.pdf p.21`, top hit `bem-48.pdf p.73 (0.381)`. Question: Quel nom d’auteur apparaît en grandes lettres jaunes sous le sous-titre ?
- VIS-024 / Q024: target `20250207_np_sgdsn_viginum_rapport menace informationnelle ia_vf.pdf p.1`, top hit `CDSE_VIGINUM_Guide_sensibilisation_entreprises_FR_12-25.pdf p.28 (0.394)`. Question: Quel organisme est associé au logo en forme de bouclier contenant un réseau de points ?
- VIS-026 / Q026: target `20230125_np_dpid-dame_extrait-memento-zicad.pdf p.20`, top hit `20230125_NP_DPID-DAME_Extrait-memento-ZICAD.pdf p.19 (0.444)`. Question: Que se passe-t-il si l’opérateur ne complète pas son dossier de demande de dérogation ?
- VIS-028 / Q028: target `2011113_igi 1300_protection du secret de la defense nationale_np.pdf p.145`, top hit `bem-48.pdf p.5 (0.402)`. Question: Quel intitulé apparaît dans l’encadré bleu réservé à l’emplacement de la photo en haut à droite ?
