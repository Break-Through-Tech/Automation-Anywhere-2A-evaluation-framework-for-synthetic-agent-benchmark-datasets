"""Check judge citations against execution evidence without repairing model output."""
import json
import re


def pointer_value(transcript, locator):
    if not locator.startswith('#/'):
        raise ValueError('Review evidence locators must start with #/ relative to the transcript')
    value = transcript
    try:
        for token in locator[2:].split('/'):
            token = token.replace('~1', '/').replace('~0', '~')
            if isinstance(value, list):
                if not re.fullmatch(r'0|[1-9][0-9]*', token):
                    raise ValueError('Array indexes must be nonnegative JSON pointer indexes')
                value = value[int(token)]
            else:
                value = value[token]
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise ValueError(f'Evidence locator does not resolve: {locator}') from exc
    return value


def check_evidence(judgment, transcript):
    for claim in [dict(evidence=judgment['task_evidence']), *judgment['milestones']]:
        for evidence in claim['evidence']:
            value = pointer_value(transcript, evidence['locator'])
            text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
            if evidence['excerpt'] not in text:
                # A whole structured value has multiple valid JSON serializations.
                # Ignore formatting whitespace, never whitespace inside strings,
                # omitted fields, changed values, array order, or paraphrases.
                if isinstance(value, (dict, list)):
                    try:
                        def unique_object(pairs):
                            result = {}
                            for key, item in pairs:
                                if key in result:
                                    raise ValueError('Duplicate evidence object key')
                                result[key] = item
                            return result
                        quoted = json.loads(evidence['excerpt'], object_pairs_hook=unique_object)
                        compact = lambda obj: json.dumps(obj, ensure_ascii=False, separators=(',', ':'), allow_nan=False)
                        if compact(quoted) == compact(value):
                            continue
                    except (ValueError, TypeError):
                        pass
                raise ValueError('Evidence excerpt is not present at its stated locator')
