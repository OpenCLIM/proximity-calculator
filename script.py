import numpy, sys
from osgeo import gdal
from osgeo.gdalconst import *
import subprocess
from pathlib import Path
import os
import logging
#import v_prox as v

#------------------------------------------------------------------------------------------------------------------------------

# register all of the GDAL drivers
gdal.AllRegister()

#setup paths to data 

#WINDOWS data directories
#configure directory/subdirectories
#current_dir = str(Path.cwd())
#print(current_dir)
#inputs = Path(current_dir + '/data/inputs/')
#print(inputs)
#temp = Path(current_dir + '/data/temp/')
#print(temp)
#outputs = Path(current_dir + '/data/outputs/')
#print(outputs)

#DOCKER data directories
inputs = Path("/data/inputs")
temp = Path("/data/temp")
outputs = Path("/data/outputs")
temp.mkdir(exist_ok=True)
outputs.mkdir(exist_ok=True)

#configure output
logger = logging.getLogger('udm-rasterise-proximity')
logger.setLevel(logging.INFO)
fh = logging.FileHandler(outputs / 'udm-rasterise-proximity.log')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

#get input polygons
input_files = []
for ext in ['shp', 'gpkg']:
    input_files.extend(list(inputs.glob(f"*/*.{ext}")))

assert len(input_files) > 0, 'No input files found'
selected_file = input_files[0]

#get extent 'xmin,ymin,xmax,ymax'
#WINDOWS
#extent = v.get_extent()
#DOCKER
extent = os.getenv('EXTENT')

if extent == 'None' or extent is None:
    extent = []
else:
    extent = ['-te', *extent.split(',')]

#------------------------------------------------------------------------------------------------------------------------------
#rasterise_100m

logger.info(f'Rasterizing {selected_file}')

subprocess.call(['gdal_rasterize',
                 '-burn', '1',          #fixed value to burn for all objects
                 '-tr', '100', '100',   #target resolution <xres> <yres>
                 '-co', 'COMPRESS=LZW', '-co', 'NUM_THREADS=ALL_CPUS',  #creation options
                 '-ot', 'UInt16',       #output data type
                 '-at',                 #enable all-touched rasterisation
                 *extent,               #'-te' <xmin> <ymin> <xmax> <ymax> 
                 selected_file, temp / 'rasterise_100m.tif'])    #src_datasource, dst_filename

logger.info('Rasterizing completed')

#------------------------------------------------------------------------------------------------------------------------------
#distance_100m

logger.info('Generating distance raster')

#WINDOWS
#subprocess.call(['python.exe', 'gdal_proximity.py',   
#                 temp / 'rasterise_100m.tif', temp / 'distance_100m.tif', #srcfile, dstfile    
#                 '-distunits', 'GEO',   
#                 '-ot', 'Float64',       
#                 '-co', 'COMPRESS=LZW', '-co', 'NUM_THREADS=ALL_CPUS']) #creation options 

#DOCKER
subprocess.call(['gdal_proximity.py',   
                 temp / 'rasterise_100m.tif', temp / 'distance_100m.tif', #srcfile, dstfile    
                 '-distunits', 'GEO',   
                 '-ot', 'Float64',       
                 '-co', 'COMPRESS=LZW', '-co', 'NUM_THREADS=ALL_CPUS']) #creation options                    

logger.info('Distance raster generated')

#------------------------------------------------------------------------------------------------------------------------------
#proximity_100m

logger.info('Generating proximity raster')

# load raster
ds = gdal.Open(str(temp / 'distance_100m.tif'))
if ds is None:
  print ('Could not open input raster file')
  sys.exit(1)

# read raster data and get info about it
band = ds.GetRasterBand(1)
rows = ds.RasterYSize
cols = ds.RasterXSize
dist = band.ReadAsArray()

#WINDOWS
#if v.get_squared() == 'true':
#    dist = dist * dist
#DOCKER
if os.getenv('SQUARED') == 'true':
    dist = dist * dist

#find distance minima maxima
min_dist = dist.min()
max_dist = dist.max()

#set standardisation polarity

#WINDOWS
#polarity = v.get_polarity()
#DOCKER
polarity = os.getenv('POLARITY')

if polarity == 'forward':
    prox = (dist - min_dist) / (max_dist - min_dist)
elif polarity == 'reverse':
    prox = (max_dist - dist) / (max_dist - min_dist)

# create the output image
driver = gdal.GetDriverByName("GTiff")
outData = driver.Create(str(temp / 'proximity_100m.tif'), cols, rows, 1, GDT_Float64)
if outData is None:
    print ('Could not create output raster file')
    sys.exit(1)

# georeference the image and set the projection
outData.SetGeoTransform(ds.GetGeoTransform())
outData.SetProjection(ds.GetProjection())

#write data to output array
arr_out = numpy.zeros((rows,cols), numpy.float64)

for i in range(0, rows):
    for j in range(0, cols):
        arr_out[i,j] = prox[i,j]      


outData.GetRasterBand(1).WriteArray(arr_out)
outData.GetRasterBand(1).SetNoDataValue(-1)

# flush data to disk
outData.FlushCache()

outData = None
band=None
ds=None

logger.info('Proximity raster generated')

#------------------------------------------------------------------------------------------------------------------------------
#translate

#get layer name

#WINDOWS
#layer_name = v.get_layer_name() + '_proximity_100m.asc'
#DOCKER
layer_name = os.getenv('LAYER_NAME') + '_proximity_100m.asc'

logger.info('Translating raster')

subprocess.call(['gdal_translate',                 
                 '-tr', '100', '100',	#target resolution <xres> <yres>                
                 '-ot', 'Float64',		#output data type    
                 '-a_nodata', '-1',		#set nodata value             
                 temp / 'proximity_100m.tif', outputs / layer_name])	#srcfile, dstfile

logger.info('Translating completed')

#------------------------------------------------------------------------------------------------------------------------------

