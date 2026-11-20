# Tables recomputed from paper/data/

## Table II: agent scores under alternative choices

| Agent | S (24) | S, floor -100 | S, without shortcut sets | S, 21 unit sets | Fail (%) | Worse (%) |
|---|---|---|---|---|---|---|
| Astra | 43.0 (1) [32.4, 53.8] | 33.8 (2) [15.5, 50.0] | 40.4 (1) [29.4, 52.0] | 37.9 (1) [28.3, 46.8] | 0.0 | 8.6 |
| Kimi | 39.7 (2) [29.2, 51.0] | 37.7 (1) [26.6, 49.5] | 38.4 (2) [26.6, 50.7] | 34.7 (2) [25.1, 44.1] | 1.7 | 8.6 |
| DeepSeek | 36.1 (3) [25.7, 46.9] | 30.9 (3) [18.7, 43.5] | 34.7 (3) [24.2, 46.0] | 31.0 (3) [22.6, 39.7] | 0.0 | 10.3 |
| Luna | 30.8 (4) [19.4, 43.1] | 17.5 (4) [-2.3, 35.7] | 29.2 (4) [17.5, 41.9] | 24.4 (4) [15.0, 34.7] | 1.7 | 20.7 |
| Qwen3.6 | 14.3 [5.9, 24.8] | 0.8 [-13.5, 15.8] | 14.4 [5.4, 25.7] | 8.3 [3.6, 13.6] | 29.3 | 27.6 |
| Gemma 4 | 16.5 [9.2, 25.4] | 0.0 [-15.6, 14.6] | 16.7 [9.3, 25.5] | 12.4 [7.1, 18.1] | 3.4 | 32.8 |

## Table III: score by plan author, data seen, implementer (S over 24 datasets; second run in parentheses)

| Plan by | Data seen | Carried out by Luna | Carried out by Astra |
|---|---|---|---|
| Astra | yes | 36.8 (37.8) | 44.2 (own run, no plan) |
| Luna | yes | 31.0 (own run, no plan) | 31.5 (31.5) |
| Astra | no | 27.6 | 29.5 (30.0) |
| Luna | no | 26.0 (23.8) | 28.0 (28.6) |

Also used in the text: Luna given Astra's no-data plans as advice 30.4; Astra following its own lightened plans 42.6.

## Table VI: published methods implemented by Astra (S of the method; S of Astra's own design on the same folds)

| Dataset | Method | Year | S (method) | S (Astra) | Beat |
|---|---|---|---|---|---|
| CMAPSS | Dual-task LSTM | 2019 | 21.0 | 44.7 | 0/1 |
| CMAPSS | DA-TCN | 2021 | 23.4 | 44.7 | 0/1 |
| CMAPSS | Two-stream Bi-LSTM | 2022 | 21.4 | 44.7 | 0/1 |
| CMAPSS | DSFormer | 2024 | 9.4 | 44.7 | 0/1 |
| CMAPSS | MSBLS | 2024 | 9.3 | 44.7 | 0/1 |
| PUBD16 | Three-stage fusion | 2021 | 32.6 | 60.4 | 1/3 |
| PUBD16 | LiteFormer | 2024 | 21.0 | 60.4 | 0/3 |
| PUBD16 | MABFN | 2023 | 34.3 | 60.4 | 0/3 |
| PUBD16 | CAFormer | 2025 | 3.6 | 60.4 | 0/3 |
| PUBD16 | MSHFFN | 2025 | 43.1 | 60.4 | 0/3 |
| TEP | Enhanced RF (static/dynamic nodes) | 2020 | 0.0 | 30.1 | 0/1 |
| TEP | SKLFDA | 2020 | 13.7 | 30.1 | 0/1 |
| TEP | MRCNN-LSTM fusion | 2023 | 46.1 | 30.1 | 1/1 |
| TEP | MRCC-Transformer | 2025 | 47.5 | 30.1 | 1/1 |
| TEP | GNN, trainable adjacency | 2024 | 44.6 | 30.1 | 1/1 |
| NCMAPSS | CART-Net | 2025 | 43.2 | 38.1 | 1/1 |
| NCMAPSS | Failure prediction + RUL (LSTM) | 2023 | 9.3 | 38.1 | 0/1 |
| NCMAPSS | Condition-indicator pipeline | 2023 | 27.6 | 38.1 | 0/1 |
| NCMAPSS | MR-LSTM | 2024 | 48.3 | 38.1 | 1/1 |
| NCMAPSS | CDSG (graph NN) | 2023 | 30.6 | 38.1 | 0/1 |
