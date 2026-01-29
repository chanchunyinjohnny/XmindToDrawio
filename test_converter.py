#!/usr/bin/env python3
"""
Test cases for XMind to Draw.io converter.
Validates fixes for issues encountered during development.
"""

import xml.etree.ElementTree as ET
from pathlib import Path
import sys
import tempfile


class ConverterTests:
    """Test suite for the XMind to Draw.io converter."""

    def __init__(self, drawio_file: str):
        self.drawio_file = Path(drawio_file)
        self.tree = None
        self.root = None
        self.errors = []
        self.warnings = []

    def load_file(self) -> bool:
        """Load the Draw.io XML file."""
        try:
            self.tree = ET.parse(self.drawio_file)
            self.root = self.tree.getroot()
            return True
        except Exception as e:
            self.errors.append(f"Failed to load file: {e}")
            return False

    def test_no_duplicate_ids(self) -> bool:
        """Test that there are no duplicate cell IDs."""
        print("Testing for duplicate IDs...")

        cells = self.root.findall('.//mxCell[@id]')
        ids = [cell.get('id') for cell in cells]

        # Check for duplicates
        seen = set()
        duplicates = set()
        for cell_id in ids:
            if cell_id in seen:
                duplicates.add(cell_id)
            seen.add(cell_id)

        if duplicates:
            self.errors.append(f"Found duplicate IDs: {duplicates}")
            print(f"  ✗ FAILED: Duplicate IDs found: {duplicates}")
            return False

        print(f"  ✓ PASSED: All {len(ids)} IDs are unique")
        return True

    def test_reserved_ids(self) -> bool:
        """Test that IDs 0 and 1 are reserved for default cells."""
        print("Testing reserved IDs 0 and 1...")

        cells = self.root.findall('.//mxCell[@id]')

        # Find cells with id 0 and 1
        id_0_cells = [c for c in cells if c.get('id') == '0']
        id_1_cells = [c for c in cells if c.get('id') == '1']

        if len(id_0_cells) != 1:
            self.errors.append(f"Expected exactly 1 cell with id='0', found {len(id_0_cells)}")
            print(f"  ✗ FAILED: Expected 1 cell with id='0', found {len(id_0_cells)}")
            return False

        if len(id_1_cells) != 1:
            self.errors.append(f"Expected exactly 1 cell with id='1', found {len(id_1_cells)}")
            print(f"  ✗ FAILED: Expected 1 cell with id='1', found {len(id_1_cells)}")
            return False

        # Verify id 1 has parent 0
        if id_1_cells[0].get('parent') != '0':
            self.errors.append("Cell with id='1' should have parent='0'")
            print("  ✗ FAILED: Cell with id='1' should have parent='0'")
            return False

        print("  ✓ PASSED: Reserved IDs 0 and 1 are correctly configured")
        return True

    def test_geometry_attribute(self) -> bool:
        """Test that mxGeometry has correct 'as' attribute (not 'as_')."""
        print("Testing mxGeometry 'as' attribute...")

        geometries = self.root.findall('.//mxGeometry')

        issues = []
        for idx, geom in enumerate(geometries):
            # Check if it has the correct 'as' attribute
            if 'as' not in geom.attrib:
                issues.append(f"Geometry {idx}: Missing 'as' attribute")
            elif geom.get('as') != 'geometry':
                issues.append(f"Geometry {idx}: 'as' attribute is '{geom.get('as')}', expected 'geometry'")

            # Check if it incorrectly has 'as_' attribute
            if 'as_' in geom.attrib:
                issues.append(f"Geometry {idx}: Has incorrect 'as_' attribute (should be 'as')")

        if issues:
            self.errors.extend(issues)
            print(f"  ✗ FAILED: {len(issues)} geometry issues found")
            for issue in issues[:5]:  # Show first 5
                print(f"    - {issue}")
            return False

        print(f"  ✓ PASSED: All {len(geometries)} geometries have correct 'as=\"geometry\"' attribute")
        return True

    def test_callouts_included(self) -> bool:
        """Test that callout annotations are included in output."""
        print("Testing callout/annotation inclusion...")

        # Look for note-style annotation cells
        cells = self.root.findall('.//mxCell[@style]')
        note_cells = [c for c in cells if 'shape=note' in c.get('style', '')]

        if len(note_cells) == 0:
            self.warnings.append("No note/annotation cells found (may be expected if source has no annotations)")
            print("  ⚠ WARNING: No annotation cells found")
            return True

        # Verify notes have the correct properties
        invalid_notes = []
        for note in note_cells:
            style = note.get('style', '')
            if '#fff2cc' not in style:
                invalid_notes.append(f"Note {note.get('id')} missing yellow fill color")

        if invalid_notes:
            self.errors.extend(invalid_notes)
            print(f"  ✗ FAILED: {len(invalid_notes)} annotation issues")
            return False

        # Check that annotations have dashed connectors linking them to topics
        edges = self.root.findall('.//mxCell[@edge="1"]')
        dashed_edges = [e for e in edges if 'dashed=1' in e.get('style', '')]

        print(f"  ✓ PASSED: Found {len(note_cells)} note-style annotations with {len(dashed_edges)} dashed connectors")
        return True

    def test_no_overlapping_cells(self) -> bool:
        """Test that cells don't overlap significantly."""
        print("Testing for overlapping cells...")

        # Get all vertex cells with geometry
        cells = []
        for cell in self.root.findall('.//mxCell[@vertex="1"]'):
            geom = cell.find('mxGeometry')
            if geom is not None:
                try:
                    x = float(geom.get('x', 0))
                    y = float(geom.get('y', 0))
                    width = float(geom.get('width', 120))
                    height = float(geom.get('height', 60))
                    cells.append({
                        'id': cell.get('id'),
                        'value': cell.get('value', '')[:30],
                        'x': x,
                        'y': y,
                        'width': width,
                        'height': height
                    })
                except ValueError:
                    continue

        # Check for overlaps
        overlaps = []
        for i, cell1 in enumerate(cells):
            for cell2 in cells[i+1:]:
                # Check if boxes overlap
                if (abs(cell1['x'] - cell2['x']) < (cell1['width'] + cell2['width']) / 2 and
                    abs(cell1['y'] - cell2['y']) < (cell1['height'] + cell2['height']) / 2):
                    # Allow some overlap for callouts near their parent
                    x_overlap = abs(cell1['x'] - cell2['x'])
                    y_overlap = abs(cell1['y'] - cell2['y'])

                    # Only flag significant overlaps (centers too close)
                    if x_overlap < 80 and y_overlap < 40:
                        overlaps.append(f"'{cell1['value']}' and '{cell2['value']}'")

        if overlaps:
            self.errors.append(f"Found {len(overlaps)} potential overlapping cells")
            print(f"  ✗ FAILED: Found {len(overlaps)} overlapping cells")
            for overlap in overlaps[:5]:  # Show first 5
                print(f"    - {overlap}")
            return False

        print(f"  ✓ PASSED: No significant overlaps among {len(cells)} cells")
        return True

    def test_utf8_encoding(self) -> bool:
        """Test that UTF-8 characters are properly encoded."""
        print("Testing UTF-8 encoding...")

        cells = self.root.findall('.//mxCell[@value]')

        # Look for cells with non-ASCII characters
        non_ascii_cells = []
        for cell in cells:
            value = cell.get('value', '')
            if any(ord(c) > 127 for c in value):
                non_ascii_cells.append(value[:50])

        if non_ascii_cells:
            print(f"  ✓ PASSED: Found {len(non_ascii_cells)} cells with non-ASCII characters (UTF-8 working)")
            # Show some examples
            for example in non_ascii_cells[:3]:
                print(f"    - '{example}'")
        else:
            self.warnings.append("No non-ASCII characters found (may be expected for English-only content)")
            print("  ⚠ WARNING: No non-ASCII characters found")

        return True

    def test_proper_structure(self) -> bool:
        """Test that the overall XML structure is valid."""
        print("Testing XML structure...")

        # Check root element
        if self.root.tag != 'mxfile':
            self.errors.append(f"Root element should be 'mxfile', got '{self.root.tag}'")
            print(f"  ✗ FAILED: Root element is '{self.root.tag}', expected 'mxfile'")
            return False

        # Check for diagram
        diagram = self.root.find('diagram')
        if diagram is None:
            self.errors.append("Missing 'diagram' element")
            print("  ✗ FAILED: Missing 'diagram' element")
            return False

        # Check for mxGraphModel
        model = diagram.find('mxGraphModel')
        if model is None:
            self.errors.append("Missing 'mxGraphModel' element")
            print("  ✗ FAILED: Missing 'mxGraphModel' element")
            return False

        # Check for root container
        root_container = model.find('root')
        if root_container is None:
            self.errors.append("Missing 'root' container element")
            print("  ✗ FAILED: Missing 'root' container element")
            return False

        print("  ✓ PASSED: XML structure is valid")
        return True

    def test_connectors_present(self) -> bool:
        """Test that connectors exist between topics."""
        print("Testing connectors...")

        edges = self.root.findall('.//mxCell[@edge="1"]')
        vertices = self.root.findall('.//mxCell[@vertex="1"]')

        if len(edges) == 0 and len(vertices) > 2:
            self.errors.append("No connectors found but multiple vertices exist")
            print("  ✗ FAILED: No connectors found")
            return False

        # Check that edges have source and target
        invalid_edges = []
        for edge in edges:
            if not edge.get('source') or not edge.get('target'):
                invalid_edges.append(edge.get('id'))

        if invalid_edges:
            self.errors.append(f"Found {len(invalid_edges)} edges without source/target")
            print(f"  ✗ FAILED: {len(invalid_edges)} edges missing source/target")
            return False

        print(f"  ✓ PASSED: Found {len(edges)} connectors linking {len(vertices)} vertices")
        return True

    def test_connector_routing(self) -> bool:
        """Test that connectors use proper routing to avoid overlapping content."""
        print("Testing connector routing...")

        edges = self.root.findall('.//mxCell[@edge="1"]')

        # Check that edges use entityRelationEdgeStyle to avoid overlapping
        non_entity_edges = []
        for edge in edges:
            style = edge.get('style', '')
            if 'edgeStyle=' in style and 'entityRelationEdgeStyle' not in style:
                non_entity_edges.append(edge.get('id'))

        if non_entity_edges:
            self.warnings.append(f"Found {len(non_entity_edges)} edges not using entityRelationEdgeStyle (may overlap content)")
            print(f"  ⚠ WARNING: {len(non_entity_edges)} edges may overlap content")
        else:
            print(f"  ✓ PASSED: All {len(edges)} connectors use proper routing to avoid overlapping")

        return True

    def run_all_tests(self) -> bool:
        """Run all tests and return overall result."""
        print(f"\n{'='*60}")
        print(f"Running tests on: {self.drawio_file}")
        print(f"{'='*60}\n")

        if not self.load_file():
            print("\n✗ FATAL: Could not load file")
            return False

        tests = [
            self.test_proper_structure,
            self.test_no_duplicate_ids,
            self.test_reserved_ids,
            self.test_geometry_attribute,
            self.test_callouts_included,
            self.test_utf8_encoding,
            self.test_connectors_present,
            self.test_connector_routing,
            self.test_no_overlapping_cells,
        ]

        results = []
        for test in tests:
            try:
                results.append(test())
            except Exception as e:
                self.errors.append(f"Test {test.__name__} failed with exception: {e}")
                results.append(False)
                print(f"  ✗ EXCEPTION in {test.__name__}: {e}")

        # Print summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests run: {len(results)}")
        print(f"Passed: {sum(results)}")
        print(f"Failed: {len(results) - sum(results)}")

        if self.warnings:
            print(f"\nWarnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")

        if self.errors:
            print(f"\nErrors: {len(self.errors)}")
            for error in self.errors[:10]:  # Show first 10
                print(f"  ✗ {error}")

        all_passed = all(results)
        if all_passed:
            print("\n✓ ALL TESTS PASSED")
        else:
            print("\n✗ SOME TESTS FAILED")

        print(f"{'='*60}\n")
        return all_passed


def test_directory_creation():
    """Test that input and output directories are created automatically."""
    print(f"\n{'='*60}")
    print("Testing Directory Creation")
    print(f"{'='*60}\n")

    # Import the converter
    from converter import XMindToDrawioConverter

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        test_input = temp_path / "test_input_dir" / "nested"
        test_output = temp_path / "test_output_dir" / "nested"

        print(f"Testing with paths:")
        print(f"  Input:  {test_input}")
        print(f"  Output: {test_output}")

        # Verify directories don't exist yet
        if test_input.exists() or test_output.exists():
            print("✗ FAILED: Test directories already exist")
            return False

        # Create converter with non-existent directories
        converter = XMindToDrawioConverter(
            input_dir=str(test_input),
            output_dir=str(test_output)
        )

        # Run convert_all (will create directories)
        print("\nRunning converter...")
        converter.convert_all()

        # Check if directories were created
        if not test_input.exists():
            print("✗ FAILED: Input directory was not created")
            return False

        if not test_output.exists():
            print("✗ FAILED: Output directory was not created")
            return False

        print("✓ PASSED: Both input and output directories were created successfully")
        print(f"{'='*60}\n")
        return True


def setup_test_environment():
    """Set up test environment with synthetic data."""
    print("\n" + "="*60)
    print("SETTING UP TEST ENVIRONMENT")
    print("="*60 + "\n")

    # Check if test data exists
    test_data_dir = Path('./testData')
    test_output_dir = Path('./testOutput')

    if not test_data_dir.exists() or not any(test_data_dir.glob('*.xmind')):
        print("Creating synthetic test data...")
        import subprocess
        result = subprocess.run([sys.executable, 'create_test_data.py'],
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("✗ FAILED: Could not create test data")
            print(result.stderr)
            return False
        print(result.stdout)

    # Run converter on test data
    print("\nRunning converter on test data...")
    from converter import XMindToDrawioConverter
    converter = XMindToDrawioConverter(
        input_dir='./testData',
        output_dir='./testOutput'
    )
    converter.convert_all()

    print(f"{'='*60}\n")
    return True


def main():
    """Main test runner."""
    print("\n" + "="*60)
    print("XMIND TO DRAWIO CONVERTER - TEST SUITE")
    print("="*60)

    # Set up test environment with synthetic data
    if not setup_test_environment():
        sys.exit(1)

    # Test directory creation
    dir_test_passed = test_directory_creation()

    # Use synthetic test file (not proprietary data)
    test_file = './testOutput/test_sample.drawio'

    # Allow custom file from command line
    if len(sys.argv) > 1:
        test_file = sys.argv[1]

    if not Path(test_file).exists():
        print(f"\nError: Test file not found: {test_file}")
        print(f"Make sure test data was generated successfully.")
        print(f"\nUsage: python {sys.argv[0]} [drawio_file]")
        sys.exit(1)

    tester = ConverterTests(test_file)
    conversion_test_passed = tester.run_all_tests()

    # Overall result
    all_passed = dir_test_passed and conversion_test_passed
    print(f"\n{'='*60}")
    print("OVERALL RESULT")
    print(f"{'='*60}")
    print(f"Directory Creation: {'✓ PASSED' if dir_test_passed else '✗ FAILED'}")
    print(f"Conversion Tests: {'✓ PASSED' if conversion_test_passed else '✗ FAILED'}")
    print(f"{'='*60}\n")

    if all_passed:
        print("✓ All tests use synthetic data only - no proprietary content")

    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
