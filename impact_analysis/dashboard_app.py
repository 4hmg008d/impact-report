"""
Impact Analysis Dashboard Application
Main entry point for the Dash web application
"""

import dash
import dash_bootstrap_components as dbc
import logging
import sys
import os
import yaml

from .src.app_dashboard_state import dashboard_state
from .src.app_dash_components import create_main_layout
from .src.app_callbacks import register_callbacks


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ImpactAnalysisDashboard:
    """Main dashboard application class"""
    
    def __init__(self, config_path: str = None):
        """Initialize the dashboard application"""
        # Determine config path
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__),
                'config_impact_analysis.yaml'
            )
        
        self.config_path = os.path.abspath(config_path)
        
        # Load initial configuration
        self._load_initial_config()
        
        # Initialize Dash app with Bootstrap theme
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            suppress_callback_exceptions=True
        )
        
        # Set app title
        self.app.title = "Impact Analysis Dashboard"
        
        # Create layout with initial config
        config_str = dashboard_state.get_config_as_yaml_string()
        filter_columns = dashboard_state.filter_columns
        filter_options = {}  # Empty initially, will be populated after data load
        
        self.app.layout = create_main_layout(config_str, filter_columns, filter_options)
        
        # Register callbacks
        register_callbacks(self.app)
        
        logger.info(f"Dashboard initialized with config: {self.config_path}")
    
    def _load_initial_config(self):
        """Load initial configuration into dashboard state"""
        try:
            with open(self.config_path, 'r') as f:
                config_yaml = yaml.safe_load(f)
            
            dashboard_state.set_config(config_yaml, self.config_path)
            logger.info("Initial configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading initial configuration: {e}")
            # Set default empty config
            dashboard_state.set_config({}, self.config_path)
    
    def run(self, debug: bool = True, host: str = '127.0.0.1', port: int = 8050):
        """Run the dashboard application"""
        logger.info(f"Starting dashboard at http://{host}:{port}")
        self.app.run(debug=debug, host=host, port=port)


def main():
    """Main function to run the dashboard"""
    # Get config path from command line or use default
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # Create and run dashboard
    dashboard = ImpactAnalysisDashboard(config_path)
    dashboard.run()


if __name__ == "__main__":
    main()
