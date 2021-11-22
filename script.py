from osgeo import gdal
from osgeo.gdalconst import *
import subprocess
from pathlib import Path
import os
import logging

# register all of the GDAL drivers
gdal.AllRegister()

# setup paths to data
data = Path(os.getenv('DATA_PATH', '/data'))

inputs = data / 'inputs'
polygons = inputs / 'polygons'
temp = data / 'temp'
outputs = data / 'outputs'
log_dir = outputs / 'log'
output_data_dir = outputs / 'data'


temp.mkdir(exist_ok=True)
outputs.mkdir(exist_ok=True)
log_dir.mkdir(exist_ok=True)
output_data_dir.mkdir(exist_ok=True)

# configure logger
logger = logging.getLogger('udm-rasterise-proximity')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(log_dir / 'udm-rasterise-proximity.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

# get input polygons
input_files = []
for ext in ['shp', 'gpkg']:
    input_files.extend(list(polygons.glob(f"*.{ext}")))

assert len(input_files) > 0, 'No input files found'
selected_file = input_files[0]

extent = os.getenv('EXTENT')

if extent == 'None' or extent is None:
    extent = []
else:
    extent = ['-te', *extent.split(',')]

# rasterise_100m

logger.info(f'Rasterizing {selected_file}')

subprocess.call(['gdal_rasterize',
                 '-burn', '1',          # fixed value to burn for all objects
                 '-tr', '100', '100',   # target resolution <xres> <yres>
                 '-co', 'COMPRESS=LZW', '-co', 'NUM_THREADS=ALL_CPUS',  # creation options
                 '-ot', 'UInt16',       # output data type
                 '-at',                 # enable all-touched rasterisation
                 *extent,               # '-te' <xmin> <ymin> <xmax> <ymax>
                 selected_file, temp / 'rasterise_100m.tif'])    # src_datasource, dst_filename

logger.info('Rasterizing completed')

# distance_100m

logger.info('Generating distance raster')

call = [
    'gdal_proximity.py',
    temp / 'rasterise_100m.tif', temp / 'distance_100m.tif',  # srcfile, dstfile
    '-distunits', 'GEO',
    '-ot', 'Float64',
    '-co', 'COMPRESS=LZW', '-co', 'NUM_THREADS=ALL_CPUS'  # creation options
]

subprocess.call(['python.exe'] + call if os.name == 'nt' else call)

logger.info('Distance raster generated')

# proximity_100m

logger.info('Generating proximity raster')

# load raster
distance_tif = gdal.Open(str(temp / 'distance_100m.tif'))

assert distance_tif is not None, 'Could not open distance raster'

# read raster data and get info about it
band = distance_tif.GetRasterBand(1)
rows = distance_tif.RasterYSize
cols = distance_tif.RasterXSize
distance = band.ReadAsArray()

if os.getenv('SQUARED').lower() == 'true':
    distance = distance * distance

# find distance minima maxima
#min_distance = distance.min()
#max_dist = distance.max()

# set standardisation polarity
#polarity = os.getenv('POLARITY')
#if polarity == 'forward':
#    proximity = (distance - min_distance) / (max_dist - min_distance)
#elif polarity == 'reverse':
#    proximity = (max_dist - distance) / (max_dist - min_distance)
#else:
#    raise Exception('Polarity must be either forward or reverse')

proximity = distance

# create the output image
driver = gdal.GetDriverByName("GTiff")
proximity_tif_path = str(temp / 'proximity_100m.tif')
proximity_tif = driver.Create(proximity_tif_path, cols, rows, 1, GDT_Float64)
assert proximity_tif is not None, 'Could not create output raster file'

# georeference the image and set the projection
proximity_tif.SetGeoTransform(distance_tif.GetGeoTransform())
proximity_tif.SetProjection(distance_tif.GetProjection())

proximity_tif.GetRasterBand(1).WriteArray(proximity)
proximity_tif.GetRasterBand(1).SetNoDataValue(-1)

# flush data to disk
proximity_tif.FlushCache()

proximity_tif = None
band = None
distance_tif = None

logger.info('Proximity raster generated')

# get layer name
layer_name = os.getenv('LAYER_NAME') + '_proximity_100m.asc'

# translate to ascii
logger.info('Translating raster')

subprocess.call(['gdal_translate',                 
                 '-tr', '100', '100',   # target resolution <xres> <yres>
                 '-ot', 'Float64',		# output data type
                 '-a_nodata', '-1',		# set nodata value
                 proximity_tif_path, output_data_dir / layer_name])  # srcfile, dstfile

logger.info('Translating completed')
