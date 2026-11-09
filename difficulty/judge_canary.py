"""Conservative spend guard for sequential paid judge diagnostics."""


def stop_reason(checks, max_attempts=3):
    if checks and checks[-1].get('status') != 'accepted':
        return 'Stop after a validation or API failure and diagnose before spending more.'
    if checks and checks[-1].get('expected_judgment') is not None and checks[-1].get('task_judgment') != checks[-1]['expected_judgment']:
        return 'Diagnostic control label mismatch: stop and inspect the evidence before another paid request.'
    if len(checks) >= 2 and all(c.get('task_judgment') in {'unmet', 'unverifiable'} for c in checks[-2:]):
        return 'Two consecutive non-success judgments: stop and diagnose; this does not prove agent failure.'
    if len(checks) >= max_attempts:
        return 'Small-test request limit reached; no automatic expansion.'
    return None
