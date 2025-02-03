import streamlit as st
from loguru import logger
import numpy as np
from pathlib import Path

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

def create_toy_schema() -> dict:
    """Create a toy schema demonstrating all BioCypher schema features."""
    return {
        "Person": {
            "represented_as": "node",
            "properties": {
                "name": "string",  # Simple format for self-explanatory property
                "age": "integer",  # Simple format for self-explanatory property
                "email": {
                    "type": "string",
                    "description": "Primary contact email address for the person"
                }
            },
            "input_label": "Person",
            "is_a": "Agent"
        },
        "Organization": {
            "represented_as": "node",
            "properties": {
                "name": "string",  # Simple format
                "founded_year": {
                    "type": "integer",
                    "description": "Year when the organization was officially established"
                },
                "location": {
                    "type": "string",
                    "description": "Primary headquarters location or main office address"
                }
            },
            "input_label": "Organization",
            "is_a": "Institution"
        },
        "WORKS_FOR": {
            "represented_as": "edge",
            "source": "Person",
            "target": "Organization",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "Date when the person started working for the organization (YYYY-MM-DD)"
                },
                "role": {
                    "type": "string",
                    "description": "Job title or position within the organization"
                }
            },
            "is_a": "Employment"
        },
        "KNOWS": {
            "represented_as": "edge",
            "source": "Person",
            "target": "Person",
            "properties": {
                "since": {
                    "type": "string",
                    "description": "Date when the relationship was established (YYYY-MM-DD)"
                },
                "relationship_type": {
                    "type": "string",
                    "description": "Nature of the relationship (e.g., colleague, friend, mentor)"
                }
            },
            "is_a": "SocialRelation"
        },
        "Project": {
            "represented_as": "node",
            "properties": {
                "name": {"type": "string"},  # Self-explanatory
                "budget": {
                    "type": "float",
                    "description": "Total allocated budget in the project's base currency"
                },
                "status": {
                    "type": "string",
                    "description": "Current project status (e.g., planned, active, completed, on-hold)"
                }
            }
        },
        "Collaboration": {
            "represented_as": "node",
            "source": ["Person", "Organization"],
            "target": "Project",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "Role of the participant (Person or Organization) in the collaboration"
                },
                "contribution": {
                    "type": "string",
                    "description": "Specific contribution or responsibility in the project"
                }
            },
            "is_a": "Partnership"
        },
        "MANAGES": {
            "represented_as": "edge",
            "source": "Person",
            "target": ["Project", "Organization"],
            "properties": {
                "level": {
                    "type": "string",
                    "description": "Management level (e.g., project manager, department head, CEO)"
                },
                "department": {
                    "type": "string",
                    "description": "Department or division where the management role is exercised"
                }
            }
        }
    }

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
        import plotly.graph_objects as go
        
        logger.info("Starting schema configuration panel")
        display_info()
        
        # File upload and save in 3 columns
        col1, col2, col3 = st.columns([4, 4, 1])
        with col1:
            # File upload
            uploaded_file = st.file_uploader("Upload BioCypher schema configuration (YAML)", type=['yaml', 'yml'])
        
        with col2:
            # Save configuration filename input
            save_path = st.text_input("Save configuration as:", value="schema_config.yaml")
            
        with col3:
            # Save button in its own column, vertically centered
            st.write("")  # Add some vertical spacing
            if st.button("Save", use_container_width=True):
                if save_path:
                    try:
                        logger.info(f"Saving schema config to: {save_path}")
                        save_schema_config(ss.get('schema_config', create_toy_schema()), Path(save_path))
                        st.success(f"Configuration saved to {save_path}")
                    except Exception as e:
                        logger.error(f"Error saving configuration: {str(e)}")
                        st.error(f"Error saving configuration: {str(e)}")
        
        if 'schema_config' not in ss:
            logger.info("Initializing with toy schema")
            ss.schema_config = create_toy_schema()
        
        if uploaded_file is not None:
            logger.info(f"Loading schema config from uploaded file: {uploaded_file.name}")
            ss.schema_config = yaml.safe_load(uploaded_file)
        
        # Initialize or load configuration
        config = ss.schema_config
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Graph View", "Schema Editor", "Ontology Mapping", "YAML Preview"])
        
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
                # Schema manipulation section
                st.subheader("Schema Editor")
                
                # Create subtabs for different editing functions
                edit_tab1, edit_tab2, edit_tab3, edit_tab4, edit_tab5 = st.tabs([
                    "Add Entities", 
                    "Add Relationships", 
                    "Modify Entities",
                    "Modify Relationships",
                    "Delete Elements"
                ])
                
                with edit_tab1:
                    st.subheader("Add New Entity")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        new_entity = st.text_input("Entity name:")
                    with col2:
                        entity_type = st.selectbox(
                            "Type",
                            options=['node', 'edge'],
                            key='new_entity_type'
                        )
                    
                    if new_entity and st.button("Add Entity"):
                        if new_entity not in config:
                            logger.info(f"Adding new entity: {new_entity}")
                            config[new_entity] = {
                                'represented_as': entity_type,
                                'properties': {}
                            }
                            st.success(f"Added {entity_type}: {new_entity}")
                
                with edit_tab2:
                    st.subheader("Add New Relationship")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        source = st.selectbox("Source entity:", options=list(config.keys()))
                    with col2:
                        target = st.selectbox("Target entity:", options=list(config.keys()))
                    with col3:
                        rel_type = st.text_input("Relationship type:")
                    
                    if source and target and rel_type and st.button("Add Relationship"):
                        if rel_type not in config:
                            config[rel_type] = {
                                'represented_as': 'edge',
                                'source': source,
                                'target': target,
                                'properties': {}
                            }
                            st.success(f"Added relationship: {rel_type}")
                
                with edit_tab3:
                    st.subheader("Modify Entity Properties")
                    # Filter for nodes
                    nodes = [k for k, v in config.items() 
                            if v.get('represented_as', 'node') == 'node']
                    selected_node = st.selectbox(
                        "Select entity to modify:",
                        options=nodes,
                        key='modify_node_selector'
                    )
                    if selected_node:
                        edit_node_properties(config, selected_node)
                
                with edit_tab4:
                    st.subheader("Modify Relationships")
                    # Filter for edges
                    edges = [k for k, v in config.items() 
                            if v.get('represented_as') == 'edge']
                    selected_edge = st.selectbox(
                        "Select relationship to modify:",
                        options=edges,
                        key='modify_edge_selector'
                    )
                    if selected_edge:
                        st.subheader("Edge Configuration")
                        col1, col2 = st.columns(2)
                        with col1:
                            source = st.selectbox(
                                "Source entity",
                                options=list(config.keys()),
                                key=f"{selected_edge}_source",
                                index=list(config.keys()).index(config[selected_edge].get('source', list(config.keys())[0]))
                            )
                            config[selected_edge]['source'] = source
                        with col2:
                            target = st.selectbox(
                                "Target entity",
                                options=list(config.keys()),
                                key=f"{selected_edge}_target",
                                index=list(config.keys()).index(config[selected_edge].get('target', list(config.keys())[0]))
                            )
                            config[selected_edge]['target'] = target
                        
                        edit_node_properties(config, selected_edge)  # Reuse for edge properties
                
                with edit_tab5:
                    st.subheader("Delete Elements")
                    element_to_delete = st.selectbox(
                        "Select element to delete:",
                        options=list(config.keys()),
                        key='delete_selector'
                    )
                    if element_to_delete:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            element_type = config[element_to_delete].get('represented_as', 'node')
                            st.info(f"Selected: {element_to_delete} ({element_type})")
                        with col2:
                            if st.button("Delete", type="secondary", key=f"delete_{element_to_delete}"):
                                confirm = st.checkbox(f"Confirm deletion of {element_to_delete}")
                                if confirm:
                                    # Delete from both config and session state
                                    del config[element_to_delete]
                                    ss.schema_config = config
                                    st.success(f"Deleted {element_to_delete}")
                                    st.experimental_rerun()
            else:
                st.info("Upload or create a schema configuration to edit it.")
        
        with tab3:
            st.subheader("Ontology Mapping")
            st.info("Ontology mapping functionality coming soon...")
            
        with tab4:
            st.subheader("YAML Preview")
            if config:
                yaml_str = yaml.dump(config, sort_keys=False, default_flow_style=False)
                st.code(yaml_str, language="yaml")
            else:
                st.info("Upload or create a schema configuration to see its YAML representation.")
    except Exception as e:
        logger.error(f"Error in schema configuration panel: {str(e)}")
        st.error(f"An error occurred in the schema configuration panel: {str(e)}")

# Only define these functions if dependencies are available
try:
    import networkx as nx
    import yaml
    import json
    import plotly.graph_objects as go

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

    def load_schema_config(config_file: Path | None = None) -> dict:
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

    def save_schema_config(config: dict, config_file: Path):
        """Save schema configuration to a YAML file."""
        try:
            with open(config_file, 'w') as f:
                yaml.dump(config, f, sort_keys=False)
        except Exception as e:
            logger.error(f"Error saving schema config: {str(e)}")
            st.error(f"Error saving schema configuration: {str(e)}")

    def create_schema_graph(config: dict) -> nx.DiGraph:
        """Create a NetworkX graph from schema configuration."""
        try:
            G = nx.DiGraph()
            
            # First pass: Add all explicit nodes
            for entity_type, entity_info in config.items():
                if isinstance(entity_info, dict):
                    representation = entity_info.get('represented_as', 'node')
                    if representation == 'node':
                        properties = entity_info.get('properties', {})
                        input_label = entity_info.get('input_label', '')
                        is_a = entity_info.get('is_a', '')
                        G.add_node(entity_type, **{
                            'type': 'node',
                            'properties': properties,
                            'input_label': input_label,
                            'is_a': is_a
                        })
            
            # Second pass: Process edges and relationship nodes
            for entity_type, entity_info in config.items():
                if isinstance(entity_info, dict):
                    # Get source and target information if present
                    sources = entity_info.get('source', [])
                    targets = entity_info.get('target', [])
                    
                    # Skip if no source/target information
                    if not sources and not targets:
                        continue
                        
                    # Convert to lists if single values
                    if isinstance(sources, str):
                        sources = [sources]
                    if isinstance(targets, str):
                        targets = [targets]
                    
                    representation = entity_info.get('represented_as', 'edge')
                    input_label = entity_info.get('input_label', '')
                    is_a = entity_info.get('is_a', '')
                    
                    if representation == 'node':
                        # This is a relationship node - add node and connecting edges
                        G.add_node(entity_type, **{
                            'type': 'relationship_node',
                            'properties': entity_info.get('properties', {}),
                            'input_label': input_label,
                            'is_a': is_a
                        })
                        
                        # Add edges from sources and to targets with meaningful names
                        for source in sources:
                            G.add_edge(source, entity_type, 
                                     type='edge',
                                     label=f'PARTICIPATES_IN_{entity_type}',
                                     name=f'PARTICIPATES_IN_{entity_type}',
                                     is_a=is_a)
                        for target in targets:
                            G.add_edge(entity_type, target, 
                                     type='edge',
                                     label=f'INVOLVES_{target}',
                                     name=f'INVOLVES_{target}',
                                     is_a=is_a)
                    else:
                        # This is a pure edge - create direct connections
                        edge_label = entity_info.get('label_as_edge', entity_type)
                        for source in sources:
                            for target in targets:
                                G.add_edge(source, target, 
                                         type='edge',
                                         label=edge_label,
                                         name=entity_type,
                                         is_a=is_a)
            
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
            
            # Create traces for nodes and edges
            node_trace = {
                'x': [], 'y': [], 
                'text': [],  # Node labels (simple names)
                'hovertext': [],  # Detailed hover information
                'mode': 'markers+text',
                'textposition': 'top center',
                'marker': {'size': 20, 'color': '#1f77b4', 'line_width': 2},
                'name': 'Nodes'
            }
            
            edge_trace = {
                'x': [], 'y': [], 
                'text': [],  # Edge labels
                'hovertext': [],  # Detailed hover information
                'mode': 'lines+text',
                'textposition': 'middle center',
                'line': {'width': 1, 'color': '#888'},
                'name': 'Edges'
            }
            
            # Collect node information
            for node, data in G.nodes(data=True):
                x, y = pos[node]
                node_trace['x'].append(x)
                node_trace['y'].append(y)
                
                # Simple label is just the node name
                node_trace['text'].append(node)
                
                # Create detailed hover text
                props = data.get('properties', {})
                input_label = data.get('input_label', '')
                is_a = data.get('is_a', '')
                hover_text = [
                    f"Name: {node}",
                    f"Label: {input_label}",
                ]
                if is_a:
                    if isinstance(is_a, list):
                        hover_text.append(f"Is a: {', '.join(is_a)}")
                    else:
                        hover_text.append(f"Is a: {is_a}")
                if props:
                    hover_text.append(f"Properties: {list(props.keys())}")
                
                node_trace['hovertext'].append("<br>".join(hover_text))
            
            # Collect edge information
            edge_labels = {}  # Store edge labels for positioning
            edge_x = []
            edge_y = []
            edge_text = []
            edge_text_pos = []
            edge_hovertext = []
            
            for source, target, data in G.edges(data=True):
                # Get positions
                x0, y0 = pos[source]
                x1, y1 = pos[target]
                
                if source == target:
                    # Self-relationship: create a circular arc
                    radius = 0.15  # Size of the arc
                    center_x = x0
                    center_y = y0 + radius
                    
                    # Create points for a smooth arc
                    t = np.linspace(0, 2*np.pi, 50)
                    arc_x = center_x + radius * np.cos(t)
                    arc_y = center_y + radius * np.sin(t)
                    
                    edge_x.extend(list(arc_x) + [None])
                    edge_y.extend(list(arc_y) + [None])
                    
                    # Position label above the arc
                    label_x = center_x
                    label_y = center_y + radius
                else:
                    # Regular edge
                    edge_x.extend([x0, x1, None])
                    edge_y.extend([y0, y1, None])
                    
                    # Position label at midpoint
                    label_x = (x0 + x1) / 2
                    label_y = (y0 + y1) / 2 + 0.05  # Slight offset above the line
                
                # Create edge label and hover text
                label = data.get('label', '')
                name = data.get('name', '')
                is_a = data.get('is_a', '')
                
                # Add label position
                edge_text.append(name)
                edge_text_pos.append([label_x, label_y])
                
                # Detailed hover text
                hover_text = [f"Name: {name}"]
                if label:
                    hover_text.append(f"Label: {label}")
                if is_a:
                    if isinstance(is_a, list):
                        hover_text.append(f"Is a: {', '.join(is_a)}")
                    else:
                        hover_text.append(f"Is a: {is_a}")
                edge_hovertext.append("<br>".join(hover_text))
            
            # Create figure
            traces = []
            
            # Add edge lines
            traces.append(go.Scatter(
                x=edge_x,
                y=edge_y,
                mode='lines',
                line={'width': 1, 'color': '#888'},
                hoverinfo='none',
                name='Edges',  # Add name for legend
                showlegend=True  # Show in legend
            ))
            
            # Add edge labels separately
            for i in range(len(edge_text)):
                if edge_text[i]:  # Only add if there's a label
                    traces.append(go.Scatter(
                        x=[edge_text_pos[i][0]],
                        y=[edge_text_pos[i][1]],
                        mode='text',
                        text=[edge_text[i]],
                        textposition='middle center',
                        hovertext=[edge_hovertext[i]],
                        hoverinfo='text',
                        showlegend=False,
                        name=f'Edge Label {i+1}'  # Name for potential future use
                    ))
            
            # Add node trace
            traces.append(go.Scatter(
                x=node_trace['x'],
                y=node_trace['y'],
                mode=node_trace['mode'],
                marker=node_trace['marker'],
                text=node_trace['text'],
                hovertext=node_trace['hovertext'],
                hoverinfo='text',
                textposition=node_trace['textposition'],
                name='Nodes',
                showlegend=True  # Explicitly show in legend
            ))
            
            # Create figure with improved legend
            fig = go.Figure(
                data=traces,
                layout=go.Layout(
                    showlegend=True,
                    hovermode='closest',
                    margin=dict(b=20, l=5, r=5, t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="right",
                        x=0.99,
                        bgcolor='rgba(50, 50, 50, 0.9)',
                        bordercolor='rgba(200, 200, 200, 0.5)',
                        borderwidth=2,
                        itemsizing='constant',
                        font=dict(
                            size=12,
                            color='white'
                        )
                    ),
                    plot_bgcolor='rgba(0, 0, 0, 0)',  # Transparent background
                    paper_bgcolor='rgba(0, 0, 0, 0)'  # Transparent background
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            logger.error(f"Error visualizing schema: {str(e)}")
            st.error(f"Error visualizing schema: {str(e)}")

    def edit_node_properties(config: dict, node_type: str):
        """Edit properties of a selected node type."""
        try:
            if node_type not in config:
                config[node_type] = {'properties': {}}
            
            properties = config[node_type].get('properties', {})
            
            st.subheader(f"Properties for {node_type}")
            
            # Add new property
            new_prop = st.text_input("Add new property:")
            if new_prop and new_prop not in properties:
                properties[new_prop] = 'string'  # default type in simple format
            
            # Edit existing properties
            for prop in list(properties.keys()):
                col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                with col1:
                    st.text(prop)
                with col2:
                    # Handle both simple string type and dict format
                    current_type = (properties[prop].get('type', properties[prop]) 
                                  if isinstance(properties[prop], dict) 
                                  else properties[prop])
                    
                    prop_type = st.selectbox(
                        "Type",
                        options=['string', 'integer', 'float', 'boolean'],
                        key=f"{node_type}_{prop}_type",
                        index=['string', 'integer', 'float', 'boolean'].index(current_type)
                    )
                    
                    # Get existing description if any
                    existing_desc = (properties[prop].get('description', '') 
                                   if isinstance(properties[prop], dict) 
                                   else '')
                    
                with col3:
                    # Optional description field
                    description = st.text_input(
                        "Description (optional)",
                        value=existing_desc,
                        key=f"{node_type}_{prop}_description",
                        placeholder="Enter property description..."
                    )
                    
                    # Update property format based on whether there's a description
                    if description:
                        properties[prop] = {
                            'type': prop_type,
                            'description': description
                        }
                    else:
                        # Use simple format if no description
                        properties[prop] = prop_type
                        
                with col4:
                    if st.button("Delete", key=f"delete_{node_type}_{prop}"):
                        del properties[prop]
            
            config[node_type]['properties'] = properties
        except Exception as e:
            logger.error(f"Error editing node properties: {str(e)}")
            st.error(f"Error editing node properties: {str(e)}")

    def edit_relationships(config: dict, source_type: str):
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