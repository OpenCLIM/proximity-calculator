import subprocess
from pathlib import Path
import os
import logging

outputs = Path("/data/outputs")
inputs = Path("/data/inputs")

input_files = []
for ext in ['shp', 'gpkg']:
    input_files.extend(list(inputs.glob(f"*/*.{ext}")))

assert len(input_files) > 0, 'No input files found'

outputs.mkdir(exist_ok=True)

logger = logging.getLogger('coverage_calculator')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(outputs / 'coverage_calculator.log')
fh.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

extent = os.getenv('EXTENT')
if extent == 'None' or extent is None:
    extent = []
else:
    extent = ['-te', *extent.split(',')]

logger.info(f'Rasterizing {selected_file}')

subprocess.call(['gdal_rasterize',
                 '-burn', '1',
                 '-tr', '100', '100',
                 '-co', 'COMPRESS=LZW', '-co', 'NUM_THREADS=ALL_CPUS',
                 '-ot', 'UInt16',
                 '-at',  # all pixels touched by polygons will be burned
                 *extent,
                 input_files[0], outputs / 'raster.tif'])

logger.info('Rasterizing completed')

logger.info('Generating proximity raster')

subprocess.call(['gdal_proximity.py',
                 outputs / 'raster.tif', outputs / 'proximity.tif',
                 '-distunits', 'GEO',
                 '-co', 'COMPRESS=LZW', '-co', 'NUM_THREADS=ALL_CPUS'])

logger.info('Proximity raster generated')
