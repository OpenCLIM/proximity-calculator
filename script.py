import subprocess
from pathlib import Path
import os

outputs = Path("/data/outputs")
inputs = Path("/data/inputs")

input_files = []
for ext in ['shp', 'gpkg']:
    input_files.extend(list(inputs.glob(f"*/*.{ext}")))

assert len(input_files) > 0, 'No input files found'

outputs.mkdir(exist_ok=True)

extent = os.getenv('EXTENT')
if extent == 'None' or extent is None:
    extent = []
else:
    extent = ['-te', *extent.split(',')]

subprocess.call(['gdal_rasterize',
                 '-burn', '1',
                 '-tr', '100', '100',
                 '-co', 'COMPRESS=LZW', '-co', 'NUM_THREADS=ALL_CPUS',
                 '-ot', 'UInt16',
                 '-at',  # all pixels touched by polygons will be burned
                 *extent,
                 input_files[0], outputs / 'raster.tif'])


subprocess.call(['gdal_proximity.py'])
