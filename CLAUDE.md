# CLAUDE.md

## Project Overview
XmindToDrawio is a Python project for converting XMind mind map files to Draw.io format.
It reads XMind files from ./xmindInput folder, extracts their structure and content, and generates equivalent Draw.io files to ./drawioOutput folder.

**Important:** Proprietary XMind files in `xmindInput/`, `drawioOutput/`, and `xmindContent/` are excluded from version control via `.gitignore`. All tests use synthetic data only.

## Development Environment

### Virtual Environment Setup
The project uses Python 3.13 with a virtual environment located in `.venv/`.

Activate the virtual environment:
```bash
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

### Installing Dependencies

```bash
pip install -r requirements.txt
```

### Running the Converter

```bash
python converter.py
```

All XMind files in `./xmindInput` will be processed and corresponding Draw.io files will be created in `./drawioOutput`.

**Note:** The converter automatically creates `xmindInput` and `drawioOutput` directories if they don't exist (including nested paths).

### Running Tests

The test suite uses **synthetic test data only** - no proprietary files are included in tests.

```bash
python test_converter.py [optional_drawio_file]
```

The test suite automatically:
1. Creates synthetic test XMind files (if needed)
2. Converts them to Draw.io format
3. Validates the output

Tests validate:
- Directory creation (input/output directories including nested paths)
- No duplicate cell IDs
- Correct geometry attributes
- Callout annotations are included (as note shapes)
- No overlapping elements
- UTF-8 encoding works properly (Chinese characters)
- Valid XML structure
- Proper connector routing (not covering content)
- Both JSON format (XMind 8+) and XML format (legacy) support

### Creating Test Data

To regenerate synthetic test data:

```bash
python create_test_data.py
```

This creates generic test files in `testData/` directory.

## Architecture Notes

The converter uses only Python standard library (no external dependencies).

### Core Components

1. **XMindParser**: Extracts content from XMind files
   - Supports both JSON format (XMind 8+) and XML format (older versions)
   - Reads from `content.json` first, falls back to `content.xml`

2. **DrawioGenerator**: Creates Draw.io XML structure
   - Converts topics to mxCell elements with proper geometry
   - Handles both attached children (regular topics) and callout children (annotations)
   - Renders callouts as Draw.io note shapes (`shape=note`) rather than connected boxes
   - Uses recursive layout algorithm that calculates subtree heights to prevent overlaps

3. **XMindToDrawioConverter**: Orchestrates the conversion process

### File Format Considerations

- **XMind files**: ZIP archives containing either `content.json` (newer) or `content.xml` (older)
- **Draw.io files**: XML-based format with mxfile/diagram/mxGraphModel structure
- **Cell IDs**: IDs 0 and 1 are reserved for default cells; user content starts at ID 2
- **Geometry attributes**: Must use `as="geometry"` (not `as_`)

### Layout Algorithm

The converter uses a recursive layout algorithm:
- Calculates total height needed for each subtree (including callouts)
- Allocates vertical space proportionally based on child count
- Centers each topic within its allocated space
- Positions callouts above their parent topics with dashed connectors

### Style Mapping

- All topics: Light blue (#dae8fc) to match XMind
- Annotations/Callouts: Yellow (#fff2cc) note shapes (using Draw.io's `shape=note`)
- Topic connectors: Curved blue lines using entityRelationEdgeStyle to avoid overlapping content
- Annotation connectors: Dashed yellow lines connecting notes to their parent topics

### Known Issues Fixed

1. Duplicate IDs (starting at 0 instead of 2)
2. Incorrect geometry attribute (`as_` instead of `as`)
3. Missing callout/annotation content
4. Overlapping elements due to insufficient spacing
5. Connectors covering content boxes (now uses entityRelationEdgeStyle for proper routing)