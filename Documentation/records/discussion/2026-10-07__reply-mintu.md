Thanks Mintu, good question. It is exactly where the view is weakest.

**Short answer: names survive, identities don't.** A name belongs to a *picture*, not to an individual object: it is derived from the picture's pixels, so two identical sprites share one name. When they touch, the cut sees one bigger picture and gives it a new name. When they separate, each piece is the original picture again, so the original name comes back by itself. What is lost is *which copy is which*: nothing tracks individuals across the contact.

Real lexicon output on a toy board (two identical blue 3×3 sprites; the right one slides left until it touches, then moves back):

```
t0 apart        b89b@(5,5)  b89b@(5,12)
t1 touching     be11@(5,5)                  <- one 3x6 blob, new name
t2 apart again  b89b@(5,5)  b89b@(5,12)     <- original name is back

changes_since t0 -> t1:  b89b became be11 @ (5,5);  b89b disappeared from (5,12)
changes_since t1 -> t2:  be11 became b89b @ (5,5);  b89b appeared @ (5,12)
```

So the change report is the weak spot: a slide-and-touch reads as "became" plus "disappeared". These are the roughly 23% of objects that touch a same-colour neighbour, which no single frame can separate. The fix I have planned is co-motion splitting: when part of a merged blob moves and part stays, split it and keep that split for the rest of the game.

One more thing your question surfaced: the true-size step runs on every frame, so on a nearly empty board it can pick a coarser grid between frames and rename everything. Locking the scale per game is next on my list.
