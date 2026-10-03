"""Table 3: linear GEE, Mancl-DeRouen covariance, t(26), Holm(17).

For Gaussian variance, identity link and working independence the GEE
coefficient estimate is ordinary least squares. Inference below uses patient
clusters, NOT the independent-observation OLS covariance.
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import t

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'kappa_workbook_package'))
from kappa_analysis import build_long, QUESTIONS, RATERS


def fit_linear_gee(frame):
    y = frame['Accepted'].to_numpy(dtype=float)
    X = np.column_stack([np.ones(len(frame)),
                         (frame.Model == 'On-site trained model').astype(float),
                         (frame.Observer == 'MP').astype(float),
                         (frame.Observer == 'DR').astype(float)])
    groups = frame['Patient ID'].to_numpy()
    ids = np.unique(groups)
    if len(frame) != 180 or len(ids) != 30 or np.linalg.matrix_rank(X) != 4:
        raise ValueError('Expected 180 observations in 30 patient clusters and rank 4')
    bread = np.linalg.inv(X.T @ X)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    residual = y - X @ beta
    meat = np.zeros((4, 4))
    ordinary_meat = np.zeros((4, 4))
    conditions = []
    # MD: corrected residual r_i* = (I - H_ii)^(-1) r_i.
    # With working variance phi*I, phi cancels from the sandwich covariance.
    for patient in ids:
        idx = groups == patient
        Xi, ri = X[idx], residual[idx]
        adjustment = np.eye(len(ri)) - Xi @ bread @ Xi.T
        conditions.append(np.linalg.cond(adjustment))
        ui = Xi.T @ np.linalg.solve(adjustment, ri)
        meat += np.outer(ui, ui)
        uncorrected = Xi.T @ ri
        ordinary_meat += np.outer(uncorrected, uncorrected)
    covariance = bread @ meat @ bread
    se = float(np.sqrt(covariance[1, 1]))
    if not np.isfinite(se) or se <= 0:
        raise ValueError('Model effect has zero/nonfinite variance; inference unavailable')
    df = len(ids) - X.shape[1]
    critical = t.ppf(.975, df)
    return dict(difference_pp=float(beta[1]*100), se_pp=se*100,
                ci_low_pp=float((beta[1]-critical*se)*100),
                ci_high_pp=float((beta[1]+critical*se)*100),
                p_unadjusted=float(2*t.sf(abs(beta[1]/se), df)), df=df,
                clusters=len(ids), paired_assessments=len(frame)//2,
                design_rank=int(np.linalg.matrix_rank(X)),
                design_condition=float(np.linalg.cond(X)),
                max_MD_condition=float(max(conditions)),
                ordinary_sandwich_se_pp=float(np.sqrt((bread@ordinary_meat@bread)[1,1])*100),
                fitted_min=float((X@beta).min()), fitted_max=float((X@beta).max()))


def holm(p):
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    result = np.empty(len(p))
    result[order] = np.minimum(1, np.maximum.accumulate(p[order] * np.arange(len(p), 0, -1)))
    return result


def analyze(path):
    wide = build_long(path)
    long = wide.melt(id_vars=['Patient ID','Model','Question'], value_vars=RATERS,
                     var_name='Observer', value_name='Accepted')
    rows, descriptive = [], []
    for question in QUESTIONS:
        sub = long[long.Question == question]
        pairs = sub.pivot(index=['Patient ID','Observer'], columns='Model', values='Accepted')
        if pairs.shape != (90, 2) or pairs.isna().any().any():
            raise ValueError(f'{question}: incomplete patient-observer pairing')
        result = {'Sub-question': question, **fit_linear_gee(sub)}
        for model, label in [('Pre-built model','pre'),('On-site trained model','on')]:
            responses = sub[sub.Model == model].Accepted
            result[label+'_n'] = int(responses.sum())
            result[label+'_N'] = len(responses)
            result[label+'_percent'] = float(responses.mean()*100)
            for observer in RATERS:
                ratings = sub[(sub.Model == model)&(sub.Observer == observer)].Accepted
                descriptive.append({'Sub-question':question,'Model':model,'Observer':observer,
                                    'n':int(ratings.sum()),'N':len(ratings),'Acceptance (%)':float(ratings.mean()*100)})
        if not np.isclose(result['difference_pp'],result['on_percent']-result['pre_percent']):
            raise ValueError('Balanced-design model coefficient does not match rate difference')
        rows.append(result)
    results = pd.DataFrame(rows)
    results['p_holm'] = holm(results.p_unadjusted)
    return results, pd.DataFrame(descriptive)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output-dir', type=Path, default=Path('gee_results'))
    args = parser.parse_args()
    results, descriptive = analyze(args.input)
    args.output_dir.mkdir(parents=True,exist_ok=True)
    results.to_csv(args.output_dir/'GEE_subquestion_results.csv',index=False)
    descriptive.to_csv(args.output_dir/'Acceptance_by_observer.csv',index=False)
    metadata = {'method':'Gaussian identity-link GEE with independence working correlation',
                'covariance':'Mancl-DeRouen bias-corrected sandwich',
                'coefficients':['intercept','on-site model','MP','DR'],
                'cluster':'patient','df':26,'holm_family':17,
                'CI_multiplicity_adjusted':False,
                'raw_input_modified':False,
                'note':'All individual responses retained. No patient-level acceptance aggregation. Observer rates are descriptive.'}
    (args.output_dir/'analysis_metadata.json').write_text(json.dumps(metadata,indent=2))
    print(results[['Sub-question','pre_percent','on_percent','difference_pp','ci_low_pp','ci_high_pp','p_holm']].to_string(index=False))


if __name__ == '__main__':
    main()
