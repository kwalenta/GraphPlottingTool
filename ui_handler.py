# map_helper.py
import dash_leaflet as dl
import matplotlib.pyplot as plt
import pandas as pd
import random
import uuid  

import plotly.express as px
from dash import html, dcc
import dash_leaflet.express as dlx
import math
import warnings  # Add this import at the top of the file
from plot_definitions import generate_plot



def generate_network_map(self, selected_time: int, zoom_level: int) -> tuple:
    """
    Generates a network map visualization using power flow data and bus locations.
    
    Args:
        selected_time (int): The selected time step identifier for filtering the data.
        zoom_level (int): The current zoom level of the map.

    Returns:
        tuple: A tuple of Dash Leaflet components representing the network map, including:
            - A list of polylines representing power lines with arrows indicating power flow direction.
            - A node layer representing bus locations with pie charts for power generation.

    """
    # Use config values
    line_weight = self.map_options["line_weight"]
    arrow_scale = self.map_options["arrow_zoom_scale"]
    arrow_min = self.map_options["arrow_min_size"]
    default_zoom = self.map_options["default_zoom"]
    technology_colors = self.map_options["technology_colors"]
    cluster_options = self.map_options["cluster_options"]


    vLineP_filtered = self.vLineP[self.vLineP["k"] == selected_time]
    vGenP_filtered = self.vGenP[self.vGenP["k"] == selected_time]


    # Generate positions and colors
    positions = []
    for i, j, flow in zip(vLineP_filtered["i"].values, vLineP_filtered["j"].values, vLineP_filtered["values"].values):
        if flow < 0:
            positions.append([(self.i.loc[j, 'lat'], self.i.loc[j, 'lon']), (self.i.loc[i, 'lat'], self.i.loc[i, 'lon']) ])
        else:
            positions.append([(self.i.loc[i, 'lat'], self.i.loc[i, 'lon']), (self.i.loc[j, 'lat'], self.i.loc[j, 'lon'])])


    def get_arrow_size(zoom):
        if zoom is None:
            zoom = default_zoom
        return max(arrow_min, int(zoom * arrow_scale))


    arrow_size = get_arrow_size(zoom_level)



    # Prepare the full layer contents (lines + arrows)
    network_layer = []
    for idx, (i_pos, line_id, flow_val, rel_val) in enumerate(zip(
        positions,
        vLineP_filtered["line"].values,
        vLineP_filtered["values"],
        vLineP_filtered["rel_values"]
    )):
        # Get color from colormap
        color_rgb = plt.get_cmap('RdYlGn_r')(rel_val)[:3]
        color = "#{:02x}{:02x}{:02x}".format(
            int(color_rgb[0]*255), int(color_rgb[1]*255), int(color_rgb[2]*255)
        )

        # Polyline base for the arrowheads
        polyline_base = dl.Polyline(
            positions=i_pos,
            color="black",
            weight=line_weight,
            opacity = 0,  
            id=f"line_base-{line_id}",    
            n_clicks=0
        )

        # Polyline for the line itself
        polyline_line = dl.Polyline(
            positions=i_pos,
            color=color,
            weight=line_weight,
            id=f"{line_id}",  
            children=[
            dl.Popup(f"Power Flow: {abs(flow_val):.1f} MW, Line rating: {vLineP_filtered.iloc[idx]['pPmax']:.1f} MW")
            ],       
            n_clicks=0
        )

        # PolylineDecorator (arrow)
        polyline_decorator = dl.PolylineDecorator(
            patterns=[dict(
                offset='50%',
                repeat='25%',
                arrowHead=dict(
                    pixelSize=arrow_size,
                    polygon=False,
                    pathOptions=dict(stroke=True, color=color)
                )
            )],
            children=[polyline_base],  
            n_clicks=0
        )

        # Append both line and arrow as top-level items
        network_layer.extend([polyline_decorator, polyline_line])
        # make network layer as a dl.LayerGroup


    network_layer = dl.LayerGroup(children=network_layer, id="network-layer-" + str(uuid.uuid4()), n_clicks=0)



    node_layer = generate_node_layer(self.i, self.gi, vGenP_filtered, self.js_generator, technology_colors, cluster_options)


    return network_layer, node_layer

def filter_dataframe(self, attr_str: str, scope: str, local_node: str=None, local_line: str=None, k_range: list=[]) -> pd.DataFrame:
    """
    Filters a DataFrame based on the provided attributes, scope, and conditions.

    Args:
        attr_str (str): The attribute string specifying which DataFrame to filter.
                        Options include "vGenP", "pDemandP", and "vLineP".
        scope (str): The scope of filtering. Options include "Local" and "Global".
                    - "Local": Filters data specific to a local node or line.
                    - "Global": Aggregates data globally (only applicable for "pDemandP").
        local_node (str, optional): The local node identifier for filtering when `scope` is "Local".
                                    Defaults to None.
        local_line (str, optional): The local line identifier for filtering when `scope` is "Local".
                                    Defaults to None.
        k_range (list, optional): A list of `k` values to filter the DataFrame by. Defaults to an empty list.

    Returns:
        pd.DataFrame: The filtered DataFrame based on the specified conditions.
                    Returns None if the specified DataFrame is not available.

    Note:
        - The method operates on different DataFrames (`vGenP`, `vLineP`) based on `attr_str`.
        - For "vGenP" with "Local" scope, filtering is based on the local node's group (`g`).
        - For "vLineP" with "Local" scope, filtering is based on the local line identifier.

    """
   
    df = None

    if attr_str == "vGenP":
        df = self.vGenP
        if df is None:
            return None
        if k_range:
            df = df[df["k"].isin(k_range)]
        if scope == "Local":
            g_local = self.gi[self.gi["i"] == local_node]
            df = df[df["g"].isin(g_local["g"])]

    elif attr_str == "vLineP":
        df = self.vLineP
        if df is None:
            return None
        if k_range:
            df = df[df["k"].isin(k_range)]
        if scope == "Local":
            df = df[df["line"] == local_line]

    return df

def generate_dynamic_plot(self, x_axis: str, y_axis: str, line_idx: str, node_idx: str, scope: str, time_range: list) -> html.Div:
    """
    Generates a dynamic plot based on the provided parameters.
    Parameters:
        x_axis (str): The variable to be used for the x-axis. Options include "time", "generator" and "line".
        y_axis (str): The variable to be used for the y-axis. Options include "dispatch" and "power_flow".
        line_idx (str): The str(index) of the line to be used for local power flow plots.
        node_idx (str): The index (str) of the node to be used for local dispatch or demand plots.
        scope (str): The scope of the plot, either "Global" or "Local".
        time_range (list): A 2-element list specifying the range of time steps [start, end] for the plot.
    Returns:
        html.Div: A Dash HTML Div containing the generated plot as a dcc.Graph component.

    Note:
        - The function dynamically filters the data based on the provided parameters and generates a plot using Plotly.
        - The plot type and configuration depend on the combination of x_axis and y_axis values.
        - If the combination of x_axis and y_axis is invalid, a placeholder scatter plot is generated.
        - The layout of the plot is customized with specific margins, background colors, and font sizes.

    """


    print(f"Updating plot: x_axis={x_axis}, y_axis={y_axis}, selected_time_range={time_range}, local_node={node_idx}, local_line={line_idx}, scope={scope}")
    
    fig = None
    y_df = None
    k_range = range(time_range[0], time_range[1] + 1)
    color_sequence = self.graph_options["colors"]

    
    if y_axis == "dispatch":
        y_df = filter_dataframe(self, "vGenP",  scope=scope, local_node=node_idx, k_range=k_range)
    elif y_axis == "power_flow":
        y_df = filter_dataframe(self, "vLineP", scope=scope, local_line=line_idx, k_range=k_range)

    fig = generate_plot(y_df, x_axis, y_axis, scope, node_idx, line_idx, color_sequence)

    if fig is None:
        fig = px.scatter(title="Select a valid combination for the plot")


    fig.update_layout(**self.graph_options["layout"])

    return html.Div([dcc.Graph(figure=fig, id="dynamic-plot", style={'height': '100%', 'width': '100%'}, config=self.graph_options["graph_save_options"])],
                    style={'flex': '1', 'min-width': '0', 'height': '90vh', 'margin-top': '0px'})

def generate_node_layer(buses: pd.DataFrame, gi: pd.DataFrame, vGenP_filtered: pd.DataFrame, js_generator: object, technology_colors: dict, cluster_options: dict) -> dl.GeoJSON:
    """
    Generates a GeoJSON layer for visualizing nodes with pie chart plots based on input data.
    Args:
        buses (pd.DataFrame): DataFrame containing bus information, including latitude and longitude.
        gi (pd.DataFrame): DataFrame containing generator information, including connected bus and technology type.
        vGenP_filtered (pd.DataFrame): Filtered DataFrame containing generation data to be visualized.
        js_generator (object): Object providing JavaScript functions for customizing point and cluster layers.
        technology_colors (dict): Dictionary mapping technology names to their corresponding colors.
    Returns:
        dl.GeoJSON: A Dash Leaflet GeoJSON layer with clustered nodes and pie chart visualizations.
    Notes:
        - The function merges and processes the input data to prepare it for visualization.
        - Rows with missing latitude or longitude coordinates are skipped.
        - The resulting GeoJSON layer supports clustering and custom rendering of points and clusters.
        - The size scaling is based on total generation values, with a minimum size defined by the user.
    """
    # merge vGenP and gi on g for pie chart plots
    merged = pd.merge(vGenP_filtered, gi, on="g", how="left")
    grouped = (
        merged.groupby(["i", "tec"])["values"]
        .sum()
        .reset_index()
    ) 
    pivoted = grouped.pivot(index="i", columns="tec", values="values").fillna(0)
    pivoted.reset_index(inplace=True)
    pivoted = pivoted.merge(buses, left_on="i", right_on="values", how="left")
    # check if any bus from set i is missing in column i
    missing_buses =  set(buses.index) - set(pivoted["i"]) 
    if missing_buses:
        # append the missing buses with their coordinates and 0 values
        for bus in missing_buses:
            lat = buses.loc[buses.index == bus, "lat"].values[0]
            lon = buses.loc[buses.index == bus, "lon"].values[0]
            pivoted = pd.concat([pivoted, pd.DataFrame([{"i": bus, "lat": lat, "lon": lon}])], ignore_index=True)
    
    if "unknown" not in technology_colors.keys():
        # Add a default color for unknown technologies
        technology_colors["unknown"] = "#808080"  # grey color
    if "no_generation" not in technology_colors.keys():
        # Add black as default color for no generation
        technology_colors["no_generation"] = "#000000"  # black color

    # Prepare GeoJSON input
    geo_data = []
    for _, row in pivoted.iterrows():
        values = []
        colors = []
        labels = []
        total = 0
        for tec, val in row.items():
            if tec == "i" or tec == "lat" or tec == "lon":
                continue  # skip the index and coordinates columns
            if val > 0:
                if tec not in technology_colors:
                    colors.append(technology_colors["unknown"])  # default color for unknown technology
                    warnings.warn(f"Undefined technology: {tec}. Please check the technology_colors mapping in the config file. Setting color to grey.")
                else:
                    colors.append(technology_colors[tec])
                values.append(round(val, 1))  # round values to 1 decimal place       
                labels.append(tec)         
                total += val

        if pd.isna(row["lat"]) or pd.isna(row["lon"]):
            # print(f"Warning: Missing coordinates for bus {row['i']}.")
            continue  #  invalid rows
        if total <= 0:
            # print(f"Warning: No generation data for bus {row['i']}.")
            # make a pie chart with 0 values
            values = [0]
            colors = [technology_colors["no_generation"]]
            labels = ["No Generation"]

        geo_data.append(dict(
            id=row["i"],
            lat=row["lat"],
            lon=row["lon"],
            name=row["i"],
            values=values,
            colors=colors,
            labels=labels,
        ))

    geojson = dlx.dicts_to_geojson(geo_data)
    geobuf = dlx.geojson_to_geobuf(geojson)

    # Return GeoJSON layer
    return dl.GeoJSON(
        id="node-layer",                     
        data=geobuf,
        format='geobuf',
        cluster=True,
        zoomToBoundsOnClick=True,
        superClusterOptions=dict(radius=cluster_options["cluster_radius"], maxZoom=cluster_options["maxZoom"]),
        pointToLayer=js_generator.pointToLayer(),
        clusterToLayer=js_generator.clusterToLayer(),
    )