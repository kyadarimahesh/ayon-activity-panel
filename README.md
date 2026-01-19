# AYON Activity Panel

Standalone Qt widget for displaying AYON version activities, comments, and status changes.

## Features

- Display version activities (comments, status changes)
- Create comments with attachments
- Update version status
- Version comparison (RV stack creation)
- Version switching via dropdown
- Progressive image loading
- Background thread processing
- Auto-updates via RV event system

## Installation

```bash
cd ayon-activity-panel/client
pip install -e .
```

## Usage

```python
from ayon_activity_panel import ActivityPanel

panel = ActivityPanel()
panel.set_project("MyProject")

version_data = {
    'version_id': 'uuid',
    'path': '/assets/character',
    'current_version': 'v003',
    'version_status': 'approved',
    'author': 'john.doe',
    'task_id': 'uuid'
}

panel.set_version('uuid', version_data)
```

## OpenRV Integration

Activity Panel automatically binds to RV events on initialization:

```python
panel = ActivityPanel(bind_rv_events=True)  # Default
```

### How It Works

1. **Loader fires event** when asset loads in RV
2. **RV event system** delivers `ayon_source_loaded` event
3. **Activity Panel** receives event and updates UI
4. **Navigation events** update panel when switching sources

### Event Flow

```
RV Loader Plugin
    ↓ fires ayon_source_loaded
RV Event System
    ↓
RVActivityPanelIntegration
    ↓ reads node metadata
ActivityPanel.set_version()
    ↓
UI updates with activities
```

### Bound Events

- `ayon_source_loaded` - Asset load
- `after-graph-view-change` - View switching
- `source-group-complete` - Source loading
- `frame-changed` - Frame navigation
- `key-down--(` / `)` - Stack navigation

## API

### Methods

- `set_version(version_id, version_data)` - Update panel
- `set_project(project_name)` - Change project
- `set_available_statuses(statuses)` - Set status options
- `refresh()` - Refresh activities
- `clear()` - Clear panel

### Signals

- `version_changed(version_id, version_data)`
- `comment_created(version_id)`

### Version Data Structure

```python
{
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
    'representations': [...]
}
```

## Architecture

```
ActivityPanel
├── Managers
│   ├── VersionDetailsManager
│   ├── ActivityDisplayManager
│   ├── RepresentationManager
│   ├── CommentHandler
│   ├── ComparisonManager
│   └── RVActivityPanelIntegration
├── API Services
│   ├── ActivityService
│   ├── VersionService
│   └── FileService
└── Workers
    └── ActivityWorker
```

## Performance

- **Debouncing**: 500ms for RV events
- **Version caching**: Skip if same version_id
- **Progressive loading**: Text first, images async
- **Background threads**: Activity fetching off main thread
