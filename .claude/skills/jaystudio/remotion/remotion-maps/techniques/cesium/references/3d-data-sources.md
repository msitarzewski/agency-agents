# Flyover data sources

## Landscape

Use MapTiler for both layers:

- `terrain-quantized-mesh-v2`: elevation encoded as Cesium quantized-mesh terrain.
- `satellite-v2`: raster satellite imagery draped on that mesh.

CesiumJS renders the layers; it does not supply the data. Set `REMOTION_MAPTILER_KEY`.

Create a key:

- https://cloud.maptiler.com/account/keys/

Official documentation:

- https://docs.maptiler.com/cesium/
- https://docs.maptiler.com/schema-raster/terrain-3d/

## City

Use Google Photorealistic 3D Tiles. Google supplies one high-resolution 3D mesh already textured
with imagery. Disable the Cesium globe and do not add MapTiler terrain or satellite beneath it. Set
`REMOTION_GOOGLE_MAPS_API_KEY`.

Create and configure a key:

- https://developers.google.com/maps/documentation/tile/get-api-key

Enable the Map Tiles API in a billing-enabled Google Cloud project and restrict the key to that API.
The application restriction must permit the local headless Remotion request.

Official documentation:

- https://developers.google.com/maps/documentation/tile/3d-tiles
- https://developers.google.com/maps/documentation/tile/policies

## Why not extruded buildings

OSM-, Overture- and vector-tile building products primarily provide footprints, approximate heights
and optional roof attributes. They are useful for analytical or stylized maps, but they do not
provide the textured architecture required for a cinematic city flyover.
