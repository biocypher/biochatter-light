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

def to_pascal_case(text: str) -> str:
    """Convert a space-separated string to PascalCase."""
    return ''.join(word.capitalize() for word in text.split())

def normalize_class_name(text: str) -> str:
    """Normalize a class name to lowercase sentence case."""
    # Replace dashes and underscores with spaces
    text = text.replace('-', ' ').replace('_', ' ')
    # Convert to lowercase
    text = text.lower()
    # Remove extra spaces
    text = ' '.join(text.split())
    return text

def validate_class_name(text: str) -> tuple[bool, str]:
    """Validate a class name and return (is_valid, message)."""
    if not text:
        return False, "Name cannot be empty"
    if text != text.lower():
        return False, "Name should be in lowercase"
    if '-' in text or '_' in text:
        return False, "Use spaces instead of dashes or underscores"
    return True, ""

def create_toy_schema() -> dict:
    """Create a toy schema demonstrating all BioCypher schema features."""
    return {
        "person": {
            "represented_as": "node",
            "properties": {
                "name": "string",
                "age": "integer",
                "email": {
                    "type": "string",
                    "description": "Primary contact email address for the person"
                }
            },
            "input_label": "PERSON_ID",  # Example of database ID column
            "is_a": "agent"
        },
        "project manager": {
            "represented_as": "node",
            "properties": {
                "name": "string",
                "certification": {
                    "type": "string",
                    "description": "Project management certification (e.g., PMP, PRINCE2)"
                },
                "experience years": {
                    "type": "integer",
                    "description": "Years of project management experience"
                }
            },
            "input_label": "manager_type",  # Example of raw data column name
            "is_a": "person"
        },
        "project": {
            "represented_as": "node",
            "properties": {
                "name": "string",
                "budget": {
                    "type": "float",
                    "description": "Total allocated budget in the project's base currency"
                },
                "status": {
                    "type": "string",
                    "description": "Current project status (e.g., planned, active, completed, on-hold)"
                }
            },
            "input_label": "project_id"  # Example of database ID
        },
        "manages": {
            "represented_as": "edge",
            "source": "project manager",  # Changed from person to project manager
            "target": "project",  # Now only manages projects
            "properties": {
                "start date": {
                    "type": "string",
                    "description": "Date when the manager started managing this project (YYYY-MM-DD)"
                },
                "responsibility level": {
                    "type": "string",
                    "description": "Level of management responsibility (e.g., lead, assistant, interim)"
                }
            },
            "input_label": "project_management",  # Example of a database relation
            "is_a": "management relation"
        },
        "organization": {
            "represented_as": "node",
            "properties": {
                "name": "string",
                "founded year": {
                    "type": "integer",
                    "description": "Year when the organization was officially established"
                },
                "location": {
                    "type": "string",
                    "description": "Primary headquarters location or main office address"
                }
            },
            "input_label": "org.name",  # Example of dotted notation from JSON
            "is_a": "institution"
        },
        "works for": {
            "represented_as": "edge",
            "source": "person",
            "target": "organization",
            "properties": {
                "start date": {
                    "type": "string",
                    "description": "Date when the person started working for the organization (YYYY-MM-DD)"
                },
                "role": {
                    "type": "string",
                    "description": "Job title or position within the organization"
                }
            },
            "input_label": "employment_relation",
            "is_a": "employment"
        },
        "knows": {
            "represented_as": "edge",
            "source": "person",
            "target": "person",
            "properties": {
                "since": {
                    "type": "string",
                    "description": "Date when the relationship was established (YYYY-MM-DD)"
                },
                "relationship type": {
                    "type": "string",
                    "description": "Nature of the relationship (e.g., colleague, friend, mentor)"
                }
            },
            "input_label": "Knows",
            "is_a": "social relation"
        },
        "collaboration": {
            "represented_as": "node",
            "source": ["person", "organization"],
            "target": "project",
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
            "input_label": "Collaboration",
            "is_a": "partnership"
        }
    }

def update_schema(new_config: dict):
    """Global function to update schema state."""
    ss['schema_config'] = dict(new_config)  # Create a deep copy
    st.rerun()  # Ensure UI reflects changes

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
        
        # Initialize schema state tracking
        if 'schema_initialized' not in ss:
            ss['schema_initialized'] = False
        
        # Schema initialization section
        if not ss['schema_initialized']:
            st.info("Please initialize your schema by either uploading a YAML file or using the toy dataset.")
            
            col1, col2 = st.columns(2)
            with col1:
                uploaded_file = st.file_uploader(label="Upload BioCypher schema configuration (YAML)", type=['yaml', 'yml'])
                if uploaded_file is not None:
                    logger.info(f"Loading schema config from uploaded file: {uploaded_file.name}")
                    new_config = yaml.safe_load(uploaded_file)
                    ss['schema_config'] = new_config
                    ss['schema_initialized'] = True
                    st.rerun()
            
            with col2:
                if st.button("Use Toy Dataset", use_container_width=True):
                    logger.info("Initializing with toy schema")
                    ss['schema_config'] = create_toy_schema()
                    ss['schema_initialized'] = True
                    st.rerun()
            
            # Return early if schema not initialized
            if not ss['schema_initialized']:
                return
        
        # Create a working copy of the schema
        config = dict(ss['schema_config'])
        
        # Display schema reset notice and save functionality
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info("⚠️ To start with a new schema, please reset the app.")
        
        with col2:
            # Save configuration filename input and button
            save_path = st.text_input("Save as:", value="schema_config.yaml", label_visibility="collapsed")
            if save_path and st.button("Save", use_container_width=True):
                try:
                    logger.info(f"Saving schema config to: {save_path}")
                    save_schema_config(ss['schema_config'], Path(save_path))
                    st.success(f"Configuration saved to {save_path}")
                except Exception as e:
                    logger.error(f"Error saving configuration: {str(e)}")
                    st.error(f"Error saving configuration: {str(e)}")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["Graph View", "Schema Editor", "Ontology Mapping", "YAML Preview"])
        
        with tab1:
            st.subheader("Schema Visualization")
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
                        new_entity = st.text_input(
                            "Entity class name:",
                            help="Enter the ontology class name in lowercase. Use spaces instead of dashes or underscores."
                        )
                        if new_entity:
                            normalized = normalize_class_name(new_entity)
                            if normalized != new_entity:
                                st.info(f"Suggested name: {normalized}")
                            
                            is_valid, message = validate_class_name(normalized)
                            if not is_valid:
                                st.warning(message)
                        
                        input_label = st.text_input(
                            "Input label (from raw data):",
                            help="Enter the label as it appears in your raw data"
                        )
                    
                    with col2:
                        entity_type = st.selectbox(
                            "Type",
                            options=['node', 'edge'],
                            key='new_entity_type'
                        )
                    
                    if new_entity and st.button("Add Entity"):
                        normalized = normalize_class_name(new_entity)
                        is_valid, message = validate_class_name(normalized)
                        
                        if is_valid:
                            if normalized not in config:
                                new_config = dict(config)
                                new_config[normalized] = {
                                    'represented_as': entity_type,
                                    'properties': {},
                                    'input_label': input_label if input_label else normalized
                                }
                                update_schema(new_config)
                                st.success(f"Added {entity_type}: {normalized}")
                            else:
                                st.error(f"Entity {normalized} already exists")
                        else:
                            st.error(message)
                
                with edit_tab2:
                    st.subheader("Add New Relationship")
                    col1, col2 = st.columns(2)
                    with col1:
                        source = st.selectbox("Source entity:", options=list(config.keys()))
                        target = st.selectbox("Target entity:", options=list(config.keys()))
                    with col2:
                        rel_type = st.text_input(
                            "Relationship class name:",
                            help="Enter the ontology class name in lowercase. Use spaces instead of dashes or underscores."
                        )
                        input_label = st.text_input(
                            "Input label (from raw data):",
                            help="Enter the label as it appears in your raw data (e.g., column name, relation type, etc.)"
                        )
                    
                    if source and target and rel_type and st.button("Add Relationship"):
                        normalized = normalize_class_name(rel_type)
                        is_valid, message = validate_class_name(normalized)
                        
                        if is_valid:
                            if normalized not in config:
                                config[normalized] = {
                                    'represented_as': 'edge',
                                    'source': source,
                                    'target': target,
                                    'properties': {},
                                    'input_label': input_label if input_label else normalized
                                }
                                st.success(f"Added relationship: {normalized}")
                            else:
                                st.error(
                                    f"Relationship {normalized} already exists. "
                                    "If you want to modify it, use the Modify Relationships tab."
                                )
                        else:
                            st.error(message)
                
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
                        options=edges if edges else ['No edges available'],
                        key='modify_edge_selector'
                    )
                    if selected_edge and selected_edge != 'No edges available':
                        st.subheader("Edge Configuration")
                        col1, col2 = st.columns(2)
                        
                        # Get current source and target
                        current_source = config[selected_edge].get('source', [])
                        current_target = config[selected_edge].get('target', [])
                        
                        # Convert to list if not already
                        if isinstance(current_source, str):
                            current_source = [current_source]
                        if isinstance(current_target, str):
                            current_target = [current_target]
                        
                        # Ensure current values exist in options
                        available_nodes = list(config.keys())
                        current_source = [s for s in current_source if s in available_nodes]
                        current_target = [t for t in current_target if t in available_nodes]
                        
                        with col1:
                            # Multi-select for sources
                            source = st.multiselect(
                                "Source entities",
                                options=available_nodes,
                                default=current_source,
                                key=f"{selected_edge}_source"
                            )
                            # Store as string if single value, list if multiple
                            config[selected_edge]['source'] = source[0] if len(source) == 1 else source
                            
                        with col2:
                            # Multi-select for targets
                            target = st.multiselect(
                                "Target entities",
                                options=available_nodes,
                                default=current_target,
                                key=f"{selected_edge}_target"
                            )
                            # Store as string if single value, list if multiple
                            config[selected_edge]['target'] = target[0] if len(target) == 1 else target
                        
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
                            
                            # Show references to this element
                            references = []
                            for k, v in config.items():
                                if k == element_to_delete:
                                    continue
                                if isinstance(v.get('source'), str) and v['source'] == element_to_delete:
                                    references.append(f"'{k}' uses this as source")
                                elif isinstance(v.get('source'), list) and element_to_delete in v['source']:
                                    references.append(f"'{k}' uses this as source")
                                if isinstance(v.get('target'), str) and v['target'] == element_to_delete:
                                    references.append(f"'{k}' uses this as target")
                                elif isinstance(v.get('target'), list) and element_to_delete in v['target']:
                                    references.append(f"'{k}' uses this as target")
                                if v.get('is_a') == element_to_delete:
                                    references.append(f"'{k}' inherits from this")
                            
                            if references:
                                st.warning(
                                    "⚠️ This element is referenced by:\n" + 
                                    "\n".join(f"- {ref}" for ref in references)
                                )
                        
                        with col2:
                            # Initialize deletion state in session state if not present
                            if f"delete_{element_to_delete}" not in ss:
                                ss[f"delete_{element_to_delete}"] = False
                            
                            # First button to initiate deletion
                            if not ss[f"delete_{element_to_delete}"]:
                                if st.button("Delete", type="secondary", use_container_width=True, key=f"init_delete_{element_to_delete}"):
                                    ss[f"delete_{element_to_delete}"] = True
                                    st.rerun()
                            # Confirmation and cancel buttons
                            else:
                                if st.button("Cancel", type="secondary", use_container_width=True, key=f"cancel_delete_{element_to_delete}"):
                                    del ss[f"delete_{element_to_delete}"]
                                    st.rerun()
                                if st.button("Confirm Deletion", type="primary", use_container_width=True, key=f"confirm_delete_{element_to_delete}"):
                                    new_config = dict(config)
                                    
                                    # Update all references first
                                    for k, v in new_config.items():
                                        if k == element_to_delete:
                                            continue
                                        # Update source references
                                        if isinstance(v.get('source'), str):
                                            if v['source'] == element_to_delete:
                                                del v['source']
                                        elif isinstance(v.get('source'), list):
                                            if element_to_delete in v['source']:
                                                v['source'] = [s for s in v['source'] if s != element_to_delete]
                                                if len(v['source']) == 1:
                                                    v['source'] = v['source'][0]
                                                elif not v['source']:
                                                    del v['source']
                                        
                                        # Update target references
                                        if isinstance(v.get('target'), str):
                                            if v['target'] == element_to_delete:
                                                del v['target']
                                        elif isinstance(v.get('target'), list):
                                            if element_to_delete in v['target']:
                                                v['target'] = [t for t in v['target'] if t != element_to_delete]
                                                if len(v['target']) == 1:
                                                    v['target'] = v['target'][0]
                                                elif not v['source']:
                                                    del v['target']
                                        
                                        # Update is_a references
                                        if v.get('is_a') == element_to_delete:
                                            del v['is_a']
                                    
                                    # Then delete the element
                                    del new_config[element_to_delete]
                                    # Clear the deletion state
                                    del ss[f"delete_{element_to_delete}"]
                                    update_schema(new_config)
                                    st.success(f"Deleted {element_to_delete} and updated all references")
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
            
            # Second pass: Add inheritance edges
            for entity_type, entity_info in config.items():
                if isinstance(entity_info, dict):
                    is_a = entity_info.get('is_a', '')
                    if is_a and is_a in G:  # Only add edge if parent exists in graph
                        G.add_edge(entity_type, is_a, 
                                 type='inheritance',
                                 name='is_a',
                                 label='is_a')
            
            # Third pass: Process edges and relationship nodes
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

            # Use Kamada-Kawai layout for better edge routing
            # Then refine with spring layout for fine-tuning
            pos = nx.kamada_kawai_layout(G)
            pos = nx.spring_layout(
                G,
                pos=pos,  # Use Kamada-Kawai as initial positions
                k=1.5,    # Optimal distance between nodes
                iterations=50,  # More iterations for better convergence
                weight=None,  # Don't use edge weights
                scale=2.0     # Scale up the layout
            )
            
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
            
            # Separate edge traces for regular edges and inheritance
            edge_x = []
            edge_y = []
            edge_text = []
            edge_text_pos = []
            edge_hovertext = []
            
            inheritance_x = []
            inheritance_y = []
            inheritance_text = []
            inheritance_text_pos = []
            inheritance_hovertext = []
            
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
                    f"Input Label: {input_label}",
                    f"Output Label: {to_pascal_case(node)}",
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
            for source, target, data in G.edges(data=True):
                # Get positions
                x0, y0 = pos[source]
                x1, y1 = pos[target]
                
                # Determine if this is an inheritance edge
                is_inheritance = data.get('type') == 'inheritance'
                
                # Choose the appropriate lists based on edge type
                if is_inheritance:
                    edge_list_x = inheritance_x
                    edge_list_y = inheritance_y
                    text_list = inheritance_text
                    text_pos_list = inheritance_text_pos
                    hover_list = inheritance_hovertext
                else:
                    edge_list_x = edge_x
                    edge_list_y = edge_y
                    text_list = edge_text
                    text_pos_list = edge_text_pos
                    hover_list = edge_hovertext
                
                if source == target:
                    # Self-relationship: create a circular arc
                    height = 0.4  # Height of the loop
                    width = height * 0.2  # Make width 30% of height for better proportions
                    center_x = x0
                    center_y = y0 + height  # Center point at full radius height
                    
                    # Create points for a complete loop
                    t = np.linspace(0, 2*np.pi, 50)
                    arc_x = center_x + width * np.cos(t)  # Reduced width
                    arc_y = center_y + height * np.sin(t)  # Full height semicircle
                    
                    # Add the points
                    edge_list_x.extend(list(arc_x) + [None])
                    edge_list_y.extend(list(arc_y) + [None])
                    
                    # Position label at the top of the arc
                    label_x = center_x
                    label_y = y0 + 2 * height  # Position label at the top of the loop
                else:
                    # Regular edge
                    edge_list_x.extend([x0, x1, None])
                    edge_list_y.extend([y0, y1, None])
                    
                    # Position label at midpoint with slight offset
                    label_x = (x0 + x1) / 2
                    label_y = (y0 + y1) / 2 + 0.05
                
                # Create edge label and hover text
                label = data.get('label', '')
                name = data.get('name', '')
                is_a = data.get('is_a', '')
                
                text_list.append(name)
                text_pos_list.append([label_x, label_y])
                
                hover_text = [f"Name: {name}"]
                if label:
                    hover_text.append(f"Label: {label}")
                if is_a:
                    if isinstance(is_a, list):
                        hover_text.append(f"Is a: {', '.join(is_a)}")
                    else:
                        hover_text.append(f"Is a: {is_a}")
                hover_list.append("<br>".join(hover_text))
            
            # Create figure
            traces = []
            
            # Add regular edge lines
            if edge_x:  # Only add if there are regular edges
                traces.append(go.Scatter(
                    x=edge_x,
                    y=edge_y,
                    mode='lines',
                    line={'width': 1, 'color': '#888'},
                    hoverinfo='none',
                    name='Relationships',
                    showlegend=True
                ))
            
            # Add inheritance edge lines
            if inheritance_x:  # Only add if there are inheritance edges
                traces.append(go.Scatter(
                    x=inheritance_x,
                    y=inheritance_y,
                    mode='lines',
                    line={'width': 2, 'color': '#e41a1c', 'dash': 'dot'},  # Red, dotted line
                    hoverinfo='none',
                    name='Inheritance',
                    showlegend=True
                ))
            
            # Add regular edge labels
            for i in range(len(edge_text)):
                if edge_text[i]:
                    traces.append(go.Scatter(
                        x=[edge_text_pos[i][0]],
                        y=[edge_text_pos[i][1]],
                        mode='text',
                        text=[edge_text[i]],
                        textposition='middle center',
                        hovertext=[edge_hovertext[i]],
                        hoverinfo='text',
                        showlegend=False,
                        name=f'Edge Label {i+1}'
                    ))
            
            # Add inheritance edge labels
            for i in range(len(inheritance_text)):
                if inheritance_text[i]:
                    traces.append(go.Scatter(
                        x=[inheritance_text_pos[i][0]],
                        y=[inheritance_text_pos[i][1]],
                        mode='text',
                        text=[inheritance_text[i]],
                        textposition='middle center',
                        hovertext=[inheritance_hovertext[i]],
                        hoverinfo='text',
                        showlegend=False,
                        name=f'Inheritance Label {i+1}'
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
                showlegend=True
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
                    plot_bgcolor='rgba(0, 0, 0, 0)',
                    paper_bgcolor='rgba(0, 0, 0, 0)'
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
            
            properties = dict(config[node_type].get('properties', {}))
            
            st.subheader(f"Properties for {node_type}")
            
            new_prop = st.text_input(
                "Add new property:",
                key=f"new_prop_{node_type}"
            )
            if new_prop and new_prop not in properties:
                new_config = dict(config)
                new_config[node_type]['properties'] = dict(properties)
                new_config[node_type]['properties'][new_prop] = 'string'
                update_schema(new_config)
            
            for prop in list(properties.keys()):
                col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                with col1:
                    st.text(prop)
                with col2:
                    current_type = (properties[prop].get('type', properties[prop]) 
                                  if isinstance(properties[prop], dict) 
                                  else properties[prop])
                    
                    prop_type = st.selectbox(
                        "Type",
                        options=['string', 'integer', 'float', 'boolean'],
                        key=f"{node_type}_{prop}_type",
                        index=['string', 'integer', 'float', 'boolean'].index(current_type)
                    )
                    
                    if prop_type != current_type:
                        new_config = dict(config)
                        if isinstance(properties[prop], dict):
                            new_config[node_type]['properties'][prop]['type'] = prop_type
                        else:
                            new_config[node_type]['properties'][prop] = prop_type
                        update_schema(new_config)
                
                with col3:
                    existing_desc = (properties[prop].get('description', '') 
                                   if isinstance(properties[prop], dict) 
                                   else '')
                    
                    description = st.text_input(
                        "Description (optional)",
                        value=existing_desc,
                        key=f"{node_type}_{prop}_description",
                        placeholder="Enter property description..."
                    )
                    
                    if description != existing_desc:
                        new_config = dict(config)
                        if description:
                            new_config[node_type]['properties'][prop] = {
                                'type': prop_type,
                                'description': description
                            }
                        else:
                            new_config[node_type]['properties'][prop] = prop_type
                        update_schema(new_config)
                
                with col4:
                    if st.button("Delete", key=f"delete_{node_type}_{prop}"):
                        new_config = dict(config)
                        del new_config[node_type]['properties'][prop]
                        update_schema(new_config)
            
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