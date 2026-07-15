from src.config.settings import PROCESSED_DIR, REGIONAL_CENTERS, COLD_SNAP_DURATION_HOURS
import pandas as pd
import requests
import numpy as np
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("WeatherPull")

def pull_national_weather():
    logger.info("Pulling Dec 2022 weather data for national regional centers via Open-Meteo API...")
    
    start_date = "2022-12-01"
    end_date = "2022-12-14" # 14 days
    
    all_temps = []
    
    for city, (lat, lon) in REGIONAL_CENTERS.items():
        logger.info(f"Pulling weather for {city}...")
        url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={start_date}&end_date={end_date}&hourly=temperature_2m"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if 'hourly' in data and 'temperature_2m' in data['hourly']:
                all_temps.append(data['hourly']['temperature_2m'][:COLD_SNAP_DURATION_HOURS])
        except Exception as e:
            logger.error(f"Failed to pull weather data for {city}: {e}")
    
    if not all_temps:
        logger.error("No weather data retrieved. Creating synthetic fallback.")
        from src.config.settings import RANDOM_SEED
        np.random.seed(RANDOM_SEED)
        national_temps = np.linspace(2.0, -2.0, COLD_SNAP_DURATION_HOURS) + np.random.normal(0, 1, COLD_SNAP_DURATION_HOURS)
    else:
        # Average across all successful pulls
        # Ensure all arrays have the same length
        min_len = min(len(t) for t in all_temps)
        national_temps = np.mean([t[:min_len] for t in all_temps], axis=0)
    
    df = pd.DataFrame({
        'temp': national_temps
    })
    
    output_path = PROCESSED_DIR / "cold_snap_temps.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved national average weather data to {output_path}")
    logger.info(f"National Cold Snap Stats: Min={df['temp'].min():.1f}°C, Avg={df['temp'].mean():.1f}°C")

if __name__ == "__main__":
    pull_national_weather()
