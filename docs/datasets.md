# Datasets: sources and licences

> Licence findings are from the official pages as read on 2026-11-09; re-check
> them at release. Exact URLs, sizes and hashes are in
> `nextunit/data/sources.json`; the raw files each converter reads are listed
> with their SHA-256 in `nextunit/benchmark/checksums/raw/`.

This repository contains **no data**. Each dataset is downloaded from the
source below and checked against SHA-256 hashes. Each keeps its original
licence; "not stated" means the official page carries no licence text, not
that redistribution is forbidden. Cite the original authors when you use a
dataset: see [Citations](#citations) below and [`datasets.bib`](datasets.bib)
(the same keys as in the paper).

**Non-commercial:** Paderborn (PUBD16) and MIMII DUE.
**Share-alike:** MATWI, CARE, MIMII DUE.

| Code | Dataset | Folds | Official source | Licence | Routes, in order of use |
|---|---|---:|---|---|---|
| PUBD16 | Paderborn bearings | 3 | Paderborn University, bearing data center | CC BY-NC 4.0 | official (manual) → PHMD mirror |
| XJTU-SY | XJTU-SY bearings | 3 | biaowang.tech/xjtu-sy-bearing-datasets | not stated (citation requested) | official (manual) → PHMD mirror |
| MATWI | MATWI tool wear | 3 | KU Leuven RDR, doi:10.48804/GK6LHH | CC BY-SA 4.0 | official |
| AHU21 | AHU fault detection | 3 | Mendeley Data jkw85sm4v4 | CC BY 4.0 | official → PHMD mirror |
| NB14 | NASA randomized battery usage | 3 | NASA PCoE data repository | not stated | official → PHMD mirror |
| CMAPSS | C-MAPSS FD004 | 1 | NASA PCoE data repository | not stated | official → PHMD mirror |
| CWRU | CWRU bearings | 4 | Case Western Reserve University bearing data center | not stated | official → PHMD mirror |
| MATR | Severson et al. 2019 battery cycle life | 1 | data.matr.io | not stated | official → PHMD mirror |
| MIMII_DUE | MIMII DUE | 1 | Zenodo 4740355 | CC BY-NC-SA 4.0 | official |
| BACKBLAZE | Backblaze hard drive data | 3 | Backblaze hard drive test data | custom terms (cite; do not sell the data) | official |
| PHME20 | PHM Europe 2020 filter clogging | 3 | PHM Society Europe 2020 data challenge | not stated | PHMD mirror |
| PRONOSTIA | FEMTO / PRONOSTIA bearings | 1 | FEMTO-ST; hosted by NASA PCoE | not stated | official → PHMD mirror |
| PHM10 | PHM 2010 milling cutters | 3 | PHM Society 2010 data challenge | not stated | PHMD mirror |
| SEU | SEU gearbox | 2 | github.com/cathysiyu/Mechanical-datasets | not stated (no LICENSE file) | official → PHMD mirror |
| HSF15 | UCI hydraulic systems | 3 | UCI Machine Learning Repository #447 | CC BY 4.0 | official → PHMD mirror |
| TEP | Tennessee Eastman process | 1 | Harvard Dataverse, doi:10.7910/DVN/6C3JR1 | public-domain dedication | official |
| NB1 | NASA battery ageing | 3 | NASA PCoE data repository | not stated | official → PHMD mirror |
| CALCE | CALCE CS2 batteries | 3 | University of Maryland CALCE battery data | not stated ("open access", citation requested) | PHMD mirror |
| NCMAPSS | N-CMAPSS DS02-006 | 1 | NASA PCoE data repository | not stated | official → PHMD mirror |
| IMS | IMS bearings | 3 | NASA PCoE data repository (University of Cincinnati) | not stated | official (manual) → PHMD mirror |
| CARE | CARE to Compare wind turbines | 3 | Zenodo 15846963 | CC BY-SA 4.0 | official |
| SCANIA | SCANIA Component X | 1 | Swedish National Data Service, doi:10.5878/bnh5-ka77 | CC BY 4.0 | official |
| THREEW | Petrobras 3W v2.0.0 | 3 | figshare, doi:10.6084/m9.figshare.29205836.v1 | CC BY 4.0 | official |
| CFRP | NASA CFRP composites | 3 | NASA PCoE data repository (Stanford) | not stated | official |

Total: 24 datasets, 58 folds.

**Routes.** "official" downloads from the publisher; "official (manual)"
needs a browser or archive tools and has written instructions; "PHMD mirror"
is the copy kept by the authors of the PHMD library in personal cloud
storage (third party, no licence statement), maintained by the PHMD project
(https://github.com/dasolma/phmd). Work that obtains data through the mirror
should cite the original publisher and PHMD: D. Solís-Martín, J. Galán-Páez,
J. Borrego-Díaz, "PHMD: An easy data access tool for prognosis and health
management datasets", *SoftwareX* 29 (2025) 102039,
doi:10.1016/j.softx.2025.102039. Please download each dataset once rather
than repeatedly. For every dataset that has both, the official files were
checked against the mirror's on 2026-11-11 and found identical (CRC32 and
size per file, or SHA-256 where the publisher gives one); exceptions: the
official Paderborn KB27 archive has 45 more measurements than the mirror
(the benchmark uses the mirror's 35), CALCE is published as spreadsheets
that the mirror converted to CSV, and IMS was not checked (nested 7z and
RAR).

## Citations

Original publication of each dataset, as cited in the paper; BibTeX in
[`datasets.bib`](datasets.bib), which also holds the PHMD entry for the
mirror route.

| Dataset | Original publication | BibTeX key |
|---|---|---|
| PUBD16 | Lessmeier et al. (2016). Condition Monitoring of Bearing Damage in Electromechanical Drive Systems by Using Motor Current Signals of Electric Motors: A Benchmark Data Set for Data-Driven Classification. Proc. European Conf. Prognostics and Health Management Society (PHME) 3. doi:10.36001/phme.2016.v3i1.1577 | `lessmeier2016paderborn` |
| CWRU | Smith and Randall (2015). Rolling Element Bearing Diagnostics Using the Case Western Reserve University Data: A Benchmark Study. Mechanical Systems and Signal Processing 64–65, 100–131. doi:10.1016/j.ymssp.2015.04.021 | `smith2015cwru` |
| SEU | Shao et al. (2019). Highly Accurate Machine Fault Diagnosis Using Deep Transfer Learning. IEEE Transactions on Industrial Informatics 15, 2446–2455. doi:10.1109/TII.2018.2864759 | `shao2019highly` |
| HSF15 | Helwig et al. (2015). Condition Monitoring of a Complex Hydraulic System Using Multivariate Statistics. Proc. IEEE Int. Instrumentation and Measurement Technology Conf. (I2MTC), 210–215. doi:10.1109/I2MTC.2015.7151267 | `helwig2015hydraulic` |
| TEP | Rieth et al. (2017). Additional Tennessee Eastman Process Simulation Data for Anomaly Detection Evaluation. Harvard Dataverse, V1. doi:10.7910/DVN/6C3JR1 | `rieth2017tep` |
| THREEW | Vaz Vargas et al. (2026). 3W Dataset 2.0.0: a realistic and public dataset with rare undesirable real events in oil wells. Scientific Data 13, 949. doi:10.1038/s41597-026-07225-z | `vaz2026threew` |
| AHU21 | Nehasil et al. (2021). Versatile AHU fault detection – Design, field validation and practical application. Energy and Buildings 237, 110781. doi:10.1016/j.enbuild.2021.110781 | `nehasil2021ahu` |
| SCANIA | Kharazian et al. (2025). SCANIA Component X dataset: a real-world multivariate time series dataset for predictive maintenance. Scientific Data 12, 493. doi:10.1038/s41597-025-04802-6 | `kharazian2025scania` |
| XJTU-SY | Wang et al. (2020). A Hybrid Prognostics Approach for Estimating Remaining Useful Life of Rolling Element Bearings. IEEE Transactions on Reliability 69, 401–412. doi:10.1109/TR.2018.2882682 | `wang2020xjtu` |
| PRONOSTIA | Nectoux et al. (2012). PRONOSTIA: An Experimental Platform for Bearings Accelerated Degradation Tests. Proc. IEEE Int. Conf. Prognostics and Health Management (PHM'12), 1–8. | `nectoux2012pronostia` |
| IMS | Qiu et al. (2006). Wavelet Filter-Based Weak Signature Detection Method and Its Application on Rolling Element Bearing Prognostics. Journal of Sound and Vibration 289, 1066–1090. doi:10.1016/j.jsv.2005.03.007 | `qiu2006ims` |
| CMAPSS | Saxena et al. (2008). Damage Propagation Modeling for Aircraft Engine Run-to-Failure Simulation. Proc. Int. Conf. Prognostics and Health Management (PHM), 1–9. doi:10.1109/PHM.2008.4711414 | `saxena2008cmapss` |
| NCMAPSS | Arias Chao et al. (2021). Aircraft Engine Run-to-Failure Dataset under Real Flight Conditions for Prognostics and Diagnostics. Data 6, 5. doi:10.3390/data6010005 | `arias2021ncmapss` |
| PHME20 | PHM Society (2020). PHM Europe 2020 Data Challenge: Remaining Useful Life Prediction for an Experimental Filtration System. http://phmeurope.org/2020/data-challenge-2020. | `phme2020challenge` |
| MATR | Severson et al. (2019). Data-driven prediction of battery cycle life before capacity degradation. Nature Energy 4, 383–391. doi:10.1038/s41560-019-0356-8 | `severson2019matr` |
| MATWI | De Pauw et al. (2023). MATWI: A Multimodal Automatic Tool Wear Inspection Dataset and Baseline Algorithms. Computer Vision Systems (ICVS 2023), Lecture Notes in Computer Science, 255–269. doi:10.1007/978-3-031-44137-0_22 | `depauw2023matwi` |
| PHM10 | PHM Society (2010). 2010 PHM Society Conference Data Challenge. https://phmsociety.org/phm_competition/2010-phm-society-conference-data-challenge/. | `phm2010challenge` |
| NB14 | Bole et al. (2014). Adaptation of an Electrochemistry-based Li-Ion Battery Model to Account for Deterioration Observed Under Randomized Use. Annual Conf. Prognostics and Health Management Society 6. doi:10.36001/phmconf.2014.v6i1.2490 | `bole2014randomized` |
| NB1 | Saha and Goebel (2007). Battery Data Set. NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA. | `saha2007battery` |
| CALCE | He et al. (2011). Prognostics of Lithium-Ion Batteries Based on Dempster–Shafer Theory and the Bayesian Monte Carlo Method. Journal of Power Sources 196, 10314–10321. doi:10.1016/j.jpowsour.2011.08.040 | `he2011calce` |
| CFRP | Saxena et al. (2008). CFRP Composites Data Set. NASA Prognostics Data Repository, NASA Ames Research Center, Moffett Field, CA. | `saxena2008cfrp` |
| MIMII_DUE | Tanabe et al. (2021). MIMII Due: Sound Dataset for Malfunctioning Industrial Machine Investigation and Inspection with Domain Shifts Due to Changes in Operational and Environmental Conditions. 2021 IEEE Workshop on Applications of Signal Processing to Audio and Acoustics (WASPAA), 21–25. doi:10.1109/WASPAA52581.2021.9632802 | `tanabe2021mimiidue` |
| CARE | Gück et al. (2024). CARE to Compare: A Real-World Benchmark Dataset for Early Fault Detection in Wind Turbine Data. Data 9, 138. doi:10.3390/data9120138 | `gueck2024care` |
| BACKBLAZE | Backblaze (2024). Backblaze Hard Drive Test Data. https://www.backblaze.com/cloud-storage/resources/hard-drive-test-data, file data_Q4_2024.zip. | `backblaze2024drive` |
