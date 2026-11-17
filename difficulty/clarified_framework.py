"""Offline framework integration for the versioned clarified design metric."""
from .clarified_design_run import report as load_report
from .design.reporting import distribution, write_report


def build_report(packet):
    result=load_report(packet)
    keys=sorted({(t['dataset'],t['domain'],t['workflow_id'] or 'not_defined') for t in result['tasks']})
    result['workflows']={ '/'.join(key):distribution([t for t in result['tasks']
        if (t['dataset'],t['domain'],t['workflow_id'] or 'not_defined')==key]) for key in keys}
    result['weights']={k:.2 for k in ('workload','reasoning','tool_use','dependencies','information')}
    result['formula']='5 * sum(five integer dimension levels in [0,4])'
    result['calibration_status']='bounded_practical_checks_passed_not_independent_accuracy'
    return result


def evaluate(args):
    if not getattr(args,'design_clarified_packet',None):
        raise ValueError('Clarified source-only mode requires --design-clarified-packet')
    if (getattr(args,'design_packet',None) or getattr(args,'design_inventory',None) or
            getattr(args,'synthetic_designed_scores',None) or getattr(args,'synthetic_structural_features',None)):
        raise ValueError('Do not mix original packets, inventories or structural indices with a clarified packet')
    result=build_report(args.design_clarified_packet)
    write_report(result,args.output_dir)
    for dataset,value in result['datasets'].items():
        print(f"{dataset}: designed difficulty={value['mean']} ({value['mean_label']}), scored={value['n_scored']}/{value['n_total']}")
    return result
