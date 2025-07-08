import os
import folium
from folium.plugins import MarkerCluster
from datetime import datetime
import math
import re
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Generate an interactive map from dashcam GPS text files.")
    parser.add_argument("--input", default="demo", help="Path to root folder")
    parser.add_argument("--output", help="Output HTML filename (defaults to input/dashcam_gps_map.html)")
    parser.add_argument("--zoom", type=int, default=15, help="Initial zoom level")
    parser.add_argument("--lat", type=float, default=-16.93, help="Initial latitude")
    parser.add_argument("--lon", type=float, default=145.44, help="Initial longitude")
    parser.add_argument("--satellite", action="store_true", help="Use Esri satellite imagery as base map")
    parser.add_argument("--max-jump", type=float, default=0.5, help="Maximum allowed GPS jump in kilometers")
    parser.add_argument("--downsample", type=int, default=6, help="Minimum time (seconds) between GPS points")
    return parser.parse_args()

def parse_line(line):
    try:
        parts = line.strip().split()
        if len(parts) < 6 or "km/h" not in parts[5]:
            return None
        if not parts[2].startswith("S:") or not parts[3].startswith("E:"):
            return None
        date_str = parts[0]
        time_str = parts[1]
        lat = float(parts[2][2:]) * -1
        lon = float(parts[3][2:])
        timestamp = datetime.strptime(f"{date_str} {time_str}", "%Y/%m/%d %H:%M:%S")
        return lat, lon, timestamp
    except:
        return None

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def load_video_timestamps(base_cardv_dir, relative_base):
    video_dict = {}
    pattern = re.compile(r'(\d{14})_.*\.MP4', re.IGNORECASE)

    search_dirs = [
        ("", os.path.join(base_cardv_dir, "MOVIE_A"))
    ]

    search_dirs.append(("RO", os.path.join(base_cardv_dir, "MOVIE_A", "RO")))

    for label, search_dir in search_dirs:
        if not os.path.isdir(search_dir):
            continue
        for file in os.listdir(search_dir):
            match = pattern.match(file)
            if match:
                ts_str = match.group(1)
                try:
                    ts = datetime.strptime(ts_str, "%Y%m%d%H%M%S")
                    rel_parts = ["CARDV", "MOVIE_A"]
                    if label == "RO":
                        rel_parts.append("RO")
                    rel_parts.append(file)
                    video_path = os.path.join(relative_base, *rel_parts).replace("\\", "/")
                    video_dict[ts] = (video_path, label)
                except:
                    continue
    return dict(sorted(video_dict.items()))

def find_closest_video(video_dict, timestamp):
    closest_ts = None
    for ts in video_dict:
        if ts <= timestamp:
            closest_ts = ts
        else:
            break
    if closest_ts:
        return video_dict[closest_ts]
    return None

def main():
    args = parse_args()

    if not os.path.isdir(args.input):
        print(f"Error: Input directory '{args.input}' does not exist.")
        return
    
    # Set default output path if not provided
    if not args.output:
        args.output = os.path.join(args.input, "dashcam_gps_map.html")
    else:
        args.output = os.path.join(args.input, args.output)

    print(f"Generating map from: {args.input}")
    print(f"Center: ({args.lat}, {args.lon}) | Zoom: {args.zoom} | Satellite: {args.satellite}")

    if args.satellite:
        m = folium.Map(
            location=[args.lat, args.lon],
            zoom_start=args.zoom,
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Tiles © Esri'
        )
    else:
        m = folium.Map(location=[args.lat, args.lon], zoom_start=args.zoom)

    marker_cluster = MarkerCluster().add_to(m)

    for subfolder in os.listdir(args.input):
        folder_path = os.path.join(args.input, subfolder)
        gps_folder = os.path.join(folder_path, "GPSdata")
        cardv_folder = os.path.join(folder_path, "CARDV")

        if not os.path.isdir(gps_folder) or not os.path.isdir(cardv_folder):
            continue

        video_dict = load_video_timestamps(cardv_folder, subfolder)

        for file in os.listdir(gps_folder):
            if not file.endswith(".TXT"):
                continue

            filepath = os.path.join(gps_folder, file)
            last_timestamp = last_lat = last_lon = None
            track_points = []

            with open(filepath, "r") as f:
                for line in f:
                    parsed = parse_line(line)
                    if parsed:
                        lat, lon, timestamp = parsed

                        if last_timestamp is not None:
                            time_delta = (timestamp - last_timestamp).total_seconds()
                            distance_km = haversine(lat, lon, last_lat, last_lon)
                            if time_delta < args.downsample or distance_km > args.max_jump:
                                continue

                        last_timestamp = timestamp
                        last_lat = lat
                        last_lon = lon

                        result = find_closest_video(video_dict, timestamp)
                        if result:
                            video_file, folder_type = result
                        else:
                            video_file = None
                            folder_type = None

                        popup_html = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}<br>{file}"
                        if video_file:
                            popup_html += f"<br><a href='{video_file}' target='_blank'>{os.path.basename(video_file)}</a>"

                        marker_color = "green" if folder_type == "RO" else "blue"

                        folium.Marker(
                            location=[lat, lon],
                            popup=popup_html,
                            icon=folium.Icon(color=marker_color, icon="info-sign")
                        ).add_to(marker_cluster)

                        track_points.append((lat, lon))

            if len(track_points) >= 2:
                folium.PolyLine(track_points, color="red", weight=2, opacity=0.7).add_to(m)

    m.save(args.output)
    print(f"Map saved as '{args.output}'")

if __name__ == "__main__":
    main()
