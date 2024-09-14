import os
import ast
import json
import networkx as nx
import matplotlib.pyplot as plt
from ontology import Ontology

# Function to extract imports from a single Python file
def extract_imports_from_file(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=file_path)

    imports = []

    # Traverse the AST to find import statements
    for node in ast.walk(tree):
        # Handling "import module" statements
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        
        # Handling "from module import ..." statements
        elif isinstance(node, ast.ImportFrom):
            if node.module is not None:  # Ignore relative imports (node.level > 0)
                imports.append(node.module)

    return imports

# Function to walk through a directory and gather all imports
def gather_imports_from_codebase(codebase_path):
    imports_graph = {}
    
    # Walk through the directory recursively
    for root, _, files in os.walk(codebase_path):
        for file in files:
            if file.endswith(".py"):  # Process only Python files
                file_path = os.path.join(root, file)
                module_name = os.path.relpath(file_path, codebase_path).replace(os.sep, ".")
                if len(module_name) > 3 and module_name[-3:].strip() == ".py":
                    
                    module_name = str(module_name[:-3])
                # Extract imports from this file
                imports = extract_imports_from_file(file_path)
                
                # Add the imports to the graph
                if module_name not in imports_graph:
                    imports_graph[module_name] = []
                imports_graph[module_name].extend(imports)
    
    return imports_graph


# Function to build the import graph and export it to JSON
def create_import_graph(codebase_path, output_json_path):
    imports_graph = gather_imports_from_codebase(codebase_path)
    
    # Create a directed graph using NetworkX
    G = nx.DiGraph()
    
    # Add edges based on the imports
    for module, dependencies in imports_graph.items():
        for dep in dependencies:
            G.add_edge(dep, module)
    
    # Convert the graph to a JSON-compatible format
    graph_data = nx.node_link_data(G)
    
    # Write the graph to a JSON file
    with open(output_json_path + ".json", "w", encoding="utf-8") as f:
        json.dump(graph_data, f, indent=4)
    
    print(f"Import graph exported to {output_json_path}")

    o = Ontology(G)
    o.create_visualization(output_json_path + ".html", show=True)
    visualize_graph(G)
    
def visualize_graph(G):
    plt.figure(figsize=(12, 12))  # Set the figure size
    
    # Create a layout for the nodes
    pos = nx.spring_layout(G, k=0.15, iterations=20)

    # Draw the nodes and edges
    nx.draw(G, pos, with_labels=True, node_size=3000, node_color='skyblue', 
            font_size=10, font_weight='bold', edge_color='gray', arrows=True)
    
    # Show the plot
    plt.title("Python Codebase Import Graph", size=15)
    plt.savefig("a.svg", format='svg', dpi=300)
    plt.close()


if __name__ == "__main__":
    import sys
    codebase_path = sys.argv[1]  # Replace with the path to your codebase
    output_json_path = sys.argv[2]

    create_import_graph(codebase_path, output_json_path)