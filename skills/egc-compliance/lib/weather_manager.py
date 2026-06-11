"""
WeatherManager - manages EnergyPlus Weather (EPW) files.

This utility maps climate zones to representative weather stations and
downloads/caches EPW files for energy modeling.
"""

import os


class WeatherManager:
    """
    Manages EnergyPlus Weather (EPW) files for energy modeling.

    Maps climate zones to representative weather stations and handles
    downloading and caching of EPW files.
    """

    # Climate zone to weather station mapping
    # Based on ASHRAE 169-2013 climate zones
    CLIMATE_ZONE_WEATHER = {
        '1A': 'USA_FL_Miami.Intl.AP.722020',
        '2A': 'USA_TX_Houston-Bush.Intercontinental.AP.722430',
        '2B': 'USA_AZ_Phoenix-Sky.Harbor.Intl.AP.722780',
        '3A': 'USA_GA_Atlanta-Hartsfield-Jackson.Intl.AP.722190',
        '3B': 'USA_NV_Las.Vegas-McCarran.Intl.AP.723860',
        '3C': 'USA_CA_San.Francisco.Intl.AP.724940',
        '4A': 'USA_MD_Baltimore-Washington.Intl.AP.724060',
        '4B': 'USA_NM_Albuquerque.Intl.Sunport.723650',
        '4C': 'USA_WA_Seattle-Tacoma.Intl.AP.727930',
        '5A': 'USA_IL_Chicago-OHare.Intl.AP.725300',
        '5B': 'USA_CO_Denver.Intl.AP.725650',
        '5C': 'USA_WA_Port.Angeles-William.R.Fairchild.Intl.AP.727885',
        '6A': 'USA_MN_Minneapolis-St.Paul.Intl.AP.726580',
        '6B': 'USA_MT_Helena.Rgnl.AP.727720',
        '7': 'USA_MN_Duluth.Intl.AP.727450',
        '8': 'USA_AK_Fairbanks.Intl.AP.702610',
    }

    def __init__(self, cache_dir: str = None):
        """
        Initialize WeatherManager.

        Args:
            cache_dir: Directory to cache downloaded EPW files.
                       Defaults to ~/.audette/weather if not specified.
        """
        if cache_dir is None:
            cache_dir = os.path.expanduser('~/.audette/weather')
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_weather_file(self, climate_zone: str, custom_epw_path: str = None) -> str:
        """
        Get EPW file for a climate zone, downloading if necessary.

        Args:
            climate_zone: Climate zone code (e.g., '5A', '3C')
            custom_epw_path: Optional path to custom EPW file

        Returns:
            Path to the EPW file

        Raises:
            ValueError: If climate zone is not supported or EPW file not found
        """
        # If custom EPW provided, validate and return it
        if custom_epw_path:
            if os.path.exists(custom_epw_path):
                return custom_epw_path
            else:
                raise ValueError(f"Custom EPW file not found: {custom_epw_path}")

        if climate_zone not in self.CLIMATE_ZONE_WEATHER:
            raise ValueError(
                f"Unknown climate zone: {climate_zone}. "
                f"Supported zones: {', '.join(sorted(self.CLIMATE_ZONE_WEATHER.keys()))}"
            )

        weather_station = self.CLIMATE_ZONE_WEATHER[climate_zone]
        epw_filename = f"{weather_station}.epw"

        # FIX Bug 8: Check bundled data directory first
        bundled_path = os.path.join(
            os.path.dirname(__file__),
            '..',
            'data',
            'weather',
            epw_filename
        )
        if os.path.exists(bundled_path):
            return bundled_path

        # Check cache directory
        epw_path = os.path.join(self.cache_dir, epw_filename)
        if os.path.exists(epw_path):
            return epw_path

        # Otherwise download it
        self._download_weather_file(weather_station, epw_path)
        return epw_path

    def _download_weather_file(self, weather_station: str, epw_path: str):
        """
        Download weather file for a station from EnergyPlus.net.

        FIX Bug 8: Download actual EPW files from DOE/NREL repository.

        Args:
            weather_station: Weather station identifier (e.g., USA_IL_Chicago-OHare.Intl.AP.725300)
            epw_path: Path to save the EPW file

        Raises:
            RuntimeError: If download fails
        """
        import urllib.request
        import urllib.error
        import zipfile
        import tempfile

        # EnergyPlus weather data is hosted on GitHub
        # Format: https://github.com/NREL/EnergyPlus/raw/develop/weather/master.geojson
        # But individual files: https://energyplus.net/weather-download/{region}/{station}

        # Try EnergyPlus.net first
        # URL pattern: https://energyplus.net/weather-download/north_and_central_america_wmo_region_4/USA_IL_Chicago-OHare.Intl.AP.725300/all
        # This returns a zip file containing the EPW

        # Extract state abbreviation from station name (e.g., USA_IL_... -> IL)
        parts = weather_station.split('_')
        if len(parts) >= 2:
            state = parts[1]
            region = 'north_and_central_america_wmo_region_4'  # Most USA stations
        else:
            raise RuntimeError(f"Cannot parse weather station format: {weather_station}")

        # Try download
        url = f"https://energyplus.net/weather-download/{region}/{weather_station}/all"

        try:
            # Download zip file to temp location
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'weather.zip')

            print(f"Downloading EPW from: {url}")
            urllib.request.urlretrieve(url, zip_path)

            # Extract EPW from zip
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Find .epw file in zip
                epw_files = [f for f in zip_ref.namelist() if f.endswith('.epw')]
                if not epw_files:
                    raise RuntimeError(f"No EPW file found in downloaded zip from {url}")

                # Extract first EPW
                zip_ref.extract(epw_files[0], temp_dir)
                extracted_epw = os.path.join(temp_dir, epw_files[0])

                # Move to final location
                import shutil
                shutil.move(extracted_epw, epw_path)

            # Cleanup temp directory
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)

            print(f"Successfully downloaded EPW to: {epw_path}")

        except (urllib.error.URLError, urllib.error.HTTPError, zipfile.BadZipFile) as e:
            # Download failed - raise error with helpful message
            raise RuntimeError(
                f"Failed to download weather file for {weather_station}. "
                f"Error: {str(e)}. "
                f"To use this skill, either: "
                f"1) Provide a custom EPW file path, or "
                f"2) Manually download EPW files from https://energyplus.net/weather "
                f"and place them in ~/.audette/weather/ or the skill's data/weather/ directory."
            )
