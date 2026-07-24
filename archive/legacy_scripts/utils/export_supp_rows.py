import pandas as pd
import numpy as np
import os

processed_dir = 'data/processed'
raw_dir = 'data/raw'

# 1. Generate Convergence Table (Top 100)
syn = pd.read_csv(os.path.join(processed_dir, 'national_synthetic_population_eti.csv'))
syn_counts = syn.groupby(['msoa21cd', 'property_type']).size().unstack(fill_value=0)
ts044_path = os.path.join(raw_dir, 'census/ts044_extracted/census2021-ts044-msoa.csv')
if not os.path.exists(ts044_path):
    ts044_path = os.path.join(raw_dir, 'census/census2021-ts044-msoa.csv')
ts044 = pd.read_csv(ts044_path)

msoas = syn['msoa21cd'].unique()[:100]
conv_lines = []
for msoa in msoas:
    if msoa not in ts044['geography code'].values: continue
    target = ts044[ts044['geography code'] == msoa].iloc[0]
    t_house = target['Accommodation type: Detached'] + target['Accommodation type: Semi-detached'] + target['Accommodation type: Terraced']
    t_flat = target['Accommodation type: In a purpose-built block of flats or tenement'] + target['Accommodation type: Part of a converted or shared house, including bedsits']
    total = t_house + t_flat + target['Accommodation type: A caravan or other mobile or temporary structure']
    if total == 0: continue
    t_house_p, t_flat_p = (t_house/total)*100, (t_flat/total)*100
    s_house, s_flat = syn_counts.loc[msoa, 'House'] if 'House' in syn_counts.columns else 0, syn_counts.loc[msoa, 'Flat'] if 'Flat' in syn_counts.columns else 0
    ape_h, ape_f = abs(t_house_p - s_house), abs(t_flat_p - s_flat)
    conv_lines.append(f"{msoa} & {ape_h:.4f} & {ape_f:.4f} & {(ape_h+ape_f)/2:.4f} \\\\")

with open(os.path.join(processed_dir, 'supp_conv_rows.tex'), 'w') as f:
    f.write('\n'.join(conv_lines))

# 2. Generate Posterior Table (First 200)
res = pd.read_csv(os.path.join(processed_dir, 'national_bayesian_results.csv'))
subset = res.head(200).copy()
post_lines = []
for _, row in subset.iterrows():
    sd_c = row['msoa_effect_sd'] * 3.17
    low, high = row['msoa_effect_mean'] - 1.96*sd_c, row['msoa_effect_mean'] + 1.96*sd_c
    post_lines.append(f"{row['msoa21cd']} & {row['msoa_effect_mean']:.4f} & {sd_c:.4f} & {low:.4f} & {high:.4f} \\\\")

with open(os.path.join(processed_dir, 'supp_post_rows.tex'), 'w') as f:
    f.write('\n'.join(post_lines))
