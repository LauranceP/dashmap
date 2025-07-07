# dashmap

This Python script generates an interactive HTML map from GPS log files captured by a [DriveVision](https://drivevision.com.au/products/drivevision-dash-cam) dashcam. The map displays GPS tracks and timestamps, and links them to corresponding video files when available. It uses [Folium](https://python-visualization.github.io/folium/) for map visualization.

## 📦 Features

* Parses dashcam GPS `.TXT` files to extract position and time  
* Filters GPS data to remove errors and sudden jumps  
* Draws paths for each trip  
* Links markers to associated video files (e.g., `.MP4` in `CARDV/MOVIE_A`)  
* Supports satellite or default map tiles  
* Outputs a self-contained `.html` map file  

> ⚠️ The GPS can be unreliable and occasionally makes sudden jumps to another hemisphere, resulting in a messy map. To counter this, coordinates are filtered to the southeast quadrant, and a maximum allowed step between consecutive points is enforced.

## 📁 Folder Structure

Each trip is expected to have the following structure. The `RO` subfolder is optional. This layout supports direct copying from the SD card:

```
input_folder/
├── TripName1/
│   ├── GPSdata/
│   │   └── *.TXT
│   └── CARDV/
│       └── MOVIE_A/
│           ├── *.MP4
│           └── RO/
│               └── *.MP4
├── TripName2/
│   └── ...
```

## 🚀 Usage

```bash
python dashcam_map.py --input path/to/input_folder
```

### Optional Arguments

| Flag           | Description                                                 | Default                       |
|----------------|-------------------------------------------------------------|-------------------------------|
| `--input`      | Path to the root input folder                               | `demo`                        |
| `--output`     | Output HTML file path (relative to input if not absolute)   | `input/dashcam_gps_map.html` |
| `--zoom`       | Initial map zoom level                                      | `15`                          |
| `--lat`        | Initial map latitude                                        | `-16.93`                      |
| `--lon`        | Initial map longitude                                       | `145.44`                      |
| `--satellite`  | Use Esri satellite imagery as the base map                  | Off                           |
| `--max-jump`   | Maximum allowed GPS jump (in km) to filter out outliers     | `0.5`                         |
| `--downsample` | Minimum time (in seconds) between GPS points                | `6`                           |

### Example

A small set of GPS and video files is included as a demo. These include cases where video is unavailable or write-protected. Demo videos are compressed to save space.

```bash
python dashcam_map.py --input "demo/" --zoom 15 --satellite
```

## 💠 Requirements

* Python 3.6+
* Install dependencies with:

```bash
pip install folium
```
