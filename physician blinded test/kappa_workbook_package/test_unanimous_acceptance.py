import unittest
import pandas as pd
from kappa_analysis import question_metrics
class Definitions(unittest.TestCase):
    def test_distinct_endpoints(self):
        frame=pd.DataFrame({"Model":["Pre-built model"]*4,"Question":["Q3-1"]*4,"RO":[1,0,1,1],"MP":[1,0,0,1],"DR":[1,0,0,0]})
        r=question_metrics(frame)[0]
        self.assertEqual(r["Unanimous acceptance n"],1)
        self.assertEqual(r["Unanimous acceptance"],.25)
        self.assertEqual(r["Acceptance all ratings"],.5)
        self.assertEqual(r["Complete agreement"],.5)
if __name__=="__main__": unittest.main()
