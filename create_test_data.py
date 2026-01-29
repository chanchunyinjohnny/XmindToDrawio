#!/usr/bin/env python3
"""
Creates synthetic test XMind files for testing purposes.

Copyright (c) 2026 Johnny
Licensed under the MIT License - see LICENSE file for details.

Contains NO proprietary content - only generic test data.
"""

import json
import zipfile
from pathlib import Path


def create_test_xmind_json(output_path: str):
    """Create a minimal XMind file with JSON format (newer XMind)."""

    # Create minimal test content - generic only
    content = [
        {
            "id": "test-sheet-1",
            "class": "sheet",
            "rootTopic": {
                "id": "root-topic",
                "class": "topic",
                "title": "Test Project",
                "structureClass": "org.xmind.ui.logic.right",
                "children": {
                    "attached": [
                        {
                            "id": "child-1",
                            "title": "Module A",
                            "children": {
                                "callout": [
                                    {
                                        "id": "callout-1",
                                        "title": "This is a test annotation"
                                    }
                                ]
                            }
                        },
                        {
                            "id": "child-2",
                            "title": "Module B",
                            "children": {
                                "attached": [
                                    {
                                        "id": "grandchild-1",
                                        "title": "Sub-module B1"
                                    },
                                    {
                                        "id": "grandchild-2",
                                        "title": "Sub-module B2"
                                    }
                                ]
                            }
                        },
                        {
                            "id": "child-3",
                            "title": "测试中文内容",  # Test UTF-8 encoding
                            "children": {
                                "callout": [
                                    {
                                        "id": "callout-2",
                                        "title": "中文注释测试"
                                    }
                                ]
                            }
                        }
                    ]
                }
            }
        }
    ]

    # Create metadata
    metadata = {
        "creator": {
            "name": "Test System",
            "version": "1.0.0"
        }
    }

    manifest = {
        "file-entries": {
            "content.json": {},
            "metadata.json": {}
        }
    }

    # Create XMind file (ZIP archive)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('content.json', json.dumps(content, ensure_ascii=False, indent=2))
        zf.writestr('metadata.json', json.dumps(metadata, ensure_ascii=False, indent=2))
        zf.writestr('manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2))


def create_test_xmind_xml(output_path: str):
    """Create a minimal XMind file with XML format (older XMind)."""

    content_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<xmap-content xmlns="urn:xmind:xmap:xmlns:content:2.0" version="2.0">
    <sheet id="sheet1">
        <topic id="root">
            <title>XML Format Test</title>
            <children>
                <topics type="attached">
                    <topic id="topic1">
                        <title>Topic A</title>
                    </topic>
                    <topic id="topic2">
                        <title>Topic B</title>
                        <children>
                            <topics type="attached">
                                <topic id="topic3">
                                    <title>Subtopic B1</title>
                                </topic>
                            </topics>
                        </children>
                    </topic>
                </topics>
            </children>
        </topic>
    </sheet>
</xmap-content>'''

    metadata_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<meta xmlns="urn:xmind:xmap:xmlns:meta:2.0" version="2.0">
    <Author>
        <Name>Test</Name>
    </Author>
</meta>'''

    # Create XMind file (ZIP archive)
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('content.xml', content_xml)
        zf.writestr('meta.xml', metadata_xml)


def main():
    """Create test data files."""
    # Create test directories
    test_input = Path('./testData')
    test_output = Path('./testOutput')

    test_input.mkdir(exist_ok=True)
    test_output.mkdir(exist_ok=True)

    # Create test XMind files with generic content
    print("Creating synthetic test data...")
    create_test_xmind_json(str(test_input / 'test_sample.xmind'))
    create_test_xmind_xml(str(test_input / 'test_legacy.xmind'))

    print(f"\n✓ Test data created successfully!")
    print(f"  Input:  {test_input}/")
    print(f"  Output: {test_output}/")
    print("\nThese files contain ONLY synthetic test data.")
    print("No proprietary content is included.")


if __name__ == '__main__':
    main()
