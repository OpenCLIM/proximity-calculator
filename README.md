## UDM Rasterise Proximity

Creates an ASCII raster with proximity to polygons for 100m<sup>2</sup> grid cells.

A single GeoPackage (.gpkg) or Shapefile (.shp) containing polygons is required.

[`gdal_rasterize`](https://gdal.org/programs/gdal_rasterize.html) is used to burn the value `1` into a 100m resolution raster.
[`gdal_proximity`](https://gdal.org/programs/gdal_proximity.html) then generates the distance-to-feature map.
'gdal_translate' converts to an ascii raster suitable for input to UDM. 

### Usage
#### sudo code example:
'docker build -t <name of image > . && docker run -v "<full local path>:/data" <any parameters which need passing> --name <name of container> <name of image>'

#### code example
`docker build -t udm-rasterise-proximity . && docker run -v "data:/data" --name udm-rasterise-proximity udm-rasterise-proximity` 

#### Passing parameters
For <any parameters which need passing> use the following notation:
 --env <parameter name>=<parameter value>

