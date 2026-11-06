## ARCAID3 startup guard (one added code cell)

Base: **habanwer/arcaid3-lexicon-dprime-dfranzen-m2 version 1 (scriptVersionId 360147562; byte-identical version scored 21.18 on 2026-10-19, then COMPLETE 0.00 on 10-21 and 10-22 (57483523, 57510463))**, all original cells unchanged and in order, except the Kaggle-gateway wait in *9. Run the benchmark* (600 s -> 1800 s).
- **Why:** since Oct 20 the model load on Kaggle takes 35-65 min instead of ~10. The stock notebook gives up on the server at ~27 min and the scorecard closes after 15 min with no action, so the rerun ends COMPLETE with 0.00 (Kaggle discussion 751598).
- **The added cell:** each game waits for the model server's `/health` before its first analyzer call; while games wait, one of them sends a RESET every 7 min (one per game, fewest first) so the scorecard stays open. The hold ends when the server is healthy, when it exits, or 2 h after notebook start.
- **Kill switch:** `SG=0`. Knobs: `SG_KEEPALIVE_S` (420), `SG_HOLD_MAX_S` (7200).

Source: `kaggle/startup_guard/` in the HabAnwer ARCAID3 repository.
