# ---------------------------------------------------------------------------------------------
# Change A (wmreason): carry world-model lines that the model writes in its REASONING.
#
# Verified defect (see kaggle/changeA/README.md): the shipped harness updates the carried world
# model only from the model's visible reply (tool_agent.py:1896,1930); reasoning is never parsed.
# On the v3 save run the visible reply carried labels on 50 of 402 turns; the reasoning carried
# them on 76, 66 of which the harness ignored.
#
# What this cell does, and nothing else:
#   after every model response, if the VISIBLE reply has no world-model labels, parse the
#   REASONING with the harness's own parser and write those fields into the carried world model,
#   each capped at WMREASON_FIELD_CAP characters (default 400). The visible reply still wins:
#   the harness applies it afterwards exactly as before. Any error leaves the response untouched.
# Kill switch: set env WMREASON=0 before this cell to disable (the cell then installs nothing).
# ---------------------------------------------------------------------------------------------
import os as _os
import inference.agent.tool_agent as _ta_wm

WMR_ON = _os.environ.get('WMREASON', '1').strip() not in ('0', '', 'false', 'False')
WMR_CAP = int(_os.environ.get('WMREASON_FIELD_CAP', '400'))
WMR_STATS = globals().get('WMR_STATS') or {'responses': 0, 'visible_labels': 0, 'reasoning_applied': 0, 'no_labels': 0,
             'fields_applied': 0, 'chars_applied': 0, 'errors': 0}

def _wmr_note(text):
    note = _ta_wm._extract_scientist_note(text or '')   # the parser installed now (F3's tolerant one in the 5.19 notebook)
    out = {}
    for key, val in note.items():
        if val:
            val = ' '.join(str(val).split())
            out[key] = val if len(val) <= WMR_CAP else val[:WMR_CAP].rstrip() + ' ...'
    return out

def _wmr_apply(agent, message):
    """Returns 'visible', 'reasoning' or 'none'. Mutates agent._summarized_knowledge only for 'reasoning'."""
    content = _ta_wm._normalize_message_content((message or {}).get('content', ''))
    if content and any(_ta_wm._extract_scientist_note(content).values()):
        return 'visible'
    note = _wmr_note(_ta_wm._extract_reasoning_text(message or {}))
    if not note:
        return 'none'
    for key, val in note.items():
        agent._summarized_knowledge[key] = val
    WMR_STATS['fields_applied'] += len(note); WMR_STATS['chars_applied'] += sum(len(v) for v in note.values())
    return 'reasoning'

if WMR_ON and not getattr(_ta_wm.ToolAgent._chat_completion, '_wmreason', False):
    _wmr_orig = _ta_wm.ToolAgent._chat_completion
    def _chat_completion(self, messages, *args, **kwargs):
        result = _wmr_orig(self, messages, *args, **kwargs)
        try:
            WMR_STATS['responses'] += 1
            kind = _wmr_apply(self, getattr(result, 'message', None))
            WMR_STATS[{'visible': 'visible_labels', 'reasoning': 'reasoning_applied', 'none': 'no_labels'}[kind]] += 1
            if WMR_STATS['responses'] % 100 == 0:
                print('ARC3_WMREASON_STATS', WMR_STATS, flush=True)
        except Exception:
            WMR_STATS['errors'] += 1
        return result
    _chat_completion._wmreason = True
    for _attr in ('__doc__', '__name__'):
        setattr(_chat_completion, _attr, getattr(_wmr_orig, _attr, None))
    _ta_wm.ToolAgent._chat_completion = _chat_completion

    # Self-test on a stub agent (no server needed): the three cases must behave as documented.
    class _Stub: pass
    _s = _Stub(); _s._summarized_knowledge = {'world_model': 'OLD'}
    assert _wmr_apply(_s, {'content': 'World model: from reply', 'reasoning': 'World model: from reasoning'}) == 'visible'
    assert _s._summarized_knowledge['world_model'] == 'OLD'          # the harness itself applies visible replies
    assert _wmr_apply(_s, {'content': '', 'reasoning': 'thinking...\nWorld model: A is a button\nPlan: press A'}) == 'reasoning'
    assert _s._summarized_knowledge['world_model'].startswith('A is a button')
    assert _wmr_apply(_s, {'content': '', 'reasoning': 'World model: ' + 'x ' * 2000}) == 'reasoning'
    assert len(_s._summarized_knowledge['world_model']) <= WMR_CAP + 4
    assert _wmr_apply(_s, {'content': 'no labels', 'reasoning': 'no labels either'}) == 'none'
    assert _ta_wm.ToolAgent._chat_completion._wmreason is True
    print(f'ARC3_WMREASON_READY cap={WMR_CAP} self_test=ok', flush=True)
else:
    print(f'ARC3_WMREASON_READY disabled={not WMR_ON} already_installed={getattr(_ta_wm.ToolAgent._chat_completion, "_wmreason", False)}', flush=True)
