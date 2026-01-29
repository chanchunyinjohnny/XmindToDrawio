#!/usr/bin/env python3
"""
XMind to Draw.io Converter

Converts XMind mind map files to Draw.io format.
Reads from ./xmindInput and outputs to ./drawioOutput

Usage:
    python converter.py

The converter automatically creates input/output directories if they don't exist.
"""

import zipfile
import xml.etree.ElementTree as ET
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any


class XMindParser:
    """Parses XMind files and extracts mind map structure."""

    def __init__(self, xmind_path: str):
        self.xmind_path = xmind_path
        self.namespaces = {
            'xmap': 'urn:xmind:xmap:xmlns:content:2.0',
            'fo': 'http://www.w3.org/1999/XSL/Format'
        }
        self.is_json_format = False

    def parse(self) -> Optional[Any]:
        """Extract and parse content from XMind file (JSON or XML format)."""
        try:
            with zipfile.ZipFile(self.xmind_path, 'r') as zip_file:
                # Try content.json first (newer format)
                if 'content.json' in zip_file.namelist():
                    self.is_json_format = True
                    content = zip_file.read('content.json')
                    return json.loads(content)
                # Fall back to content.xml (older format)
                elif 'content.xml' in zip_file.namelist():
                    self.is_json_format = False
                    content = zip_file.read('content.xml')
                    return ET.fromstring(content)
        except Exception as e:
            print(f"Error parsing {self.xmind_path}: {e}")
        return None

    def get_root_topic(self, root: Any) -> Optional[Any]:
        """Find the root topic in the XMind structure."""
        if self.is_json_format:
            # JSON format: array of sheets
            if isinstance(root, list) and len(root) > 0:
                first_sheet = root[0]
                return first_sheet.get('rootTopic')
            return None
        else:
            # XML format: xmap-content -> sheet -> topic
            sheet = root.find('.//xmap:sheet', self.namespaces)
            if sheet is not None:
                return sheet.find('xmap:topic', self.namespaces)
            return None


class DrawioGenerator:
    """Generates Draw.io XML structure from mind map data."""

    def __init__(self):
        self.cell_id = 2  # Start at 2 because IDs 0 and 1 are reserved for default cells
        self.x_spacing = 250
        self.min_y_spacing = 120
        self.box_width = 120
        self.box_height = 60
        self.callout_width = 200
        self.callout_height = 60
        self.callout_offset_x = -50
        self.callout_offset_y = -80
        self.callout_spacing = 70

    def create_drawio_xml(self, root_topic: Any, is_json: bool, namespaces: Dict = None) -> ET.Element:
        """Create Draw.io XML structure from XMind topic tree."""
        # Create Draw.io root structure
        mxfile = ET.Element('mxfile', host='app.diagrams.net', version='21.0.0')
        diagram = ET.SubElement(mxfile, 'diagram', name='Page-1')
        mxGraphModel = ET.SubElement(diagram, 'mxGraphModel',
                                     dx='1426', dy='782', grid='1',
                                     gridSize='10', guides='1')
        root = ET.SubElement(mxGraphModel, 'root')

        # Add default cells
        ET.SubElement(root, 'mxCell', id='0')
        ET.SubElement(root, 'mxCell', id='1', parent='0')

        # Convert topic tree
        if root_topic is not None:
            if is_json:
                self._convert_json_topic(root_topic, root, parent_id='1',
                                        x=400, y=300, level=0)
            else:
                self._convert_xml_topic(root_topic, root, namespaces, parent_id='1',
                                       x=400, y=300, level=0)

        return mxfile

    def _calculate_subtree_height(self, topic: Dict) -> int:
        """Calculate the total height needed for a topic and all its descendants."""
        children = topic.get('children', {})
        attached_topics = children.get('attached', [])
        callout_topics = children.get('callout', [])

        # Base height for this node
        base_height = self.min_y_spacing

        # Add extra height for callouts (they appear above the topic)
        if callout_topics:
            base_height += len(callout_topics) * self.callout_spacing

        if not attached_topics:
            # Leaf node: return base height (including callout space)
            return base_height

        # Calculate total height needed for all children
        total_child_height = 0
        for child in attached_topics:
            total_child_height += self._calculate_subtree_height(child)

        # Return the maximum of children's total height or base height
        return max(total_child_height, base_height)

    def _convert_json_topic(self, topic: Dict, parent: ET.Element,
                            parent_id: str, x: int, y: int, level: int) -> str:
        """Recursively convert JSON format XMind topics to Draw.io cells."""
        # Get topic title
        title = topic.get('title', 'Topic')

        # Create cell ID
        current_id = str(self.cell_id)
        self.cell_id += 1

        # Create mxCell for this topic
        cell = ET.SubElement(parent, 'mxCell',
                            id=current_id,
                            value=title,
                            style=self._get_style(level),
                            vertex='1',
                            parent='1')

        # Add geometry
        geometry = ET.SubElement(cell, 'mxGeometry',
                                x=str(x),
                                y=str(y),
                                width=str(self.box_width),
                                height=str(self.box_height))
        geometry.set('as', 'geometry')

        # Process children topics
        children = topic.get('children', {})

        # Process attached children (regular child topics)
        attached_topics = children.get('attached', [])

        if attached_topics:
            # Calculate total height needed for all children
            total_height = sum(self._calculate_subtree_height(child) for child in attached_topics)

            # Start position for first child (centered around parent)
            current_y = y - (total_height / 2)

            for child_topic in attached_topics:
                # Calculate height needed for this child's subtree
                child_height = self._calculate_subtree_height(child_topic)

                # Position child at the center of its allocated space
                child_x = x + self.x_spacing
                child_y = current_y + (child_height / 2)

                # Convert child
                child_id = self._convert_json_topic(child_topic, parent, current_id,
                                                    child_x, child_y, level + 1)

                # Create connector
                self._create_connector(parent, current_id, child_id)

                # Move to next child position
                current_y += child_height

        # Process callout children (annotations/notes)
        callout_topics = children.get('callout', [])
        for idx, callout in enumerate(callout_topics):
            # Position callouts above the topic, stacked vertically
            callout_x = x + self.callout_offset_x
            callout_y = y + self.callout_offset_y - (idx * self.callout_spacing)

            # Convert callout
            callout_id = self._convert_json_callout(callout, parent, current_id,
                                                    callout_x, callout_y)

        return current_id

    def _convert_json_callout(self, callout: Dict, parent: ET.Element,
                              parent_id: str, x: int, y: int) -> str:
        """Convert JSON format callout (annotation) to Draw.io note/annotation."""
        # Get callout title
        title = callout.get('title', '')

        # Create cell ID
        current_id = str(self.cell_id)
        self.cell_id += 1

        # Use sticky note style for annotations - this clearly indicates it's a note
        # Using shape=note which is Draw.io's built-in note/annotation shape
        callout_style = ('shape=note;whiteSpace=wrap;html=1;'
                        'fillColor=#fff2cc;strokeColor=#d6b656;'
                        'fontSize=9;align=left;verticalAlign=top;'
                        'spacing=8;spacingLeft=12;spacingRight=12;spacingTop=8;'
                        'backgroundOutline=1;size=12;')

        # Create mxCell for callout annotation
        cell = ET.SubElement(parent, 'mxCell',
                            id=current_id,
                            value=title,
                            style=callout_style,
                            vertex='1',
                            parent='1')

        # Add geometry with relative positioning to parent
        geometry = ET.SubElement(cell, 'mxGeometry',
                                x=str(x),
                                y=str(y),
                                width=str(self.callout_width),
                                height=str(self.callout_height))
        geometry.set('as', 'geometry')

        # Create connector from parent to annotation (dashed line to show relationship)
        connector_id = str(self.cell_id)
        self.cell_id += 1

        connector = ET.SubElement(parent, 'mxCell',
                                 id=connector_id,
                                 value='',
                                 style='edgeStyle=none;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;dashed=1;strokeColor=#d6b656;strokeWidth=1;',
                                 edge='1',
                                 parent='1',
                                 source=parent_id,
                                 target=current_id)

        geometry = ET.SubElement(connector, 'mxGeometry', relative='1')
        geometry.set('as', 'geometry')

        return current_id

    def _calculate_xml_subtree_height(self, topic: ET.Element, namespaces: Dict) -> int:
        """Calculate the total height needed for an XML topic and all its descendants."""
        children = topic.find('xmap:children', namespaces)
        if children is None:
            return self.min_y_spacing

        child_topics = []
        for topics_container in children.findall('xmap:topics', namespaces):
            child_topics.extend(topics_container.findall('xmap:topic', namespaces))

        if not child_topics:
            return self.min_y_spacing

        # Calculate total height needed for all children
        total_height = sum(self._calculate_xml_subtree_height(child, namespaces)
                          for child in child_topics)

        return max(total_height, self.min_y_spacing)

    def _convert_xml_topic(self, topic: ET.Element, parent: ET.Element,
                           namespaces: Dict, parent_id: str,
                           x: int, y: int, level: int) -> str:
        """Recursively convert XML format XMind topics to Draw.io cells."""
        # Get topic title
        title_elem = topic.find('xmap:title', namespaces)
        title = title_elem.text if title_elem is not None and title_elem.text else 'Topic'

        # Create cell ID
        current_id = str(self.cell_id)
        self.cell_id += 1

        # Create mxCell for this topic
        cell = ET.SubElement(parent, 'mxCell',
                            id=current_id,
                            value=title,
                            style=self._get_style(level),
                            vertex='1',
                            parent='1')

        # Add geometry
        geometry = ET.SubElement(cell, 'mxGeometry',
                                x=str(x),
                                y=str(y),
                                width=str(self.box_width),
                                height=str(self.box_height))
        geometry.set('as', 'geometry')

        # Process children topics
        children = topic.find('xmap:children', namespaces)
        if children is not None:
            # Collect all child topics
            child_topics = []
            for topics_container in children.findall('xmap:topics', namespaces):
                child_topics.extend(topics_container.findall('xmap:topic', namespaces))

            if child_topics:
                # Calculate total height needed for all children
                total_height = sum(self._calculate_xml_subtree_height(child, namespaces)
                                  for child in child_topics)

                # Start position for first child (centered around parent)
                current_y = y - (total_height / 2)

                for child_topic in child_topics:
                    # Calculate height needed for this child's subtree
                    child_height = self._calculate_xml_subtree_height(child_topic, namespaces)

                    # Position child at the center of its allocated space
                    child_x = x + self.x_spacing
                    child_y = current_y + (child_height / 2)

                    # Convert child
                    child_id = self._convert_xml_topic(child_topic, parent, namespaces,
                                                       current_id, child_x, child_y, level + 1)

                    # Create connector
                    self._create_connector(parent, current_id, child_id)

                    # Move to next child position
                    current_y += child_height

        return current_id

    def _create_connector(self, parent: ET.Element, source_id: str, target_id: str):
        """Create a connector between two cells."""
        connector_id = str(self.cell_id)
        self.cell_id += 1

        # Use entity relation style which routes around shapes to avoid overlapping
        connector = ET.SubElement(parent, 'mxCell',
                                 id=connector_id,
                                 value='',
                                 style='edgeStyle=entityRelationEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;curved=1;strokeColor=#6c8ebf;strokeWidth=1;',
                                 edge='1',
                                 parent='1',
                                 source=source_id,
                                 target=target_id)

        geometry = ET.SubElement(connector, 'mxGeometry', relative='1')
        geometry.set('as', 'geometry')

    def _get_style(self, level: int) -> str:
        """Get cell style based on hierarchy level."""
        if level == 0:
            # Root node style - blue with bold text
            return 'rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=14;'
        elif level == 1:
            # First level children - light blue
            return 'rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=12;'
        else:
            # Deeper levels - also light blue to match XMind
            return 'rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontSize=11;'


class XMindToDrawioConverter:
    """Main converter class."""

    def __init__(self, input_dir: str = './xmindInput', output_dir: str = './drawioOutput'):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)

    def convert_all(self):
        """Convert all XMind files in input directory."""
        # Create input and output directories if they don't exist
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Find all XMind files
        xmind_files = list(self.input_dir.glob('*.xmind'))

        if not xmind_files:
            print(f"No XMind files found in '{self.input_dir}'")
            print("Please add XMind files to the xmindInput folder and run again.")
            return

        print(f"Found {len(xmind_files)} XMind file(s)")

        # Convert each file
        for xmind_file in xmind_files:
            self.convert_file(xmind_file)

    def convert_file(self, xmind_path: Path):
        """Convert a single XMind file to Draw.io format."""
        print(f"\nConverting: {xmind_path.name}")

        # Parse XMind file
        parser = XMindParser(str(xmind_path))
        root = parser.parse()

        if root is None:
            print(f"  Failed to parse {xmind_path.name}")
            return

        # Get root topic
        root_topic = parser.get_root_topic(root)
        if root_topic is None:
            print(f"  No root topic found in {xmind_path.name}")
            return

        # Generate Draw.io structure
        generator = DrawioGenerator()
        drawio_xml = generator.create_drawio_xml(root_topic, parser.is_json_format, parser.namespaces)

        # Save to file
        output_path = self.output_dir / f"{xmind_path.stem}.drawio"
        tree = ET.ElementTree(drawio_xml)
        ET.indent(tree, space='  ')  # Pretty print
        tree.write(output_path, encoding='utf-8', xml_declaration=True)

        print(f"  ✓ Saved to: {output_path}")


def main():
    """Main entry point."""
    print("XMind to Draw.io Converter")
    print("=" * 40)

    converter = XMindToDrawioConverter()
    converter.convert_all()

    print("\nConversion complete!")


if __name__ == '__main__':
    main()