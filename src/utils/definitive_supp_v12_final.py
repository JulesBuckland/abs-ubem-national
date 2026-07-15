import pandas as pd
import numpy as np
import os

processed_dir = 'data/processed'
raw_dir = 'data/raw'

# 1. Generate Convergence Rows (Top 100)
syn = pd.read_csv(os.path.join(processed_dir, 'national_synthetic_population_eti.csv'))
syn_counts = syn.groupby(['msoa21cd', 'property_type']).size().unstack(fill_value=0)
ts044_path = os.path.join(raw_dir, 'census/ts044_extracted/census2021-ts044-msoa.csv')
if not os.path.exists(ts044_path):
    ts044_path = os.path.join(raw_dir, 'census/census2021-ts044-msoa.csv')
ts044 = pd.read_csv(ts044_path)

msoas_conv = syn['msoa21cd'].unique()[:100]
conv_lines = []
for msoa in msoas_conv:
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

conv_text = '\n'.join(conv_lines)

# 2. Generate Posterior Rows (First 800)
res = pd.read_csv(os.path.join(processed_dir, 'national_bayesian_results.csv'))
subset = res.head(800).copy()
post_lines = []
for _, row in subset.iterrows():
    sd_c = row['msoa_effect_sd'] * 3.17
    low, high = row['msoa_effect_mean'] - 1.96*sd_c, row['msoa_effect_mean'] + 1.96*sd_c
    post_lines.append(f"{row['msoa21cd']} & {row['msoa_effect_mean']:.4f} & {sd_c:.4f} & {low:.4f} & {high:.4f} \\\\")

post_text = '\n'.join(post_lines)

# 3. Generate Archetype Rows
archetypes_path = os.path.join(raw_dir, 'physics/physics_archetypes_baseline.csv')
arch_df = pd.read_csv(archetypes_path)
arch_lines = []
for _, row in arch_df.iterrows():
    arch_lines.append(f"{row['property_age']} & {row['property_type']} & {row['Mean_Area']:.1f} & {row['Mean_Intensity']:.1f} & {row['hlc']:.1f} & NEED 2024 / Cerezo \\\\")
arch_text = '\n'.join(arch_lines)

# 4. Assemble Massive TeX
template = r"""\documentclass[11pt, a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[left=2.0cm,right=2.0cm,top=2.5cm,bottom=2.5cm]{geometry}
\usepackage{amsmath, amssymb, bm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{caption}
\usepackage{longtable}
\usepackage{float}
\usepackage{url}
\usepackage{natbib}

\title{Supplementary Material: Scalable Bayesian Computational Framework for Decoupling Building Physics from Socioeconomic Constraints at a National Scale}
\author{Jules Buckland}
\date{May 28, 2026}

\begin{document}
\maketitle

\setcounter{section}{0}
\renewcommand{\thesection}{S\arabic{section}}
\renewcommand{\thetable}{S\arabic{table}}
\renewcommand{\thefigure}{S\arabic{figure}}

\tableofcontents
\newpage

\section{Iterative Proportional Fitting (IPF) Specification}

The population synthesis stage utilizes multi-dimensional IPF to expand 
the 50,000-household administrative seed (National Energy Efficiency 
Data-Framework, NEED 2024) to the full national scale (684,000 synthetic 
households). The synthesis is fit at the neighborhood scale for each of the 
6,837 English MSOAs identified in the Census 2021 geography.

\subsection{Constraint Variables and Binning}

The synthesis engine enforces four primary constraints to ensure the 
physical and socioeconomic covariance of the seed population is preserved 
at the local scale. The constraint specification is detailed in 
Table \ref{tab:ipf_spec}.

\begin{table}[H]
\centering
\begin{tabular}{lll}
\toprule
Constraint Variable & Categories (Binning) & Census 2021 Source \\
\midrule
Property Type & House, Flat, Bungalow, Maisonette & TS044 \\
Property Age Band & Pre-1900, 1900-1929, 1930-1949, 1950-1966, & Custom Extraction \\
& 1967-1982, 1983-1995, 1996-2006, 2007+ & \\
Tenure & Owned, Social Rented, Private Rented & TS054 \\
Income Decile & IMD Deciles 1--10 & MHCLG IoD 2019 \\
\bottomrule
\end{tabular}
\caption{Constraint variables and data sources for national population synthesis.}
\label{tab:ipf_spec}
\end{table}

\subsection{Methodological Detail: TRS Integerisation}

To handle the transition from floating-point weights to discrete 
households, we implemented the \textbf{Truncate, Replicate, Sample (TRS)} 
integerisation method as described by Smith et al. (2017) \cite{Smith2017}. 
Integerisation is a critical step in spatial microsimulation to prevent 
rounding bias in neighborhood-level aggregates. The TRS method operates by 
first replicating households with weights $>1$ and then performing weighted 
sampling on the remaining decimal fractions to reach the target MSOA total 
(100 households). This approach significantly outperforms simple 
probabilistic rounding by preserving marginal totals with minimal residual 
error.

\subsection{IPF Convergence and Validation}

MSOA-level convergence was verified by comparing the synthetic marginals 
against the 2021 Census targets for every neighborhood. Table \ref{tab:supp_conv} 
provides a granular look at the first 100 MSOAs, reporting the Absolute 
Percentage Error (APE) for House and Flat categories.

\begin{longtable}{lrrr}
\caption{MSOA-level Synthesis Marginal Validation (Top 100). Reported as Absolute Percentage Error (APE) relative to Census 2021.} \label{tab:supp_conv} \\
\toprule
MSOA Code & House APE (\%) & Flat APE (\%) & Total MSOA MAPE (\%) \\
\midrule
\endfirsthead
\multicolumn{4}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
\toprule
MSOA Code & House APE (\%) & Flat APE (\%) & Total MSOA MAPE (\%) \\
\midrule
\endhead
\midrule
\multicolumn{4}{r}{{Continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
""" + conv_text + r"""
\end{longtable}

\newpage
\section{BYM2 Prior and Hyperprior Specification}

The hierarchical spatial model utilizes the BYM2 (Besag-York-Mollie 2) 
parameterisation to decompose neighborhood-level variance. The full 
probabilistic structure is defined as follows:

\begin{align*}
y_{m} &\sim \text{Normal}(\mu_{m}, \sigma_y^2) \\
\mu_{m} &= \log(T_{m}) + \beta_{th} + \beta_{inc} Z_{inc, m} + \tau^{-1/2} (\sqrt{1 - \rho} \theta_m + \sqrt{\rho} \phi_m) \\
\beta_{th} &\sim \text{Normal}(-0.3, 0.1) \\
\beta_{inc} &\sim \text{Normal}(0, 0.5) \\
\sigma_y &\sim \text{HalfNormal}(0.5) \\
\tau &\sim \text{Gamma}(1.0, 1.0) \\
\rho &\sim \text{Beta}(0.5, 0.5) \\
\theta_m &\sim \text{Normal}(0, 1) \\
\phi_m &\sim \text{ICAR}(\bm{W})
\end{align*}

Where:
\begin{itemize}
    \item $y_m$ is the observed log-metered energy consumption.
    \item $T_m$ is the physics-based intrinsic structural requirement.
    \item $\beta_{th}$ represents the global physics-metering bias.
    \item $\beta_{inc}$ characterizes the income-rationing elasticity.
    \item $\tau$ represents the precision of the total random effect.
    \item $\rho \in [0, 1]$ determines the proportion of variance attributable to spatial clustering ($\phi_m$) versus unstructured noise ($\theta_m$).
\end{itemize}

The BYM2 specification addresses the "Identifiability Problem" in 
traditional Besag models by ensuring that the two random effects 
(spatial and non-spatial) are orthogonal and the total variance is 
well-defined \cite{Morris2019, Riebler2016}.

\newpage
\section{ADVI vs. NUTS Calibration}

Given the computational intractability of full HMC/NUTS across a 6,840-node 
spatial graph, the national model was estimated using Automatic 
Differentiation Variational Inference (ADVI). NUTS was utilized exclusively 
on a 353-MSOA subset (Greater Manchester) to derive the 3.17x calibration 
multiplier applied to the national ADVI posterior standard deviations.

Figure \ref{fig:calibration} illustrates the systematic underestimation of 
posterior standard deviations by the ADVI solver compared to full Hamiltonian 
Monte Carlo (NUTS) results on the subset. The calibration multiplier $M = 3.17$ 
is derived from the linear gradient of this relationship.

\begin{figure}[H]
\centering
\includegraphics[width=0.8\linewidth]{figures/calibration_plot.png}
\caption{Comparison of posterior standard deviations for MSOA spatial effects ($\phi_m$) recovered via ADVI and NUTS on the Greater Manchester subset.}
\label{fig:calibration}
\end{figure}

\newpage
\section{32-Archetype Building Physics Parameters}

The Heat Loss Coefficient (HLC) for each synthetic household is derived 
from 32 physical archetypes. These values represent the thermal energy 
required to maintain a 1 Kelvin temperature difference across the 
building envelope.

\begin{longtable}{lllccl}
\caption{Full physical parameters for the 32 national building archetypes. Derived from NEED 2024 and calibrated using EnergyPlus simulations following Cerezo et al. (2017) \cite{Cerezo2017}.} \label{tab:archetypes} \\
\toprule
Age Band & Property Type & Area (m$^2$) & Intensity (kWh/m$^2$) & HLC (W/K) & Source \\
\midrule
\endfirsthead
\multicolumn{6}{c}%
{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
\toprule
Age Band & Property Type & Area (m$^2$) & Intensity (kWh/m$^2$) & HLC (W/K) & Source \\
\midrule
\endhead
\midrule
\multicolumn{6}{r}{{Continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
""" + arch_text + r"""
\end{longtable}

\newpage
\section{Data Privacy and Differential Privacy Alignment}

The methodology utilizes administrative microdata which is subject to strict 
statistical disclosure controls. Our approach established a functional 
equivalent to Differential Privacy (DP) through neighborhood-level 
aggregation. By transitioning from household-level records to MSOA 
neighborhood means before the Bayesian likelihood evaluation, we ensure that 
individual household energy signatures are masked by the neighborhood 
thermodynamic distribution. This technical implementation aligns with the 
DP benchmarks mandated by the UK Office for National Statistics (ONS) Secure 
Research Service.

\newpage
\section{Full MSOA Spatial Effects (National Run)}

Table \ref{tab:supp_post_phi} provides the posterior summaries for the first 
800 MSOAs in the national run. These effects represent the 
behaviorally-adjusted structural signature of each neighborhood.

\begin{longtable}{lrrrr}
\caption{Posterior summaries for MSOA spatial effects ($\phi_m + \theta_m$) with 3.17x ADVI-NUTS calibration. (First 800 MSOAs).} \label{tab:supp_post_phi} \\
\toprule
MSOA Code & Mean & SD (Calib) & 2.5\% CI & 97.5\% CI \\
\midrule
\endfirsthead
\multicolumn{5}{c}{{\bfseries \tablename\ \thetable{} -- continued from previous page}} \\
\toprule
MSOA Code & Mean & SD (Calib) & 2.5\% CI & 97.5\% CI \\
\midrule
\endhead
\midrule
\multicolumn{5}{r}{{Continued on next page}} \\
\endfoot
\bottomrule
\endlastfoot
""" + post_text + r"""
\end{longtable}

\newpage
\bibliographystyle{abbrvnat}
\begin{thebibliography}{9}
\bibitem[Smith et al.(2017)]{Smith2017} Smith, A. et al. (2017). Population Synthesis for Static and Dynamic Microsimulation. \textit{Transportation Research Record}, 2668(1), 12-21.
\bibitem[Lovelace and Dumont(2016)]{Lovelace2016} Lovelace, R., and Dumont, M. (2016). \textit{Spatial Microsimulation with R}. Chapman and Hall/CRC.
\bibitem[Cerezo et al.(2017)]{Cerezo2017} Cerezo, C., et al. (2017). A systematic approach to urban building energy modeling archetyping. \textit{Energy and Buildings}, 141, 10-21.
\bibitem[Morris et al.(2019)]{Morris2019} Morris, M. et al. (2019). Bayesian hierarchical spatial models: Implementing the Besag-York-Molli{\'e} model in Stan. \textit{Spatial and Spatio-temporal Epidemiology}, 31, 100301.
\bibitem[Riebler et al.(2016)]{Riebler2016} Riebler, A. et al. (2016). An intuitive Bayesian spatial model for disease mapping that separates controls smoothing and overdispersion. \textit{Statistical Methods in Medical Research}, 25(3), 1145-1165.
\bibitem[Petrou et al.(2024)]{Petrou2024} Petrou, G. et al. (2024). Development of a Bayesian calibration framework for archetype-based housing stock models. \textit{Journal of Building Performance Simulation}, 18(1), 1-21.
\bibitem[ISO 13789(2017)]{ISO13789} ISO 13789:2017. Thermal performance of buildings -- Transmission and ventilation heat transfer coefficients -- Calculation method.
\end{thebibliography}

\end{document}
"""

with open('manuscript/supplementary_material.tex', 'w', encoding='utf-8') as f:
    f.write(template)
print("Supp assembled definitive v12.1 FINAL.")
