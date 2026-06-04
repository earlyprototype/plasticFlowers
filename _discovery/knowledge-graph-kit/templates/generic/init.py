#!/usr/bin/env python3
"""
Initialize research knowledge graph
Creates directory structure and empty entities.json
"""

import sys
import shutil
from pathlib import Path

# Add parent directory to path to import core
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.graph_manager import GraphManager


def init_research_graph():
    """Initialize research knowledge graph"""
    print("Initializing Research Knowledge Graph")
    print("=" * 50)
    
    # Load config and create graph manager
    gm = GraphManager('config.yaml')
    
    # Create directory structure
    paths = gm.config.get_paths()
    for key, path in paths.items():
        if key.endswith('_dir'):
            path_obj = Path(path)
            path_obj.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created: {path_obj}")
    
    # Save initial entities.json
    gm.save()
    print(f"✓ Created: {gm.entities_path}")
    
    # Copy universal viewer from core
    core_dir = Path(__file__).parent.parent.parent / 'core'
    core_viewer = core_dir / 'viewer.html'
    local_viewer = Path('viewer.html')
    if core_viewer.exists():
        shutil.copy(core_viewer, local_viewer)
        print(f"✓ Created: {local_viewer}")
    
    # Copy server files from core
    for filename in ['server.py', 'gemini_api_server.py', 'gemini_config.template.json']:
        core_file = core_dir / filename
        if core_file.exists():
            shutil.copy(core_file, Path(filename))
            print(f"✓ Created: {filename}")
    
    # Print stats
    stats = gm.graph_data['metadata']
    print(f"\n{'=' * 50}")
    print(f"Graph initialized!")
    print(f"Domain: {stats['domain']}")
    print(f"Version: {stats['version']}")
    print(f"\nEntity types:")
    for category, config in gm.config.get_entity_types().items():
        label = gm.config.get_entity_label(category, plural=True)
        print(f"  - {label}")
    
    print(f"\nNext steps:")
    print(f"  1. Add entities using graph_manager.py")
    print(f"  2. Or merge from existing file")
    print(f"  3. Start viewer: python server.py")
    print(f"{'=' * 50}\n")


if __name__ == "__main__":
    init_research_graph()

