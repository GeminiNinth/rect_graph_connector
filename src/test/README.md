# Testing Guide for rect_graph_connector

This directory contains tests for the rect_graph_connector project. The tests are organized by component and use pytest as the testing framework.

## Test Structure

```
src/test/
├── conftest.py              # Common fixtures for all tests
├── gui/                     # Tests for GUI components
│   ├── test_canvas.py       # Tests for the Canvas widget
│   ├── controllers/         # Tests for controllers
│   │   └── test_mode_controller.py
│   └── rendering/           # Tests for rendering components
│       ├── test_renderers.py        # Original renderer tests
│       └── test_renderers_fixed.py  # Fixed renderer tests for UV environment
├── models/                  # Tests for data models
│   ├── test_graph.py        # Tests for the Graph class
│   ├── test_rect_node.py    # Tests for the RectNode class
│   └── test_connectivity.py # Tests for connectivity functions
└── utils/                   # Tests for utility functions
    ├── test_geometry.py     # Tests for geometry utilities
    └── test_file_handler.py # Tests for file handling utilities
```

## Running Tests

### Using the Unified Test Script

The project includes a unified test script (`run_tests.sh`) that provides flexible options for running tests:

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

### Using UV Directly

You can also run tests directly with UV:

```bash
# Set PYTHONPATH to include the src directory
export PYTHONPATH="$PWD/src"

# Run all tests
uv run -m pytest

# Run tests for a specific module
uv run -m pytest src/test/gui/

# Run a specific test file
uv run -m pytest src/test/models/test_graph.py

# Run tests with coverage
uv run -m pytest --cov=rect_graph_connector

# Run tests with coverage and use the .coveragerc configuration
uv run -m pytest --cov=rect_graph_connector --cov-config=.coveragerc
```

The project includes a `.coveragerc` file that configures coverage to store data in the `tmp/coverage` directory. This file is automatically created by the `run_tests.sh` script when running tests with coverage.

### Using VSCode

1. Open the Testing view by clicking the flask icon in the Activity Bar
2. You'll see a tree of all tests in the project
3. Click the play button next to a test, file, or directory to run those tests
4. Test results will be displayed with pass/fail indicators

## Coverage Targets

The project has the following coverage targets:

- Controllers: 90% or higher
- Canvas: 80% or higher
- Overall: 75% or higher

You can check the current coverage by running:

```bash
./run_tests.sh
```

For a detailed HTML report:

```bash
./run_tests.sh --html
```

The script will output clickable links to the coverage reports that you can open directly from your terminal:
```
HTML coverage report available at: file:///path/to/rect_graph_connector/tmp/coverage/html/index.html
```

Simply click on the link in your terminal to open the report in your browser. This feature works in most modern terminal emulators including GNOME Terminal, Konsole, iTerm2, and VSCode's integrated terminal.

### Coverage Files Organization

All coverage files are stored in the `tmp/coverage` directory:

- `.coverage`: Raw coverage data file
- `coverage.xml`: XML coverage report (generated with `--xml` option)
- `html/`: Directory containing HTML coverage reports (generated with `--html` option)

This organization keeps temporary test files separate from the main project files and makes cleanup easier.

You can also generate both HTML and XML reports at once:

```bash
./run_tests.sh --html --xml
```

Or use the `--full` option which generates both reports:

```bash
./run_tests.sh --full
```

Both commands will provide clickable links in the terminal output for easy access to the reports.

## PyQt Testing Considerations

The project uses PyQt5 for GUI components, which can cause issues when running tests in certain virtual environment setups. To address this:

1. We use UV to run tests, which helps avoid PyQt initialization issues
2. For problematic renderer tests, we have a fixed version (`test_renderers_fixed.py`) that uses mock objects

If you encounter issues with PyQt tests:
1. Try running with the `--ignore-renderers` option: `./run_tests.sh --ignore-renderers`
2. Use the fixed renderer tests: `./run_tests.sh --fixed-renderers`
3. Consider creating mock versions of widgets that don't require QApplication initialization

## Writing New Tests

When writing new tests:

1. Follow the existing structure and naming conventions
2. Use fixtures from `conftest.py` when possible
3. Follow the Arrange-Act-Assert pattern
4. Test both normal and edge cases
5. Keep tests independent of each other
6. Focus on testing one thing per test function
7. Use descriptive test names that explain what is being tested

Example test structure:

```python
def test_something():
    # Arrange - set up test data and conditions
    expected = 42
    
    # Act - perform the action being tested
    result = calculate_something()
    
    # Assert - check that the result matches expectations
    assert result == expected
```

## Mocking and Test Doubles

For components that depend on external resources or complex objects:

1. Use the `pytest-mock` fixture `mocker` to create mock objects
2. Use the `pytest-qt` fixtures for testing Qt components
3. Create custom fixtures in `conftest.py` for common test scenarios

Example of mocking:

```python
def test_file_saving(canvas, mocker):
    # Mock the file dialog
    mock_save = mocker.patch('PyQt5.QtWidgets.QFileDialog.getSaveFileName')
    mock_save.return_value = ('test.csv', '')
    
    # Call the function that uses the file dialog
    canvas.save_graph()
    
    # Verify the mock was called
    mock_save.assert_called_once()
```

## Debugging Tests

If a test fails:

1. Use the `-v` flag for more verbose output: `./run_tests.sh -v`
2. Use the `--pdb` flag to drop into the debugger on failure: `uv run -m pytest --pdb`
3. Add print statements with `print()` for debugging
4. In VSCode, set breakpoints and use the "Debug Test" option

## Continuous Integration

The tests are designed to work in a CI environment. The coverage reports can be used to track test coverage over time.