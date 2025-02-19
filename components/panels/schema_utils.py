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