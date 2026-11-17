from argparse import Namespace
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from difficulty.clarified_framework import evaluate


class ClarifiedFrameworkTests(unittest.TestCase):
    def test_rejects_mixed_protocol_inputs(self):
        args=Namespace(design_clarified_packet=Path('new'),design_packet=[Path('old')],output_dir=Path('unused'))
        with self.assertRaisesRegex(ValueError,'mix'):evaluate(args)

    def test_offline_path_writes_scores_without_an_api_client(self):
        stub={'datasets':{'synthetic':{'mean':60,'mean_label':'complete_inventory_mean','n_scored':1,'n_total':1}},'tasks':[]}
        with tempfile.TemporaryDirectory() as temp:
            args=Namespace(design_clarified_packet=Path('frozen'),output_dir=Path(temp)/'out')
            with patch('difficulty.clarified_framework.build_report',return_value=stub), patch('difficulty.clarified_framework.write_report') as write, patch('openai.OpenAI',side_effect=AssertionError('No API')):
                self.assertIs(evaluate(args),stub)
                write.assert_called_once_with(stub,args.output_dir)


if __name__=='__main__':unittest.main()
