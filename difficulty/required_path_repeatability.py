"""Offline evaluation of the frozen paired prompt study; no API calls."""
from statistics import mean

ROLES = {'sim_exit', 'airline_no_target_exit', 'retail_no_target_exit',
         'fraud_package_exit', 'simple_control', 'complex_control'}
ARMS = ('original', 'clarified')


def summarize(observations, thresholds):
    """Keep arms separate and never replace missing/error observations with zero."""
    seen, groups, unavailable = set(), {}, []
    for item in observations:
        role, arm, repeat = item['role'], item['arm'], item['repeat']
        if role not in ROLES or arm not in ARMS or type(repeat) is not int or repeat not in range(3):
            raise ValueError('Unexpected study observation')
        identity = (role, arm, repeat)
        if identity in seen:
            raise ValueError('Duplicate observation')
        seen.add(identity)
        score = item.get('score')
        if item.get('status') != 'scored' or type(score) not in (int, float) or not 0 <= score <= 100:
            unavailable.append(identity)
        else:
            groups.setdefault((role, arm), []).append(score)
    expected = {(r, a, n) for r in ROLES for a in ARMS for n in range(3)}
    missing = sorted(expected-seen)
    complete = not missing and not unavailable
    cases = []
    for role in sorted(ROLES):
        arms = {}
        for arm in ARMS:
            values = groups.get((role, arm), [])
            usable = len(values) == 3
            arms[arm] = {'usable_judgments': len(values), 'scores': values,
                         'mean': mean(values) if usable else None,
                         'range': max(values)-min(values) if usable else None}
        cases.append({'role': role, 'arms': arms,
            'mean_shift': arms['clarified']['mean']-arms['original']['mean']
                if all(a['mean'] is not None for a in arms.values()) else None})
    arms_summary = {}
    for arm in ARMS:
        ranges = [c['arms'][arm]['range'] for c in cases]
        ready = all(v is not None for v in ranges)
        gap = (next(c for c in cases if c['role']=='complex_control')['arms'][arm]['mean'] -
               next(c for c in cases if c['role']=='simple_control')['arms'][arm]['mean']) if ready else None
        arms_summary[arm] = {'max_range': max(ranges) if ready else None,
            'mean_range': mean(ranges) if ready else None, 'complexity_gap': gap,
            'repeatability_pass': (max(ranges) <= thresholds['max_repeat_range'] and
                mean(ranges) <= thresholds['max_mean_repeat_range']) if ready else None,
            'control_gap_pass': gap >= thresholds['min_authored_complexity_gap'] if ready else None}
    review = [c['role'] for c in cases if c['role'] in {'airline_no_target_exit','retail_no_target_exit'}
              and c['mean_shift'] is not None and abs(c['mean_shift']) > thresholds['non_target_mean_shift_review_threshold']]
    candidate = arms_summary['clarified']
    return {'complete': complete, 'missing': missing, 'unusable': unavailable,
        'cases': cases, 'arms': arms_summary, 'non_target_shift_review': review,
        'numeric_candidate_gate_pass': bool(complete and candidate['repeatability_pass'] and candidate['control_gap_pass']),
        'semantic_review_still_required': True, 'independent_validation': False,
        'dataset_scores_changed': False, 'automatic_adoption': False}
