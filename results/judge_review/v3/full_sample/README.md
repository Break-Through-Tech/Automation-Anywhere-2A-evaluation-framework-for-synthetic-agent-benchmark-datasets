# Initial validation snapshot

These files preserve the initial result: sixteen responses received, fifteen
accepted and R10 rejected. R10's rejection was subsequently traced to JSON
serialization whitespace and revalidated offline after a tested validator fix.
The current result is in `../full_sample_revalidated/`; use that version for
the development-sample comparison. The initial snapshot is retained for audit.
