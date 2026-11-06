# Lineage

How each of our notebook versions descends from earlier notebooks, ours and others'. The tree is **inferred from code**, not typed by hand:

- **Parent:** for every version, the notebook that started running earlier and has the fewest differing code lines (`Tools/lineage/infer_parents.py`).
- **Ties:** go to the earliest original, so an unchanged copy is never credited over its source.
- **Diffs:** every version folder holds a cell diff against this parent (`DIFF.md`) and, where the parent is ours, against the third-party notebook at the root of its chain (`vs-root-base/DIFF.md`).

**Third-party roots** are notebooks by other authors. They are cited in [`../Documentation/REFERENCES.md`](../Documentation/REFERENCES.md).

## Our own code (no earlier notebook shares 30% of its lines)

- [`arc3-duck-fp4-depth@v1`](../Submissions/ARC-AGI-3/_development/2026-09-19__arc3-duck-fp4-depth/v1__not-run__no-saved-run/) · development
- [`arc-prize-2026-arc-agi-3-starter@v1`](../Submissions/ARC-AGI-3/2026-09-05__arc-prize-2026-arc-agi-3-starter/v1__2026-09-05__LB-0.02/) · LB 0.02 · submissions
  - [`arc-prize-2026-arc-agi-3-starter@v2`](../Submissions/ARC-AGI-3/2026-09-05__arc-prize-2026-arc-agi-3-starter/v2__2026-09-05__LB-0.09/) · 874 lines from parent · LB 0.09 · submissions
    - [`arc-prize-2026-arc-agi-3-starter@v3`](../Submissions/ARC-AGI-3/2026-09-05__arc-prize-2026-arc-agi-3-starter/v3__2026-09-07__LB-0.09/) · 286 lines from parent · LB 0.09 · submissions
      - [`arc-prize-2026-arc-agi-3-starter@v4`](../Submissions/ARC-AGI-3/2026-09-05__arc-prize-2026-arc-agi-3-starter/v4__2026-09-08__LB-0.13/) · 218 lines from parent · LB 0.13 · submissions
        - [`arc-prize-2026-arc-agi-3-starter@v5`](../Submissions/ARC-AGI-3/2026-09-05__arc-prize-2026-arc-agi-3-starter/v5__2026-09-11__save-run/) · 136 lines from parent · submissions
          - [`arc-prize-2026-arc-agi-3-starter@v6`](../Submissions/ARC-AGI-3/2026-09-05__arc-prize-2026-arc-agi-3-starter/v6__2026-09-11__LB-0.13/) · 0 lines from parent · LB 0.13 · submissions
          - [`arc-prize-2026-arc-agi-3-starter@v7`](../Submissions/ARC-AGI-3/2026-09-05__arc-prize-2026-arc-agi-3-starter/v7__2026-09-13__LB-0.13/) · 87 lines from parent · LB 0.13 · submissions
            - [`arc-prize-2026-arc-agi-3-starter@v8`](../Submissions/ARC-AGI-3/2026-09-05__arc-prize-2026-arc-agi-3-starter/v8__2026-09-13__LB-0.07/) · 11 lines from parent · LB 0.07 · submissions
            - [`arc-prize-2026-arc-agi-3-starter@v9`](../Submissions/ARC-AGI-3/2026-09-05__arc-prize-2026-arc-agi-3-starter/v9__2026-09-14__LB-0.13/) · 18 lines from parent · LB 0.13 · submissions
- [`arcaid3-mount-diag@v1`](../Tools/diagnostics/arcaid3-mount-diag/runs/v1__2026-10-14__save-run/) · tools
- [`arcaid3-mount-diag@v2`](../Tools/diagnostics/arcaid3-mount-diag/runs/v2__2026-10-14__save-run/) · tools
- [`arcaid3-mount-diag@v3`](../Tools/diagnostics/arcaid3-mount-diag/runs/v3__2026-10-22__save-run/) · tools
- [`arcaid3-mount-diag@v4`](../Tools/diagnostics/arcaid3-mount-diag/runs/v4__2026-10-22__save-run/) · tools

## dfranzen/arc-agi-3-milestone-2-solution@v1

- [`arcaid3-lexicon-view-dfranzen-m2@v1`](../Submissions/ARC-AGI-3/2026-10-05__arcaid3-lexicon-view-dfranzen-m2/v1__2026-10-05__LB-24.95/) · 771 lines from parent · LB 24.95 · submissions
  - [`arcaid3-lexicon-view-dfranzen-m2@v2`](../Submissions/ARC-AGI-3/2026-10-05__arcaid3-lexicon-view-dfranzen-m2/v2__2026-10-07__save-run/) · 172 lines from parent · submissions
    - [`arcaid3-lexicon-view-dfranzen-m2@v3`](../Submissions/ARC-AGI-3/2026-10-05__arcaid3-lexicon-view-dfranzen-m2/v3__2026-10-08__save-run/) · 821 lines from parent · submissions
      - [`arcaid3-lexicon-view-dfranzen-m2@v4`](../Submissions/ARC-AGI-3/2026-10-05__arcaid3-lexicon-view-dfranzen-m2/v4__2026-10-08__LB-27.05_31.90_26.83__SELECTED/) · 281 lines from parent · LB 27.05, 31.90, 26.83 · submissions
        - [`arcaid3-rep-v4-r1@v1`](../Ablations/ARC-AGI-3/2026-10-09__A1-replicates-v2-vs-v4/runs/arcaid3-rep-v4-r1/v1__2026-10-09__save-run/) · 0 lines from parent · ablations
        - [`arcaid3-rep-v4-r2@v1`](../Ablations/ARC-AGI-3/2026-10-09__A1-replicates-v2-vs-v4/runs/arcaid3-rep-v4-r2/v1__2026-10-09__save-run/) · 0 lines from parent · ablations
        - [`arcaid3-lb-lex-r1@v1`](../Ablations/ARC-AGI-3/2026-10-09__A2-lexicon-on-vs-off/runs/arcaid3-lb-lex-r1/v1__2026-10-09__save-run/) · 48 lines from parent · ablations
          - [`arcaid3-lb-off-r1@v1`](../Ablations/ARC-AGI-3/2026-10-09__A2-lexicon-on-vs-off/runs/arcaid3-lb-off-r1/v1__2026-10-09__save-run/) · 4 lines from parent · ablations
            - [`arcaid3-lb-off-r2@v1`](../Ablations/ARC-AGI-3/2026-10-09__A2-lexicon-on-vs-off/runs/arcaid3-lb-off-r2/v1__2026-10-09__save-run/) · 0 lines from parent · ablations
          - [`arcaid3-lb-lex-r2@v1`](../Ablations/ARC-AGI-3/2026-10-09__A2-lexicon-on-vs-off/runs/arcaid3-lb-lex-r2/v1__2026-10-09__save-run/) · 0 lines from parent · ablations
          - [`arcaid3-lt-lex-r1@v1`](../Ablations/ARC-AGI-3/2026-10-09__A3-level-trials-lexicon/runs/arcaid3-lt-lex-r1/v1__2026-10-09__save-run/) · 58 lines from parent · ablations
            - [`arcaid3-lt-off-r1@v1`](../Ablations/ARC-AGI-3/2026-10-09__A3-level-trials-lexicon/runs/arcaid3-lt-off-r1/v1__2026-10-09__save-run/) · 4 lines from parent · ablations
            - [`arcaid3-lt-lex-r2@v1`](../Ablations/ARC-AGI-3/2026-10-09__A3-level-trials-lexicon/runs/arcaid3-lt-lex-r2/v1__2026-10-10__save-run/) · 10 lines from parent · ablations
              - [`arcaid3-lt-off-r2@v1`](../Ablations/ARC-AGI-3/2026-10-09__A3-level-trials-lexicon/runs/arcaid3-lt-off-r2/v1__2026-10-10__save-run/) · 4 lines from parent · ablations
                - [`arcaid3-lt-off-r3@v1`](../Ablations/ARC-AGI-3/2026-10-09__A3-level-trials-lexicon/runs/arcaid3-lt-off-r3/v1__2026-10-10__save-run/) · 4 lines from parent · ablations
              - [`arcaid3-lt-lex-r3@v1`](../Ablations/ARC-AGI-3/2026-10-09__A3-level-trials-lexicon/runs/arcaid3-lt-lex-r3/v1__2026-10-10__LB-7.16/) · 4 lines from parent · LB 7.16 · ablations
          - [`arcaid3-lexicon-view-dfranzen-m2@v5`](../Submissions/ARC-AGI-3/2026-10-05__arcaid3-lexicon-view-dfranzen-m2/v5__2026-10-17__LB-27.79_24.35/) · 113 lines from parent · LB 27.79, 24.35 · submissions
            - [`arcaid3-lexicon-view-dfranzen-m2@v6`](../Submissions/ARC-AGI-3/2026-10-05__arcaid3-lexicon-view-dfranzen-m2/v6__2026-10-17__save-run/) · 0 lines from parent · submissions
            - [`arcaid3-lexicon-dprime-dfranzen-m2@v1`](../Submissions/ARC-AGI-3/2026-10-19__arcaid3-lexicon-dprime-dfranzen-m2/v1__2026-10-19__LB-21.18_0.00_0.00/) · 57 lines from parent · LB 21.18, 0.00, 0.00 · submissions
              - [`arcaid3-lexicon-dprime-dfranzen-m2-sg@v1`](../Submissions/ARC-AGI-3/2026-10-25__arcaid3-lexicon-dprime-dfranzen-m2-sg/v1__2026-10-25__LB-25.26_27.47_22.23/) · 204 lines from parent · LB 25.26, 27.47, 22.23 · submissions
    - [`arcaid3-rep-v2-r1@v1`](../Ablations/ARC-AGI-3/2026-10-09__A1-replicates-v2-vs-v4/runs/arcaid3-rep-v2-r1/v1__2026-10-09__save-run/) · 0 lines from parent · ablations
    - [`arcaid3-rep-v2-r2@v1`](../Ablations/ARC-AGI-3/2026-10-09__A1-replicates-v2-vs-v4/runs/arcaid3-rep-v2-r2/v1__2026-10-09__save-run/) · 0 lines from parent · ablations
- [`arcaid3-restart-dfranzen-m2@v1`](../Ablations/ARC-AGI-3/2026-10-12__restart-v1/runs/arcaid3-restart-dfranzen-m2/v1__2026-10-12__LB-25.76/) · 145 lines from parent · LB 25.76 · ablations
  - [`arcaid3-restart-dfranzen-m2-r2@v1`](../Ablations/ARC-AGI-3/2026-10-12__restart-v1/runs/arcaid3-restart-dfranzen-m2-r2/v1__2026-10-12__save-run/) · 0 lines from parent · ablations
  - [`arcaid3-pair-restart-r1@v1`](../Ablations/ARC-AGI-3/2026-10-13__restart-pair/runs/arcaid3-pair-restart-r1/v1__2026-10-14__LB-24.42/) · 111 lines from parent · LB 24.42 · ablations
    - [`arcaid3-pair-flag0-r1@v1`](../Ablations/ARC-AGI-3/2026-10-13__restart-pair/runs/arcaid3-pair-flag0-r1/v1__2026-10-14__save-run-error/) · 2 lines from parent · ablations
      - [`arcaid3-pair-flag0-r1@v2`](../Ablations/ARC-AGI-3/2026-10-13__restart-pair/runs/arcaid3-pair-flag0-r1/v2__2026-10-14__save-run-error/) · 0 lines from parent · ablations
      - [`arcaid3-pair-flag0-r1@v3`](../Ablations/ARC-AGI-3/2026-10-13__restart-pair/runs/arcaid3-pair-flag0-r1/v3__2026-10-14__save-run-error/) · 0 lines from parent · ablations
      - [`arcaid3-pair-flag0-r1b@v1`](../Ablations/ARC-AGI-3/2026-10-13__restart-pair/runs/arcaid3-pair-flag0-r1b/v1__2026-10-14__LB-26.22/) · 0 lines from parent · LB 26.22 · ablations
- [`arcaid3-probe-first-dfranzen-m2@v1`](../Submissions/ARC-AGI-3/2026-10-23__arcaid3-probe-first-dfranzen-m2/v1__2026-10-23__save-run/) · 203 lines from parent · submissions
  - [`arcaid3-probe-first-dfranzen-m2@v2`](../Submissions/ARC-AGI-3/2026-10-23__arcaid3-probe-first-dfranzen-m2/v2__2026-10-23__LB-0.00/) · 113 lines from parent · LB 0.00 · submissions
    - [`arcaid3-lt-pf-off-r1@v1`](../Ablations/ARC-AGI-3/2026-10-24__level-trials-probe-first/runs/arcaid3-lt-pf-off-r1/v1__2026-10-24__save-run/) · 65 lines from parent · ablations
      - [`arcaid3-lt-pf-on-r1@v1`](../Ablations/ARC-AGI-3/2026-10-24__level-trials-probe-first/runs/arcaid3-lt-pf-on-r1/v1__2026-10-24__save-run/) · 2 lines from parent · ablations
        - [`arcaid3-lt-pf-on-r2@v1`](../Ablations/ARC-AGI-3/2026-10-24__level-trials-probe-first/runs/arcaid3-lt-pf-on-r2/v1__2026-10-24__LB-error/) · 2 lines from parent · LB error · ablations
      - [`arcaid3-lt-pf-off-r2@v1`](../Ablations/ARC-AGI-3/2026-10-24__level-trials-probe-first/runs/arcaid3-lt-pf-off-r2/v1__2026-10-24__save-run/) · 2 lines from parent · ablations
    - [`arcaid3-probe-first-dfranzen-m2-sg@v1`](../Submissions/ARC-AGI-3/2026-10-25__arcaid3-probe-first-dfranzen-m2-sg/v1__2026-10-25__LB-23.41_30.57__SELECTED/) · 204 lines from parent · LB 23.41, 30.57 · submissions

## foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b@v6

- [`arc3-duck-qwen38-baseline@v1`](../Submissions/ARC-AGI-3/2026-09-16__arc3-duck-qwen38-baseline/v1__2026-09-16__LB-1.37/) · 32 lines from parent · LB 1.37 · submissions
  - [`arc3-duck-ab-tricks@v1`](../Ablations/ARC-AGI-3/2026-09-18__ab-tricks/runs/arc3-duck-ab-tricks/v1__2026-09-16__save-run-error/) · 90 lines from parent · ablations
    - [`arc3-duck-ab-tricks@v2`](../Ablations/ARC-AGI-3/2026-09-18__ab-tricks/runs/arc3-duck-ab-tricks/v2__2026-09-18__save-run/) · 146 lines from parent · ablations
      - [`arc3-duck-ab-tricks@v3`](../Ablations/ARC-AGI-3/2026-09-18__ab-tricks/runs/arc3-duck-ab-tricks/v3__2026-09-18__save-run/) · 19 lines from parent · ablations

## keithtyser/duck-qwen3-8-flash-next-nvfp4-mtp@v13

- [`arc3-duck-fp4-serving@v1`](../Submissions/ARC-AGI-3/2026-09-18__arc3-duck-fp4-serving/v1__2026-09-18__LB-2.49/) · 4 lines from parent · LB 2.49 · submissions
  - [`arc3-duck-fp4-batch@v1`](../Submissions/ARC-AGI-3/2026-09-18__arc3-duck-fp4-batch/v1__2026-09-18__LB-3.04/) · 59 lines from parent · LB 3.04 · submissions
    - [`arc3-duck-fp4-depth@v2`](../Submissions/ARC-AGI-3/_development/2026-09-19__arc3-duck-fp4-depth/v2__2026-09-19__save-run-error/) · 68 lines from parent · development
      - [`arc3-duck-fp4-stall@v1`](../Submissions/ARC-AGI-3/_development/2026-09-19__arc3-duck-fp4-stall/v1__2026-09-19__save-run-error/) · 110 lines from parent · development
        - [`arc3-duck-fp4-stall@v2`](../Submissions/ARC-AGI-3/_development/2026-09-19__arc3-duck-fp4-stall/v2__2026-09-19__save-run/) · 2 lines from parent · development
          - [`arc3-duck-fp4-reset@v1`](../Submissions/ARC-AGI-3/2026-09-19__arc3-duck-fp4-reset/v1__2026-09-19__save-run-error/) · 79 lines from parent · submissions
            - [`arc3-duck-fp4-reset@v2`](../Submissions/ARC-AGI-3/2026-09-19__arc3-duck-fp4-reset/v2__2026-09-19__save-run-error/) · 8 lines from parent · submissions
              - [`arc3-duck-fp4-reset@v3`](../Submissions/ARC-AGI-3/2026-09-19__arc3-duck-fp4-reset/v3__2026-09-20__LB-3.37/) · 16 lines from parent · LB 3.37 · submissions
                - [`arc3-duck-fp4-reset@v4`](../Submissions/ARC-AGI-3/2026-09-19__arc3-duck-fp4-reset/v4__2026-09-20__LB-2.84/) · 2 lines from parent · LB 2.84 · submissions
                - [`duck-nvfp4-batch-stall-warn-dead-sign@v1`](../Submissions/ARC-AGI-3/2026-09-23__duck-nvfp4-batch-stall-warn-dead-sign/v1__2026-09-23__LB-3.39/) · 56 lines from parent · LB 3.39 · submissions
                  - [`duck-nvfp4-batch-stall-warn-dead-sign@v2`](../Submissions/ARC-AGI-3/2026-09-23__duck-nvfp4-batch-stall-warn-dead-sign/v2__2026-09-23__save-run/) · 8 lines from parent · submissions
                  - [`duck-nvfp4-batch-stall-warn-dead-sign@v3`](../Submissions/ARC-AGI-3/2026-09-23__duck-nvfp4-batch-stall-warn-dead-sign/v3__2026-09-25__LB-3.59/) · 148 lines from parent · LB 3.59 · submissions
                    - [`duck-nvfp4-batch-stall-warn-dead-sign@v4`](../Submissions/ARC-AGI-3/2026-09-23__duck-nvfp4-batch-stall-warn-dead-sign/v4__2026-09-25__save-run/) · 76 lines from parent · submissions
                    - [`arc3-duck-fp4-kvfp8@v1`](../Submissions/ARC-AGI-3/_development/2026-09-26__arc3-duck-fp4-kvfp8/v1__2026-09-26__save-run-error/) · 62 lines from parent · development
                    - [`duck-nvfp4-batch-stall-warn-dead-sign@v5`](../Submissions/ARC-AGI-3/2026-09-23__duck-nvfp4-batch-stall-warn-dead-sign/v5__2026-09-26__save-run-error/) · 223 lines from parent · submissions
                      - [`notebook7c0bf2022d@v1`](../Submissions/ARC-AGI-3/_development/2026-09-26__notebook7c0bf2022d/v1__2026-09-26__save-run/) · 0 lines from parent · development
                      - [`duck-nvfp4-batch-stall-warn-dead-sign-compact@v1`](../Submissions/ARC-AGI-3/2026-09-26__duck-nvfp4-batch-stall-warn-dead-sign-compact/v1__2026-09-26__LB-2.78/) · 142 lines from parent · LB 2.78 · submissions
                        - [`v5b-v5-compact-keep-reasoning-8-min-bytes-sk@v1`](../Submissions/ARC-AGI-3/_development/2026-09-28__v5b-v5-compact-keep-reasoning-8-min-bytes-sk/v1__2026-09-28__save-run/) · 37 lines from parent · development
                    - [`duck-v3-wmreason@v1`](../Submissions/ARC-AGI-3/2026-09-27__duck-v3-wmreason/v1__2026-09-27__LB-3.03/) · 74 lines from parent · LB 3.03 · submissions
  - [`arc3-duck-fp4-ledger@v1`](../Submissions/ARC-AGI-3/2026-09-22__arc3-duck-fp4-ledger/v1__2026-09-22__LB-2.57/) · 95 lines from parent · LB 2.57 · submissions
    - [`arc3-duck-fp4-prompts@v1`](../Submissions/ARC-AGI-3/2026-09-22__arc3-duck-fp4-prompts/v1__2026-09-22__LB-3.01/) · 57 lines from parent · LB 3.01 · submissions

## madarshbb/arc-qwen-3-8-27b-agent@v1

- [`arcaid3-lexicon-agent-arc-agi-2@v1`](../Submissions/ARC-AGI-2/2026-10-31__arcaid3-lexicon-agent-arc-agi-2/v1__2026-10-31__LB-0.00/) · 579 lines from parent · LB 0.00 · submissions
  - [`arcaid3-lexicon-agent-arc-agi-2@v2`](../Submissions/ARC-AGI-2/2026-10-31__arcaid3-lexicon-agent-arc-agi-2/v2__2026-11-01__save-run/) · 42 lines from parent · submissions
    - [`arcaid3-lexicon-agent-arc-agi-2@v4`](../Submissions/ARC-AGI-2/2026-10-31__arcaid3-lexicon-agent-arc-agi-2/v4__2026-11-01__save-run/) · 4 lines from parent · submissions
      - [`arcaid3-lexicon-agent-arc-agi-2@v5`](../Submissions/ARC-AGI-2/2026-10-31__arcaid3-lexicon-agent-arc-agi-2/v5__2026-11-01__save-run/) · 12 lines from parent · submissions
        - [`arcaid3-lexicon-agent-arc-agi-2@v6`](../Submissions/ARC-AGI-2/2026-10-31__arcaid3-lexicon-agent-arc-agi-2/v6__2026-11-01__LB-10.83_late-10.69_late-11.25/) · 102 lines from parent · LB 10.83, 10.69 (late), 11.25 (late) · submissions
    - [`arcaid3-lexicon-agent-arc-agi-2@v3`](../Submissions/ARC-AGI-2/2026-10-31__arcaid3-lexicon-agent-arc-agi-2/v3__2026-11-01__save-run/) · 0 lines from parent · submissions

## scottlegrand/taaf-flashnext-sheetu12b-0922@v1

- [`taaf-flashnext-sheetu12b-reasoning-notes@v1`](../Submissions/ARC-AGI-3/2026-09-27__taaf-flashnext-sheetu12b-reasoning-notes/v1__not-run__save-run/) · 74 lines from parent · submissions
  - [`taaf-flashnext-sheetu12b-reasoning-notes@v2`](../Submissions/ARC-AGI-3/2026-09-27__taaf-flashnext-sheetu12b-reasoning-notes/v2__not-run__save-run/) · 0 lines from parent · submissions
- [`taaf-flashnext-sheetu12b-reasoning-notes@v3`](../Submissions/ARC-AGI-3/2026-09-27__taaf-flashnext-sheetu12b-reasoning-notes/v3__2026-09-27__LB-3.90/) · 74 lines from parent · LB 3.90 · submissions
- [`taaf-flashnext-sheetu12b-0922@v1`](../Submissions/ARC-AGI-3/2026-09-30__taaf-flashnext-sheetu12b-0922/v1__2026-09-30__LB-4.17/) · 0 lines from parent · LB 4.17 · submissions
- [`arcaid3-lexicon-view@v1`](../Submissions/ARC-AGI-3/2026-10-03__arcaid3-lexicon-view/v1__2026-10-03__LB-error/) · 681 lines from parent · LB error · submissions
  - [`arcaid3-lexicon-view-py312@v1`](../Ablations/ARC-AGI-3/2026-10-04__lexicon-view-read-or-not/runs/arcaid3-lexicon-view-py312/v1__2026-10-04__save-run/) · 0 lines from parent · ablations
  - [`arcaid3-lexicon-view-v2@v1`](../Submissions/ARC-AGI-3/2026-10-04__arcaid3-lexicon-view-v2/v1__2026-10-04__LB-4.56/) · 92 lines from parent · LB 4.56 · submissions

