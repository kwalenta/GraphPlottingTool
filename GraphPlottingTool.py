import dash
from dash import dcc, html, Input, Output, ctx
import dash_leaflet as dl
import numpy as np
import os
import helper_functions as h
from data_loader import get_data
from ui_handler import generate_network_map, generate_dynamic_plot
import sys
from MarkerJS import MarkerJS



class GraphPlottingTool:
    """
    This class is designed to create an interactive Dash web application for visualizing and analyzing network data 
    from power system optimization models. It provides a user-friendly interface with dropdowns, sliders, and interactive maps 
    to explore the data.

    Attributes:
    -----------

        input_dir (str): 
            Directory containing input data files.
        input_type (str): 
            Type of input data ('sqlite').
        tables (list): 
            List containing tables to be loaded from the input data.
        dropdown_options_y (list):
            Options for the Y-axis dropdown.
        dropdown_options_x (list): 
            Options for the X-axis dropdown.
        map_options (dict): 
            Configuration options for the map.
        app (dash.Dash): 
            Dash application instance.
        bounds (list): 
            Map bounds for visualization.

    Methods:
    -------- 
        __init__(config_path: str=None):
            Initializes the GraphPlottingTool class by loading the configuration and setting up the app.
        load_data():
            Loads network data from the results file.
        create_app():
            Initializes the Dash application.
        setup_layout():
            Defines the layout of the Dash application, including controls, map, and graph sections.
        setup_callbacks():
            Defines the callbacks for interactivity in the Dash application, such as updating the map, syncing sliders, 
            and generating dynamic plots.
        run():
            Starts the Dash server to host the application.
    """

    def __init__(self, config_path: str = None):
        """
        Initialize the class.

        This method sets up the class by loading the configuration, checking for required tables,
        and initializing the application components.

        Args:
            config_path (str, optional): Path to the configuration file. If not provided,
                                         the default "config.yml" in the current directory is used.

        Raises:
            ValueError: If the input type is not "sqlite".
            ValueError: If any of the required tables ("i", "la", "vLineP" "vGenP, "k", "gi") 
                        are missing from the configuration.

        Attributes:
            input_dir (str): Directory for input files as specified in the configuration.
            input_type (str): Type of input data ("sqlite").
            tables (dict): Dictionary of tables loaded from the configuration.
            dropdown_options_y (list): Dropdown options for the Y-axis.
            dropdown_options_x (list): Dropdown options for the X-axis.
            map_options (dict): Mapping options from the configuration.
            app (dash.Dash): Dash application instance.
            js_generator (MarkerJS): Instance of MarkerJS for generating pie charts.
            bounds (list): Bounds for the map visualization.
        """


        # Load configuration from this directory or from the provided path
        config = h.load_config("config.yml") if config_path is None else h.load_config(config_path)
        self.input_dir = os.path.abspath(config["input_dir"])
        self.input_type = config["input_type"]
        self.tables = config["tables"]
        self.dropdown_options_y = config["dropdown_options_y"]
        self.dropdown_options_x = config["dropdown_options_x"]
        self.map_options = config["map_options"]
        self.graph_options = config["graph_options"]

        if self.input_type not in ["sqlite"]:
            raise ValueError("Invalid input type. Please choose 'sqlite' or implement new format.")

        required_tables = ["i", "la", "vLineP", "k", "vGenP", "gi"]
        missing = [t for t in required_tables if t not in self.tables]
        if missing:
            raise ValueError(f"Missing required table(s): {missing}")


        self.load_data()  # Load data on initialization
        self.js_generator = MarkerJS(self.map_options, self.vGenP)  # Create instance of MarkerJS with vGenP data for pie chart sizing
        self.create_app()  # Initialize Dash app
        self.setup_layout()  # Define layout
        self.setup_callbacks()  # Define callbacks
     
    def load_data(self, ):
        """
        Loads the necessary data for the application.

        This method is intended to handle the data loading process. 
        Ensure that the required data sources are accessible and properly formatted.
        """
        get_data(self)
        
    def create_app(self):
        """
        Creates and initializes a Dash application instance.

        This method sets up a Dash application with specific configurations:
            - `suppress_callback_exceptions`: Allows callbacks to be defined even if their corresponding components are not present in the initial layout.
            - `prevent_initial_callbacks`: Disables the automatic triggering of callbacks when the app is first loaded.

        Returns:
            None
        """
        self.app = dash.Dash(__name__, suppress_callback_exceptions=True, prevent_initial_callbacks=False)

    def setup_layout(self):
        """
        Sets up the layout for the Dash application.
        This method defines the structure and components of the application's user interface, 
        including dropdowns, sliders, buttons, and visualizations such as maps and graphs. 
        The layout dynamically adjusts based on the data and configuration provided.

        Key Features:
            - Dropdowns for selecting X-axis and Y-axis options.
            - A slider for selecting time steps, with an optional number input for precise selection.
            - A range slider for selecting a range of time.
            - A map visualization on the left side, displaying network data.
            - A dynamic graph on the right side, which updates based on user interactions.

        Components:
            - Time Slider: Enables navigation through time steps.
            - Time Slider Input: Provides precise input for time step.
            - Axis Dropdowns: Allows selection of X-axis and Y-axis variables for the graph.
            - Local Button: A button for toggling scope (global or local).
            - Range Slider: Allows selection of a range of time steps.
            - Map: Displays a network visualization with tile layers and markers.
            - Graph: Displays dynamic plots based on selected data.

        Stores:
            - `last-clicked-line`: Stores the index of the last clicked line.
            - `last-clicked-node`: Stores the index of the last clicked node.
            - `map-zoom`: Stores the default zoom level for the map.

        Layout Structure:
            - Top Row: Contains global controls such as dropdowns, sliders, and buttons.
            - Main Section: Divided into two parts:
                - Left: Map visualization.
                - Right: Dynamic graph visualization.

        Styling:
            - The layout is styled for responsiveness, with flexible widths and heights.
            - Components are aligned and spaced for a clean and user-friendly interface.

        """

        self.app.layout = html.Div([

            # === GLOBAL TOP CONTROLS ROW (Slider on left, Axis dropdowns + Button on right) ===
            html.Div([

                html.Div([
                   
                    # === Time Slider + Optional Number Input ===
                    html.Div([
                        # Slider
                        html.Div([
                            dcc.Slider(
                                id='time-slider',
                                min=1,
                                max=len(self.k),
                                step=1,
                                marks=(
                                    {
                                        1: {'label': '1'},
                                        len(self.k) // 2: {'label': f"{len(self.k) // 2:d}"},
                                        len(self.k): {'label': f"{len(self.k):d}"},
                                    }
                                ),
                                tooltip={"placement": "top", "always_visible": True},
                                value=1,
                            )
                        ], style={'flex': '1'}),  # Slider fills most of the space

                        # Number input 
                        html.Div([
                            dcc.Input(
                                id='time-slider-input',
                                type='number',
                                min=1,
                                max=len(self.k),
                                step=1,
                                value=1,
                                style={'width': '70px', 'margin-left': '10px'}
                            )
                        ], style={'display': 'block', 'flex': 'none'})  # input stays compact
                    ], style={'flex': '1', 'display': 'flex', 'align-items': 'center', 'gap': '10px'}),

                ], style={
                    'display': 'flex',
                    'align-items': 'center',
                    'flex': '1',
                    'margin-right': '20px',
                    'min-width': '0',
                    'max-width': '50%'
                }),


                # Right side: Axis Dropdowns + Button (left-aligned within their container) + RangeSlider
                html.Div([
                    html.Div([
                        # html.Label("Y-Axis:", style={'font-weight': 'bold'}),
                        dcc.Dropdown(
                            id="y-axis-dropdown",
                            options=self.dropdown_options_y,
                            value=self.dropdown_options_y[0]['value'],
                            clearable=False,
                            style={'width': '120px', 'font-weight': 'bold'},
                        ),
                    ], style={'margin-right': '10px', 'margin-left': '4px'}),

                    html.Div([
                        # html.Label("X-Axis:", style={'font-weight': 'bold'}),
                        dcc.Dropdown(
                            id="x-axis-dropdown",
                            options=self.dropdown_options_x,
                            value=self.dropdown_options_x[0]['value'],
                            clearable=False,
                            style={'width': '120px', 'font-weight': 'bold'},
                        ),
                    ], style={'margin-right': '10px'}),

                    html.Div([
                        # html.Label("Scope:", style={'font-weight': 'bold'}),
                        html.Button("Local", id="local-button", n_clicks=0, style={
                            'minWidth': '80px',
                            'padding': '6px 12px',
                            'display': 'flex',
                            'alignItems': 'center',
                            'font-weight': 'bold',
                        }),
                    ]),
                    # add additional slider for the range of k values 
                    html.Div([
                        dcc.RangeSlider(
                            id='time-slider-range',
                            min=1,
                            max=len(self.k),
                            step=1,
                            marks=(
                                {
                                    1: {'label': '1'},
                                    len(self.k) // 2: {'label': f"{len(self.k) // 2:d}"},
                                    len(self.k) : {'label': f"{len(self.k) :d}"},
                                } 
                            ),
                            tooltip={"placement": "top", "always_visible": True},
                            #allowCross=False,
                            value=[1, 24],
                            pushable=24,
                            
                        ),

                    ], style={'margin-right': '10px', "flex": "1","display": 'block'}),





                ], style={
                    'display': 'flex',
                    'align-items': 'center',
                    'justify-content': 'flex-start',
                    'width': '50%',
                }),

            ], style={
                'display': 'flex',
                'align-items': 'center',
                'margin-bottom': '10px',
                'justify-content': 'space-between',
                'flex-wrap': 'wrap'
            }),

            dcc.Store(id="last-clicked-line", data=str(self.la.index[0])),
            dcc.Store(id="last-clicked-node", data=self.i.index[0]),
            dcc.Store(id="map-zoom", data=self.map_options["default_zoom"]),  # Default zoom

            # === MAIN SECTION: Map + Graph ===
            html.Div([

                # Left Section: Map
                html.Div([
                    dl.Map(children=[
                        dl.TileLayer(url='https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
                                     attribution='&copy; <a href="https://carto.com/">CARTO</a>'),
                        html.Div(id="network-layer"),
                        html.Div(id="node-wrapper"),
                    ], bounds=self.bounds, style={'height': '100%', 'width': '100%', 'background-color': '#6BA3A3'}, id="network-map",
                    zoom=self.map_options["default_zoom"], center=[np.mean(self.i['lat']), np.mean(self.i['lon'])]),
                ], style={'flex': '1', 'min-width': '0', 'height': '90vh'}),

                # Right Section: Graph
                html.Div([                   
                    dcc.Graph(id="dynamic-plot", style={'width': '100%', 'height': '100%', 'background-color': '#6BA3A3'}), # NOTE: this whole html.Div is replaced in the callback !!                  
                ], id="dynamic-plot-container", style={'flex': '1', 'min-width': '0', 'height': '90vh', 'margin-top': '0px'})
            ], style={'display': 'flex', 'gap': '10px', 'height': '90vh', 'flex-wrap': 'wrap'}),
        ], style={"background-color": "#6BA3A3", "padding": "10px"})

    def setup_callbacks(self):
        """
        Sets up all the Dash callbacks for the application.
        This method defines multiple callbacks to handle user interactions and update
        the application state dynamically. The callbacks include:

        1. `update_network`: Updates the network map based on the selected time
            and zoom level.
            - Outputs: Updates the "children" property of the "network-map" component
                and the "node-wrapper" component.
            - Inputs:  "time-slider" value, and "map-zoom" data.
        2. `store_last_clicked_line`: Stores the ID of the last clicked line.
            - Outputs: Updates the "data" property of the "last-clicked-line" component.
            - Inputs: Click events for each line in the dataset.
        3. `store_last_clicked_node`: Stores the ID of the last clicked node.
            - Outputs: Updates the "data" property of the "last-clicked-node" component.
            - Inputs: Click events for each node in the dataset.
        4. `sync_slider_and_input`: Synchronizes the values of the time slider and its corresponding input field.
            - Outputs: Updates the "value" properties of both the "time-slider" and 
              "time-slider-input" components.
            - Inputs: "time-slider" value and "time-slider-input" value.
        5. `toggle_button_label`: Toggles the label of the "local-button" between 
            "Local" and "Global" based on the number of clicks.
            - Outputs: Updates the "children" property of the "local-button" component.
            - Inputs: Click events on the "local-button".
        6. `store_map_zoom`: Stores the current zoom level of the network map.
            - Outputs: Updates the "data" property of the "map-zoom" component.
            - Inputs: "zoom" property of the "network-map" component.
        7. `update_dynamic_plot`: Updates the dynamic plot based on various user inputs, including axis selections, clicked line or node, scope, and time range.
            - Outputs: Updates the "children" property of the "dynamic-plot-container" 
              component.
            - Inputs: "x-axis-dropdown" value, "y-axis-dropdown" value, 
              "last-clicked-line" data, "last-clicked-node" data, 
              "local-button" children, and "time-slider-range" value.

        Each callback is designed to handle specific interactions and ensure the 
        application responds dynamically to user inputs.
        """

        @self.app.callback(
            [
             Output("network-layer", "children"),  
             Output("node-wrapper", "children")],
            [
             Input("time-slider", "value"),
             Input("map-zoom", "data")
            ],          
             # prevent_initial_call=True
        )
        def update_network(selected_time, zoom_level):
            arrows, node_layer = generate_network_map(
                self=self,
                selected_time=selected_time,
                zoom_level=zoom_level,
            )
            return arrows, node_layer
        
        @self.app.callback(
            Output("last-clicked-line", "data"),
            [Input(str(line.Index), "n_clicks") for line in self.la.itertuples(index=True)]
        )
        def store_last_clicked_line(*args):
            if not ctx.triggered:
                return None
            
            clicked_id = ctx.triggered[0]['prop_id'].split('.')[0]
            print(f"Clicked line: {clicked_id}")
            return clicked_id

        @self.app.callback(
            Output("last-clicked-node", "data"),
            Input("node-layer", "clickData"),        
            )
        def store_last_clicked_node(click_data):
            if not click_data:
                return dash.no_update
            clicked_id = click_data["properties"]["id"]
            print(f"Clicked node: {clicked_id}")
            return clicked_id
        
        @self.app.callback(
            Output("time-slider", "value"),
            Output("time-slider-input", "value"),
            Input("time-slider", "value"),
            Input("time-slider-input", "value"),
        )
        def sync_slider_and_input(slider_val, input_val):
            ctx = dash.callback_context
            if not ctx.triggered:
                raise dash.exceptions.PreventUpdate

            triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
            if triggered_id == "time-slider":
                return slider_val, slider_val
            else:
                return input_val, input_val
               
        @self.app.callback(
            Output("local-button", "children"),
            Input("local-button", "n_clicks")
        )
        def toggle_button_label(n_clicks):
            if n_clicks % 2 == 0:
                return "Local"
            else:
                return "Global"

        @self.app.callback(
            Output("map-zoom", "data"),
            Input("network-map", "zoom")
        )
        def store_map_zoom(zoom_level):
            return zoom_level

        @self.app.callback(
            Output("dynamic-plot-container", "children"),
            [Input("x-axis-dropdown", "value"), 
             Input("y-axis-dropdown", "value"), 
             Input("last-clicked-line", "data"),
             Input("last-clicked-node", "data"),
             Input("local-button", "children"),
             Input("time-slider-range", "value")],
             # prevent_initial_call=True

        )
        def update_dynamic_plot(x_axis, y_axis, line_idx, node_idx, scope, time_range):
            return generate_dynamic_plot(
                self=self,
                x_axis=x_axis,
                y_axis=y_axis,
                line_idx=line_idx,
                node_idx=node_idx,
                scope=scope,
                time_range=time_range
            )
    
    def run(self):
        """
        Starts the application by running the Flask development server.

        This method initializes and runs the Flask application with debugging
        disabled for production use.

        Returns:
            None
        """
        self.app.run(debug=False)

if __name__ == "__main__":
    # check for passed config file (if calling from command line)
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = "config.yml"

    # fallback if config doesn't exist
    if not os.path.exists(config_path):
        h.copy_default_config()  # assumes it writes to config.yml
    else:
        # Run with specified config
        GraphPlottingTool(config_path=config_path).run()



