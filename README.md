## Proximity Calculator

Creates a GeoTIFF with distance to nearest feature (m) from each grid cell.

A single GeoPackage (.gpkg) or Shapefile (.shp) containing target polygons is required.

[`gdal_rasterize`](https://gdal.org/programs/gdal_rasterize.html) is used to burn the value `1` into a 100m resolution raster.
[`gdal_proximity`](https://gdal.org/programs/gdal_proximity.html) then generates the proximity map.

### Usage
`docker build -t proximity-calculator . && docker run -v "data:/data" --name proximity-calculator proximity-calculator` 
