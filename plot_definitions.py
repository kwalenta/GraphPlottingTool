import plotly.express as px
import pandas as pd

def generate_plot(y_df: pd.DataFrame, x_axis: str, y_axis: str, scope: str, node_idx: int, line_idx: int, color_sequence: list):
    """
    Generates a plot based on the provided data and parameters.
    Parameters:
        y_df (pd.DataFrame): The input data for plotting. Must contain columns relevant to the selected x_axis and y_axis.
        x_axis (str): The x-axis variable. Options include "time", "generator", or "line".
        y_axis (str): The y-axis variable. Options include "dispatch", "demand", or "power_flow".
        scope (str): The scope of the plot. Can be "Global" or "Local".
        node_idx (int): The index of the node for local plots. Used when scope is "Local".
        line_idx (int): The index of the line for local plots. Used when scope is "Local".
        color_sequence (list): A list of colors to use for the plot.
    Returns:
        plotly.graph_objects.Figure or None: The generated plot as a Plotly figure object. 
        Returns None if the input data is empty or invalid.
    Notes:
        - The function supports different plot types (area, line, bar, histogram) based on the x_axis and y_axis combination.
        - The labels and titles of the plots are dynamically generated based on the input parameters.
        - If the combination of x_axis and y_axis is not supported, the function returns None.
    """

    if y_df is None or y_df.empty:
        print("No data available for plotting.")
        return None
    else:

        if x_axis == "time" and y_axis == "dispatch":
            x_label = "Time"
            title = "Global dispatch over time" if scope == "Global" else f"Local dispatch for {node_idx} over time"
            fig = px.area(y_df, x="k", y="values", color="g", title=title, labels={"k": x_label, "values": "Dispatch", "g": "Generator"}, color_discrete_sequence=color_sequence,)

        elif x_axis == "time" and y_axis == "demand":
            x_label = "Time"
            fig = px.line(y_df, x="k", y="values", title="Demand Over Time", labels={"i": x_label, "values": "Demand"}, color_discrete_sequence=color_sequence,)
        
        elif x_axis == "time" and y_axis == "power_flow":
            x_label = "Time"
            title = "Power Flow over time" if scope == "Global" else f"Local Power Flow for {line_idx} over time"
            fig = px.line(y_df, x="k", y="values", color="line", title=title, labels={"k": x_label, "values": "Power Flow", "line": "Line"},
                            hover_data={"values": True, "line": True, "i": True, "j": True}, color_discrete_sequence=color_sequence,)

        elif x_axis == "generator" and y_axis == "dispatch":
            x_label = "Generator"
            y_df["k"] = y_df["k"].astype(str).copy()
            y_df["g"] = y_df["g"].astype(str).copy()
            y_df["values"] = pd.to_numeric(y_df["values"], errors="coerce")
            title = "Global dispatch for each generator" if scope == "Global" else f"Local dispatch for {node_idx}"
            fig = px.bar(y_df, x="g", y="values", color="g", title=title, labels={"g": x_label, "values": "Dispatch", "k": "Time"},
                         hover_data={"values": False, "k": False}, color_discrete_sequence=color_sequence)

        elif x_axis == "line" and y_axis == "power_flow":
            x_label = "Line"
            title = "Power Flow Distribution over all Lines" if scope == "Global" else f"Local Power Flow Distribution for {line_idx}"
            fig = px.histogram(y_df, x="values", color="line", title=title, nbins=10,
                                 color_discrete_sequence=color_sequence)
        else:
            fig = None
        
        return fig