"""Check the revised Table 3 against the user's supplied S1 workbook."""
import argparse
import numpy as np
from gee_acceptance_analysis import analyze, holm

EXPECTED_COUNTS = [(14,80),(8,62),(27,72),(17,66),(20,62),(59,87),
                   (58,76),(24,57),(55,77),(16,85),(15,77),(18,78),
                   (13,56),(87,88),(38,83),(81,87),(69,88)]
EXPECTED_CI = [(58.6,88.1),(44.9,75.1),(35.5,64.5),(39.0,69.9),
               (33.1,60.3),(16.6,45.7),(2.4,37.6),(22.4,51.0),
               (11.5,37.4),(63.7,89.7),(52.2,85.6),(54.2,79.2),
               (28.1,67.5),(-5.1,7.3),(34.8,65.2),(-1.8,15.1),(12.6,29.6)]

def verify(path):
    results, rates = analyze(path)
    assert list(zip(results.pre_n, results.on_n)) == EXPECTED_COUNTS
    assert list(zip(results.ci_low_pp.round(1),results.ci_high_pp.round(1))) == EXPECTED_CI
    adjusted = results.set_index('Sub-question').p_holm
    for q, expected in [('Q4-2',.081),('Q4-4',.002),('Q6-1',.717),('Q6-3',.234)]:
        assert round(adjusted[q],3) == expected
    assert all(v < .001 for q,v in adjusted.items() if q not in ['Q4-2','Q4-4','Q6-1','Q6-3'])
    assert (results.p_holm < .05).sum() == 14
    assert (results.df == 26).all() and (rates.N == 30).all()
    np.testing.assert_allclose(holm([.03,.001,.2]),[.06,.003,.2])
    print('PASS: all 17 counts, confidence intervals and adjusted p-values reproduce Table 3; 14/17 significant.')

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('--input',required=True)
    verify(p.parse_args().input)
