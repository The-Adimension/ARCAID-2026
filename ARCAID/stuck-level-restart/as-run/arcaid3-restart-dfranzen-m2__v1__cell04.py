%%writefile /kaggle/restart.patch
diff --git a/ARC3-Inference/inference/agent/tool_agent.py b/ARC3-Inference/inference/agent/tool_agent.py
index 84a9cdd..3e926c5 100644
--- a/ARC3-Inference/inference/agent/tool_agent.py
+++ b/ARC3-Inference/inference/agent/tool_agent.py
@@ -995,6 +995,30 @@ def _summary_interval_tokens() -> int:
     return max(0, _get_env_int("ARC3_SUMMARY_INTERVAL_TOKENS", 0))
 
 
+def _stuck_restart_tokens() -> int:
+    """Generated tokens on one level after which that level's conversation is cleared, once. 0 disables.
+
+    A level attempt still open at 100K tokens finished by 140K only 14.6% of the
+    time in a 4-pass run, while 40 of its 67 unfinished attempts were on levels
+    another pass completed, typically with half the tokens. The model's first
+    hypothesis on a level is the variance, so a stuck attempt is given a fresh
+    context (the board stays where it is) instead of more tokens in the old one.
+    """
+    return max(0, _get_env_int("ARC3_STUCK_RESTART_TOKENS", 0))
+
+
+def _stuck_restart_log(record: dict[str, Any]) -> None:
+    """Append one restart event to ARC3_STUCK_RESTART_LOG (JSON lines), if set."""
+    path = os.environ.get("ARC3_STUCK_RESTART_LOG", "").strip()
+    if not path:
+        return
+    try:
+        with open(path, "a", encoding="utf-8") as fh:
+            fh.write(json.dumps(record) + "\n")
+    except OSError as exc:
+        log.warning("stuck_level_restart: cannot write %s: %s", path, exc)
+
+
 def _drain_stop_at_summaries() -> bool:
     """Whether the drain may stop early on a summary.
 
@@ -3860,6 +3884,15 @@ class ToolAgent:
                         _pace_reference_tokens(completed_level),
                     )
                     self._pace_last_completed_level = completed_level
+            restarted = getattr(self, "_stuck_restarts", None) or {}
+            completed = max(1, int(summary.get("level") or 2) - 1)
+            if completed in restarted:
+                event = dict(restarted[completed], event="completed_after_restart",
+                             tokens_after=self._session_generated_tokens - self._tokens_at_level_start,
+                             actions_total=_priority_action_count(summary) - self._actions_at_level_start)
+                log.warning("stuck_level_restart: level %d completed after restart (%d more tokens)",
+                            completed, event["tokens_after"])
+                _stuck_restart_log(event)
             self._actions_at_level_start = _priority_action_count(summary)
             self._tokens_at_level_start = self._session_generated_tokens
         if summary.get("level_transition") and _persistent_functions_scope() == "levelup":
@@ -6369,6 +6402,54 @@ class ToolAgent:
             log.warning("priority: total level count unavailable or invalid; using 10")
         return 10
 
+    def _maybe_restart_stuck_level(self, state_path: Path, append_transcript) -> str:
+        """Clear this level's conversation once it has used ARC3_STUCK_RESTART_TOKENS.
+
+        Called at the start of a fresh turn (never on a yield resumption), where
+        nothing is in flight. At most once per level. The system prompt, the
+        retained functions and the board are kept; the level's messages go. The
+        level is re-priced as a fresh attempt, and the dropped prefix is flagged
+        to the scheduler as a trim. Returns the line to put before this turn's
+        prompt, or "" when nothing was cleared.
+        """
+        limit = _stuck_restart_tokens()
+        if limit <= 0 or getattr(self, "_resume_after_yield", False):
+            return ""
+        summary = self._last_step_summary or {}
+        level = int(summary.get("level") or 1)
+        restarted = getattr(self, "_stuck_restarts", None)
+        if restarted is None:
+            restarted = self._stuck_restarts = {}
+        tokens = self._session_generated_tokens - getattr(self, "_tokens_at_level_start", 0)
+        if level in restarted or tokens < limit or not self._history_messages:
+            return ""
+        actions = max(0, _priority_action_count(summary) - self._actions_at_level_start)
+        event = {
+            "event": "restart", "state_path": str(state_path), "slot": self._diag_name,
+            "level": level, "tokens_before": tokens, "actions_before": actions,
+            "messages_dropped": len(self._history_messages),
+            "elapsed_s": getattr(self, "_game_elapsed_seconds", None),
+        }
+        restarted[level] = event
+        self._history_messages = []
+        self._tokens_at_level_start = self._session_generated_tokens
+        self._note_history_evicted()
+        log.warning(
+            "stuck_level_restart: level %d after %d tokens and %d actions; %d messages dropped",
+            level, tokens, actions, event["messages_dropped"],
+        )
+        append_transcript(
+            "ANALYZER STATUS",
+            f"stuck_level_restart: level={level} tokens={tokens} actions={actions} "
+            f"messages_dropped={event['messages_dropped']}",
+        )
+        _stuck_restart_log(event)
+        return (
+            f"Your earlier conversation on this level was cleared after {actions} actions "
+            "without completing it. The board below is the level's current state, not its "
+            "starting state. Your retained functions are still available."
+        )
+
     def _maybe_handover(self) -> None:
         """Re-price this game, and yield the slot if a gate is running.
 
@@ -6612,6 +6693,9 @@ class ToolAgent:
 
         append_transcript("SYSTEM PROMPT", self._system_prompt)
 
+        restart_note = self._maybe_restart_stuck_level(state_path, append_transcript)
+        if restart_note:
+            user_prompt = restart_note + "\n\n" + user_prompt
         previous_history_messages = list(self._history_messages)
         # Mirrors the history snapshot: a turn abandoned on a request failure is
         # rolled back, and the per-game token allowance has to roll back with it
