from src.schema.description import ClassContext

def build_class_xquery_context(class_details: ClassContext) -> str:
    """
    Constructs a context string for XQuery generation based on class details.

    Args:
        class_details (ClassDescription): An instance of ClassDescription containing details about the class.

    Returns:
        str: A formatted context string for XQuery generation.
    """
    context_parts = []
    
    if class_details.name:
        context_parts.append(f"Class Name: {class_details.name}")
    
    if class_details.template:
        context_parts.append(f"Template: {class_details.template}")
    
    if class_details.example_instances:
        instances_info = ', '.join(class_details.example_instances)
        context_parts.append(f"Instances: {instances_info}")
    
    context_string = "\n".join(context_parts)
    
    return context_string
