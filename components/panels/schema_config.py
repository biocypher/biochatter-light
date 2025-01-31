import streamlit as st
from loguru import logger

ss = st.session_state

def check_dependencies():
    """Check if all required dependencies are installed."""
    missing_deps = []
    try:
        import networkx
    except ImportError:
        missing_deps.append("networkx")
    
    try:
        import plotly
    except ImportError:
        missing_deps.append("plotly")
    
    try:
        import yaml
    except ImportError:
        missing_deps.append("PyYAML")
    
    return missing_deps

def schema_config_panel():
    """Main function for the Schema Configuration panel."""
    try:
        # Check dependencies first
        missing_deps = check_dependencies()
        if missing_deps:
            st.error(
                "Some required dependencies are missing. Please install them using: "
                f"poetry install -E biocypher\n\n"
                f"Missing dependencies: {', '.join(missing_deps)}"
            )
            return
        
        # Import dependencies only if they're available
        import networkx as nx
        import yaml
        import json
        from pathlib import Path
        import plotly.graph_objects as go
        from typing import Dict, List, Optional
        
        logger.info("Starting schema configuration panel")
        display_info()
        
        # File upload
        uploaded_file = st.file_uploader("Upload BioCypher schema configuration (YAML)", type=['yaml', 'yml'])
        
        if 'schema_config' not in ss:
            logger.info("Initializing empty schema config")
            ss.schema_config = {}
        
        if uploaded_file is not None:
            logger.info(f"Loading schema config from uploaded file: {uploaded_file.name}")
            ss.schema_config = yaml.safe_load(uploaded_file)
        
        # Initialize or load configuration
        config = ss.schema_config
        
        # Add new node type
        new_node_type = st.text_input("Add new node type:")
        if new_node_type and new_node_type not in config:
            logger.info(f"Adding new node type: {new_node_type}")
            config[new_node_type] = {'properties': {}, 'relationships': []}
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["Graph View", "Node Configuration", "Ontology Mapping"])
        
        with tab1:
            st.subheader("Schema Graph Visualization")
            if config:
                logger.info("Creating and visualizing schema graph")
                G = create_schema_graph(config)
                visualize_schema(G)
            else:
                st.info("Upload or create a schema configuration to visualize it.")
        
        with tab2:
            if config:
                selected_node = st.selectbox("Select node type to edit:", options=list(config.keys()))
                if selected_node:
                    logger.info(f"Editing node: {selected_node}")
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_node_properties(config, selected_node)
                    with col2:
                        edit_relationships(config, selected_node)
            else:
                st.info("Upload or create a schema configuration to edit nodes.")
        
        with tab3:
            st.subheader("Ontology Mapping")
            st.info("Ontology mapping functionality coming soon...")
        
        # Save configuration
        if config:
            if st.button("Save Configuration"):
                save_path = st.text_input("Save path:", value="schema_config.yaml")
                if save_path:
                    try:
                        logger.info(f"Saving schema config to: {save_path}")
                        save_schema_config(config, Path(save_path))
                        st.success(f"Configuration saved to {save_path}")
                    except Exception as e:
                        logger.error(f"Error saving configuration: {str(e)}")
                        st.error(f"Error saving configuration: {str(e)}")
    except Exception as e:
        logger.error(f"Error in schema configuration panel: {str(e)}")
        st.error(f"An error occurred in the schema configuration panel: {str(e)}")

# Only define these functions if dependencies are available
try:
    import networkx as nx
    import yaml
    import json
    from pathlib import Path
    import plotly.graph_objects as go
    from typing import Dict, List, Optional

    def display_info():
        """Display introductory information about the Schema Configuration panel."""
        try:
            st.markdown(
                "This section allows you to interact with BioCypher schema configuration. "
                "You can visualize your schema as a graph, modify nodes and edges, map to "
                "underlying ontologies, and perform advanced mapping operations. The panel "
                "works with BioCypher's YAML configuration format and can read from and write "
                "to your pipeline configuration."
            )
        except Exception as e:
            logger.error(f"Error displaying info: {str(e)}")
            st.error("Error displaying panel information")

    def load_schema_config(config_file: Optional[Path] = None) -> Dict:
        """Load schema configuration from a YAML file or use existing."""
        try:
            if config_file and config_file.exists():
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading schema config: {str(e)}")
            st.error(f"Error loading schema configuration: {str(e)}")
            return {}

    def save_schema_config(config: Dict, config_file: Path):
        """Save schema configuration to a YAML file."""
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config, f, sort_keys=False)
        except Exception as e:
            logger.error(f"Error saving schema config: {str(e)}")
            st.error(f"Error saving schema configuration: {str(e)}")

    def create_schema_graph(config: Dict) -> nx.DiGraph:
        """Create a NetworkX graph from schema configuration."""
        try:
            G = nx.DiGraph()
            
            # Add nodes
            for node_type, node_info in config.items():
                if isinstance(node_info, dict):
                    properties = node_info.get('properties', {})
                    G.add_node(node_type, **{'type': 'node', 'properties': properties})
            
            # Add edges
            for node_type, node_info in config.items():
                if isinstance(node_info, dict) and 'relationships' in node_info:
                    for rel in node_info['relationships']:
                        source = node_type
                        target = rel.get('target')
                        rel_type = rel.get('type')
                        if target and rel_type:
                            G.add_edge(source, target, type=rel_type)
            
            return G
        except Exception as e:
            logger.error(f"Error creating schema graph: {str(e)}")
            st.error(f"Error creating schema visualization: {str(e)}")
            return nx.DiGraph()

    def visualize_schema(G: nx.DiGraph):
        """Visualize schema graph using Plotly."""
        try:
            if not G.nodes():
                st.info("No nodes to visualize. Add some nodes to see the graph.")
                return

            pos = nx.spring_layout(G)
            
            # Create edge traces
            edge_x = []
            edge_y = []
            edge_text = []
            
            for edge in G.edges(data=True):
                x0, y0 = pos[edge[0]]
                x1, y1 = pos[edge[1]]
                edge_x.extend([x0, x1, None])
                edge_y.extend([y0, y1, None])
                edge_text.append(edge[2].get('type', ''))
            
            edge_trace = go.Scatter(
                x=edge_x, y=edge_y,
                line=dict(width=1, color='#888'),
                hoverinfo='text',
                text=edge_text,
                mode='lines'
            )
            
            # Create node traces
            node_x = []
            node_y = []
            node_text = []
            
            for node in G.nodes(data=True):
                x, y = pos[node[0]]
                node_x.append(x)
                node_y.append(y)
                props = node[1].get('properties', {})
                node_text.append(f"{node[0]}<br>Properties: {list(props.keys())}")
            
            node_trace = go.Scatter(
                x=node_x, y=node_y,
                mode='markers+text',
                hoverinfo='text',
                text=[node for node in G.nodes()],
                textposition="top center",
                marker=dict(
                    size=20,
                    color='#1f77b4',
                    line_width=2
                )
            )
            
            # Create figure
            fig = go.Figure(data=[edge_trace, node_trace],
                           layout=go.Layout(
                               showlegend=False,
                               hovermode='closest',
                               margin=dict(b=0, l=0, r=0, t=0),
                               xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                               yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
                           ))
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error visualizing schema: {str(e)}")
            st.error(f"Error visualizing schema: {str(e)}")

    def edit_node_properties(config: Dict, node_type: str):
        """Edit properties of a selected node type."""
        try:
            if node_type not in config:
                config[node_type] = {'properties': {}}
            
            properties = config[node_type].get('properties', {})
            
            st.subheader(f"Properties for {node_type}")
            
            # Add new property
            new_prop = st.text_input("Add new property:")
            if new_prop and new_prop not in properties:
                properties[new_prop] = {'type': 'string'}  # default type
            
            # Edit existing properties
            for prop in list(properties.keys()):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.text(prop)
                with col2:
                    prop_type = st.selectbox(
                        "Type",
                        options=['string', 'integer', 'float', 'boolean'],
                        key=f"{node_type}_{prop}_type",
                        index=['string', 'integer', 'float', 'boolean'].index(
                            properties[prop].get('type', 'string')
                        )
                    )
                    properties[prop]['type'] = prop_type
                with col3:
                    if st.button("Delete", key=f"delete_{node_type}_{prop}"):
                        del properties[prop]
            
            config[node_type]['properties'] = properties
        except Exception as e:
            logger.error(f"Error editing node properties: {str(e)}")
            st.error(f"Error editing node properties: {str(e)}")

    def edit_relationships(config: Dict, source_type: str):
        """Edit relationships for a selected node type."""
        try:
            if source_type not in config:
                config[source_type] = {}
            
            if 'relationships' not in config[source_type]:
                config[source_type]['relationships'] = []
            
            relationships = config[source_type]['relationships']
            
            st.subheader(f"Relationships for {source_type}")
            
            # Add new relationship
            col1, col2, col3 = st.columns(3)
            with col1:
                new_target = st.selectbox("Target node type:", options=list(config.keys()), key=f"new_rel_{source_type}")
            with col2:
                new_type = st.text_input("Relationship type:", key=f"new_rel_type_{source_type}")
            with col3:
                if st.button("Add Relationship", key=f"add_rel_{source_type}"):
                    if new_type and new_target:
                        relationships.append({
                            'target': new_target,
                            'type': new_type
                        })
            
            # Edit existing relationships
            for i, rel in enumerate(relationships):
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    rel['target'] = st.selectbox(
                        "Target",
                        options=list(config.keys()),
                        key=f"{source_type}_rel_{i}_target",
                        index=list(config.keys()).index(rel['target'])
                    )
                with col2:
                    rel['type'] = st.text_input(
                        "Type",
                        value=rel['type'],
                        key=f"{source_type}_rel_{i}_type"
                    )
                with col3:
                    if st.button("Delete", key=f"delete_{source_type}_rel_{i}"):
                        relationships.pop(i)
        except Exception as e:
            logger.error(f"Error editing relationships: {str(e)}")
            st.error(f"Error editing relationships: {str(e)}")

except ImportError:
    # These functions will not be defined if dependencies are missing
    pass 