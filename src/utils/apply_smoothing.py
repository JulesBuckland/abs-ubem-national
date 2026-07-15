import re

with open('src/visualization/visuals_generator.py', 'r', encoding='utf-8') as f:
    code = f.read()

smooth_code = """
        # Apply the 3.17x multiplier to the SD
        msoa_map_res['calibrated_sd'] = msoa_map_res['msoa_effect_sd'] * 3.17
        
        # SPATIAL SMOOTHING: Apply spatial lag to smooth out regional block artifacts
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
"""

old_code = """
        # Apply the 3.17x multiplier to the SD
        msoa_map_res['calibrated_sd'] = msoa_map_res['msoa_effect_sd'] * 3.17
        
        # INCREASE CONTRAST: Cap at 95th percentile and use high-contrast colormap
        vmax_sd = msoa_map_res['calibrated_sd'].quantile(0.95)
        
        fig, ax = plt.subplots(1, 1, figsize=(12, 16))
        msoa_map_res.plot(column='calibrated_sd', cmap='magma', legend=True,
"""

code = code.replace(old_code.strip(), smooth_code.strip())

with open('src/visualization/visuals_generator.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Updated 04_generate_visuals.py for Spatial Smoothing.')
