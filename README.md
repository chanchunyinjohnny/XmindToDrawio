# XMind to Draw.io Converter

A clean, simple Python converter that transforms XMind mind maps into Draw.io diagrams. Built with zero external dependencies using only Python standard library.

## Features

- ✅ **Zero Dependencies** - Uses only Python standard library
- ✅ **Dual Format Support** - Handles both modern (JSON) and legacy (XML) XMind formats
- ✅ **Complete Conversion** - Preserves topics, subtopics, and annotations
- ✅ **UTF-8 Support** - Properly handles Chinese, Japanese, Korean, and other languages
- ✅ **Smart Layout** - Automatic spacing calculation to prevent overlapping elements
- ✅ **Note Annotations** - Converts XMind callouts to Draw.io note shapes
- ✅ **Auto-Creation** - Automatically creates input/output directories

## Requirements

- Python 3.7+
- No external packages required!

## Installation

1. Clone or download this repository
2. That's it! No `pip install` needed.

```bash
cd XmindToDrawio
```

## Usage

### Basic Conversion

1. Place your XMind files in the `xmindInput/` folder
2. Run the converter:

```bash
python converter.py
```

3. Find your Draw.io files in the `drawioOutput/` folder

The converter automatically creates the input/output directories if they don't exist.

### Example Output

```
XMind to Draw.io Converter
========================================
Found 3 XMind file(s)

Converting: project.xmind
  ✓ Saved to: drawioOutput/project.drawio

Converting: notes.xmind
  ✓ Saved to: drawioOutput/notes.drawio

Conversion complete!
```

## Features in Detail

### Smart Layout Algorithm

The converter uses a recursive layout algorithm that:
- Calculates the space needed for each subtree
- Allocates vertical space proportionally
- Centers topics within their allocated space
- Positions annotations near their parent topics

### Style Mapping

- **Topics**: Light blue boxes with rounded corners
- **Annotations**: Yellow note shapes (sticky note style)
- **Connectors**: Curved blue lines that route around shapes

### Supported XMind Elements

| XMind Element | Draw.io Equivalent | Status |
|---------------|-------------------|---------|
| Root Topic | Centered topic with bold text | ✅ |
| Child Topics | Hierarchical topics | ✅ |
| Callouts/Notes | Note shapes | ✅ |
| UTF-8 Text | Full Unicode support | ✅ |
| Nested Topics | Multi-level hierarchy | ✅ |

## Testing

The project includes a comprehensive test suite that validates all conversions using synthetic data only.

### Run Tests

```bash
python test_converter.py
```

The test suite automatically:
1. Creates synthetic test data (no proprietary content)
2. Converts test files
3. Validates the output

### Create Test Data

To regenerate synthetic test files:

```bash
python create_test_data.py
```

### Test Coverage

- ✅ No duplicate cell IDs
- ✅ Correct geometry attributes
- ✅ Annotation inclusion (as note shapes)
- ✅ No overlapping elements
- ✅ UTF-8 encoding (Chinese characters)
- ✅ Valid XML structure
- ✅ Connector routing
- ✅ Both JSON and XML format support
- ✅ Directory auto-creation

## Project Structure

```
XmindToDrawio/
├── converter.py           # Main converter script
├── test_converter.py      # Comprehensive test suite
├── create_test_data.py    # Synthetic test data generator
├── requirements.txt       # Dependencies (none!)
├── README.md             # This file
├── CLAUDE.md             # Developer documentation
├── .gitignore            # Excludes proprietary files
│
├── xmindInput/           # Place your XMind files here (git-ignored)
├── drawioOutput/         # Converted Draw.io files appear here (git-ignored)
│
├── testData/             # Synthetic test XMind files (included)
└── testOutput/           # Test Draw.io output (included)
```

## How It Works

1. **Parse XMind Files** - Extracts content from ZIP archives
   - JSON format: `content.json` (XMind 8+)
   - XML format: `content.xml` (legacy)

2. **Build Topic Tree** - Recursively processes topics and annotations
   - Calculates layout positions
   - Handles nested hierarchies
   - Processes callouts as note shapes

3. **Generate Draw.io XML** - Creates valid Draw.io format
   - mxfile/diagram/mxGraphModel structure
   - Proper cell IDs and geometry
   - Note shapes for annotations

## Known Limitations

- Does not support XMind markers/icons
- Does not preserve XMind themes/colors (uses standard blue/yellow)
- Does not support XMind relationships (lines between non-parent topics)
- Does not support XMind boundaries or summaries

## Privacy & Security

**Important**: This project respects your privacy.

- Your XMind files in `xmindInput/` are **never committed** to version control
- All test data is **synthetic** and generic
- No proprietary content is included in the codebase

See `.gitignore` for excluded directories.

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `python test_converter.py`
2. No proprietary data is included
3. Code follows existing style (clean, simple, well-commented)
4. Use only Python standard library (no external dependencies)

## Architecture

For detailed architecture documentation, see [CLAUDE.md](CLAUDE.md).

Key components:
- **XMindParser** - Extracts content from XMind files
- **DrawioGenerator** - Creates Draw.io XML structure
- **XMindToDrawioConverter** - Orchestrates conversion

## License

[Add your license here]

## Acknowledgments

Built with Python standard library only. No external dependencies means:
- Easy installation
- Fast execution
- No security vulnerabilities from third-party packages
- Works anywhere Python runs

---

**Questions or Issues?** Open an issue on the repository.
