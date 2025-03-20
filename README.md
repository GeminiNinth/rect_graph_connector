# Rectangular Graph Connector

A Python application for creating rectangular graph structures with a graphical user interface.

## Features

- Create rectangular node groups with customizable dimensions
- Drag and drop nodes to reposition them
- Create edges between nodes using right-click
- Group operations (rotation, deletion)
- Export graph structure to CSV format

### Components

- **RectNode**: Represents a rectangular node with position and size information
- **Graph**: Manages the graph structure, including nodes, edges, and groups
- **Canvas**: Handles visualization and user interactions
- **MainWindow**: Manages the application UI and user controls
- **FileHandler**: Handles CSV file operations
- **GeometryCalculator**: Provides geometric calculation utilities

## Requirements

- Python 3.12 or higher
- PyQt5 5.15.0 or higher

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/rect_graph_connector.git
cd rect_graph_connector
```

2. Install uv:
Follow the instructions on the [uv official installation guide](https://docs.astral.sh/uv/getting-started/installation/).


## Usage

Run the application:
```bash
uv run main.py
```

### Basic Operations

1. **Create Nodes**:
   - Enter the number of rows and columns in the input fields.
   - Click "Add" to create a rectangular group of nodes with the specified dimensions.

2. **Move Nodes**:
   - Left-click and drag nodes to reposition them within the canvas.
   - All nodes in a group move together, maintaining their relative positions.

3. **Create Edges**:
   - Right-click and drag from one node to another to initiate an edge.
   - Release the mouse button to finalize the edge creation.

4. **Group Operations**:
   - Select a group by clicking any node within it.
   - Use "Rotate Group" to rotate the selected group 90 degrees clockwise.
   - Use "Delete Group" to remove the selected group from the canvas.

5. **Export**:
   - Click "Export CSV" to save the current graph structure to a CSV file.
   - The exported file will be named "graph_output.csv" and saved in the project directory.

## Testing

The project includes a unified test script that provides flexible options for running tests.

### Running Tests

Use the `run_tests.sh` script to run tests with various options:

```bash
# Run all tests with default settings (UV and coverage)
./run_tests.sh

# Run tests without using UV
./run_tests.sh --no-uv

# Run a specific test file
./run_tests.sh src/test/models/test_rect_node.py

# Run tests in verbose mode
./run_tests.sh --verbose

# Generate HTML and XML coverage reports
./run_tests.sh --full

# Run all tests including fixed renderer tests
./run_tests.sh --all
```

For a complete list of options:
```bash
./run_tests.sh --help
```

### Coverage Targets

The project has the following coverage targets:
- Controllers: 90% or higher
- Canvas: 80% or higher
- Overall: 75% or higher

To view detailed coverage information:
```bash
# Generate HTML coverage report
./run_tests.sh --html
```

The script will output clickable links to the coverage reports that you can open directly from your terminal:
```
HTML coverage report available at: file:///path/to/rect_graph_connector/tmp/coverage/html/index.html
```

Simply click on the link in your terminal to open the report in your browser. This feature works in most modern terminal emulators including GNOME Terminal, Konsole, iTerm2, and VSCode's integrated terminal.

All coverage files are stored in the `tmp/coverage` directory:
- `.coverage`: Raw coverage data
- `coverage.xml`: XML coverage report
- `html/`: HTML coverage report directory

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the terms of the LICENSE file included in the repository.