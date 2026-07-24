import re

with open('src/visualization/visuals_generator.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Remove libpysal spatial smoothing and vmax capping
old_map_code = """        # SPATIAL SMOOTHING: Apply spatial lag to smooth out regional block artifacts
        try:
            import libpysal
            # Create Queen contiguity weights
            w = libpysal.weights.Queen.from_dataframe(msoa_map_res, use_index=False)
            w.transform = 'r' # Row-standardized
            # Apply spatial lag (average of neighbors)
            msoa_map_res['calibrated_sd_smoothed'] = libpysal.weights.lag_spatial(w, msoa_map_res['calibrated_sd'])
            plot_col = 'calibrated_sd_smoothed'
            logger.info('Applied spatial smoothing to Figure 3.')
        except Exception as e:
            logger.warning(f'Smoothing failed, using raw: {e}')
            plot_col = 'calibrated_sd'
        
        # INCREASE CONTRAST: Cap at 95th percentile and use high-contrast colormap
        vmax_sd = msoa_map_res[plot_col].quantile(0.95)
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 16))
        msoa_map_res.plot(column=plot_col, cmap='magma', legend=True,
                         legend_kwds={'label': "Calibrated Posterior Standard Deviation (3.17x multiplier)", 'orientation': "vertical", 'shrink': 0.6},
                         ax=ax, edgecolor='none', vmin=0, vmax=vmax_sd)"""

new_map_code = """        plot_col = 'calibrated_sd'
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 16))
        msoa_map_res.plot(column=plot_col, cmap='magma', legend=True,
                         legend_kwds={'label': "Calibrated Posterior Standard Deviation (3.17x multiplier)", 'orientation': "vertical", 'shrink': 0.6},
                         ax=ax, edgecolor='none')"""

code = code.replace(old_map_code, new_map_code)

# 2. Remove log bins from hexbin
old_hexbin = """        hb = plt.hexbin(
            data['theoretical_gas_kwh'],
            data['empirical_thermal_index'],
            gridsize=50,
            cmap='magma_r',
            bins='log'
        )
        cb = plt.colorbar(hb, label='log10(N MSOAs)')"""

new_hexbin = """        hb = plt.hexbin(
            data['theoretical_gas_kwh'],
            data['empirical_thermal_index'],
            gridsize=50,
            cmap='magma_r'
        )
        cb = plt.colorbar(hb, label='N MSOAs')"""

code = code.replace(old_hexbin, new_hexbin)

with open('src/visualization/visuals_generator.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Visuals script reverted to authentic data representation.')
