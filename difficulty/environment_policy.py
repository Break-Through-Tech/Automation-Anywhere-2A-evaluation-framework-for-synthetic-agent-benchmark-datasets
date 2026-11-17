"""Validate versioned outcome, blocker, behavior, and eligibility findings."""
import json

if __package__:
    from .judge_evidence import check_evidence
else:
    from judge_evidence import check_evidence


LEGACY_POLICY = "provisional_outcome_v0.2"
CURRENT_POLICY = "provisional_outcome_v0.3"


def validate_environment_assessment(raw, judgment, transcript, policy_version=LEGACY_POLICY):
    # Default preserves old recorded runners; the current judge passes v0.3 explicitly.
    if policy_version not in {LEGACY_POLICY, CURRENT_POLICY}:
        raise ValueError("Unsupported environmental policy version")
    environment = raw.get('environment_assessment')
    recognition = raw.get('blocker_recognition')
    specifications = [
        ('environment_assessment', environment, {'supported_blocker', 'suspected_blocker', 'not_established'}),
        ('blocker_recognition', recognition, {'supported_positive', 'unsupported_claim', 'not_established'}),
    ]
    for name, finding, statuses in specifications:
        if not isinstance(finding, dict) or finding.get('status') not in statuses:
            raise ValueError(f'{name} must declare a supported status')
        if not isinstance(finding.get('rationale'), str) or not finding['rationale'].strip():
            raise ValueError(f'{name} requires a rationale')
        evidence = finding.get('evidence')
        if not isinstance(evidence, list):
            raise ValueError(f'{name} evidence must be a list')
        if finding['status'] != 'not_established' and not evidence:
            raise ValueError(f'{name} claims require evidence')
        for item in evidence:
            if not isinstance(item, dict) or not all(isinstance(item.get(k), str) and item[k].strip()
                                                    for k in ('locator', 'excerpt')):
                raise ValueError(f'{name} evidence needs locator and excerpt')
        check_evidence({'task_evidence': evidence, 'milestones': []}, transcript)
    prevents = environment.get('prevents_required_execution')
    if type(prevents) is not bool:
        raise ValueError('Environment must declare prevents_required_execution as boolean')
    if environment['status'] == 'not_established' and prevents:
        raise ValueError('Unestablished blocker cannot assert prevented execution')
    blocked = environment['status'] == 'supported_blocker' and prevents
    if blocked and policy_version == LEGACY_POLICY and judgment['task_judgment'] != 'unverifiable':
        raise ValueError('A supported blocker preventing execution requires an unverifiable outcome')
    if blocked and policy_version == CURRENT_POLICY and judgment['task_judgment'] == 'met':
        raise ValueError('A preventing blocker cannot coexist with a met outcome')
    if recognition['status'] == 'supported_positive' and not blocked:
        raise ValueError('Positive blocker recognition requires a supported execution blocker')
    eligible = raw.get('difficulty_eligible')
    reason = raw.get('difficulty_exclusion_reason')
    if type(eligible) is not bool or not isinstance(reason, str):
        raise ValueError('Difficulty eligibility must be boolean with an exclusion-reason string')
    if eligible and (blocked or judgment['task_judgment'] == 'unverifiable'
                     or environment['status'] == 'suspected_blocker'):
        raise ValueError('Blocked, unresolved, or unverifiable attempts are not difficulty eligible')
    if not eligible and not reason.strip():
        raise ValueError('Excluded attempts require an explicit exclusion reason')
    if eligible and reason.strip():
        raise ValueError('Eligible attempts cannot declare an exclusion reason')
    return {'environment_assessment_json': json.dumps(environment, ensure_ascii=False),
            'blocker_recognition_json': json.dumps(recognition, ensure_ascii=False),
            'environment_blocked': int(blocked), 'blocker_recognition_status': recognition['status'],
            'difficulty_eligible': int(eligible), 'difficulty_exclusion_reason': reason}
