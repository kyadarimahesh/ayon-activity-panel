# Integration Guide

## Installation

```bash
cd ayon-activity-panel/client
pip install -e .
```

## Review Browser Integration

```python
from ayon_activity_panel import ActivityPanel

class ReviewBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Create panel (RV events disabled for browser)
        self.activity_panel = ActivityPanel(bind_rv_events=False)
        
        # Add as dock
        dock = QDockWidget("Version Info", self)
        dock.setWidget(self.activity_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        
        # Connect table selection
        self.tableView.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )
    
    def _on_selection_changed(self):
        row_data = self._get_selected_row_data()
        if row_data:
            self.activity_panel.set_version(
                row_data['version_id'], 
                row_data
            )
```

## OpenRV Integration

Activity Panel automatically integrates with RV when `bind_rv_events=True` (default).

### Menu Integration

```python
# In ayon-openrv/startup/ayon_menus/
from ayon_activity_panel import ActivityPanel
import rv.qtutils

def show_activity_panel():
    """Show activity panel docked to RV."""
    panel = ActivityPanel()  # Auto-binds to RV events
    
    rv_window = rv.qtutils.sessionWindow()
    dock = QDockWidget("AYON Activity Panel", rv_window)
    dock.setWidget(panel)
    rv_window.addDockWidget(Qt.RightDockWidgetArea, dock)
    dock.show()
```

### How It Works

**1. Loader fires event:**
```python
# load_frames.py
rv.commands.sendInternalEvent("ayon_source_loaded", json.dumps(event_data))
```

**2. Panel receives event:**
```python
# RVActivityPanelIntegration (auto-initialized)
def _on_ayon_source_loaded(event):
    data = json.loads(event.contents())
    self.activity_panel.set_version(data['version_id'], data)
```

**3. Navigation updates:**
```python
# Bound events update panel when switching sources
- after-graph-view-change
- source-group-complete
- frame-changed
- key-down--( / )
```

## Version Data Structure

```python
version_data = {
    'version_id': 'uuid',
    'task_id': 'uuid',
    'product_id': 'uuid',
    'product_name': 'renderMain',
    'path': '/assets/character',
    'current_version': 'v003',
    'versions': ['v001', 'v002', 'v003'],
    'all_product_versions': [...],  # Full GraphQL nodes
    'version_status': 'approved',
    'author': 'john.doe',
    'representations': [...],
    'current_representation_path': '/path/to/file.exr'
}
```

## Benefits

- **No mode switching** - Simple `set_version()` calls
- **Loose coupling** - Apps don't import each other
- **Auto-updates** - RV events handled automatically
- **Reusable** - Single implementation everywhere
