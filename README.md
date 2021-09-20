## UDM Rasterise Proximity

Creates an ASCII raster with standardised proximity to polygons for 100m<sup>2</sup> grid cells.

A single GeoPackage (.gpkg) or Shapefile (.shp) containing polygons is required.

[`gdal_rasterize`](https://gdal.org/programs/gdal_rasterize.html) is used to burn the value `1` into a 100m resolution raster.
[`gdal_proximity`](https://gdal.org/programs/gdal_proximity.html) then generates the distance-to-feature map which is standardised.
'gdal_translate' converts to an ascii raster suitable for input to UDM. 

### Usage
`docker build -t udm-rasterise-proximity . && docker run -v "data:/data" --name udm-rasterise-proximity udm-rasterise-proximity` 
