import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class RepoContractTests(unittest.TestCase):
    def test_expected_modules_exist(self):
        for name in ('ingestion/jobs/lambda_function.py',
                     'ingestion/benchmarks/lambda_function.py',
                     'ingestion/fx/lambda_function.py',
                     'routing/router_lambda/lambda_function.py',
                     'processing/benchmarks/lambda_function.py',
                     'processing/fx/lambda_function.py',
                     'processing/jobs_glue/glue_job.py'):
            with self.subTest(name=name):
                self.assertTrue((ROOT / name).is_file())

    def test_env_not_committed(self):
        self.assertFalse((ROOT / '.env').exists())

if __name__ == '__main__':
    unittest.main()
