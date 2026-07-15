import pandas as pd
res = pd.read_csv('data/processed/national_bayesian_results.csv')
subset = res.iloc[200:1000].copy() # Rows 200 to 1000
post_lines = []
for _, row in subset.iterrows():
    sd_c = row['msoa_effect_sd'] * 3.17
    low, high = row['msoa_effect_mean'] - 1.96*sd_c, row['msoa_effect_mean'] + 1.96*sd_c
    post_lines.append(f"{row['msoa21cd']} & {row['msoa_effect_mean']:.4f} & {sd_c:.4f} & {low:.4f} & {high:.4f} \\\\")

with open('data/processed/supp_post_rows_extra.tex', 'w') as f:
    f.write('\n'.join(post_lines))
