# RV Integration Flow

## Architecture

```
OpenRV Loader Plugin
    ↓ fires event
RV Event System ("ayon_source_loaded")
    ↓ delivers to
RVActivityPanelIntegration
    ↓ reads node metadata
ActivityPanel.set_version()
    ↓ updates
UI with activities
```

## Event Flow

### 1. Asset Load

```python
# load_frames.py
def load(context, name, namespace, options):
    # Load media
    loaded_node = rv.commands.addSourceVerbose([filepath])
    
    # Build event data with versions
    event_data = build_event_data_with_versions(context, filepath, logger)
    
    # Store metadata in node
    _store_version_metadata(node, context, event_data)
    
    # Fire event
    rv.commands.sendInternalEvent("ayon_source_loaded", json.dumps(event_data))
```

### 2. Panel Receives Event

```python
# rv_integration_manager.py
def _on_ayon_source_loaded(event):
    data = json.loads(event.contents())
    
    row_data = {
        'version_id': data['version_id'],
        'task_id': data['task_id'],
        'path': data['path'],
        'current_version': data['current_version'],
        'versions': data['versions'],
        'all_product_versions': data['all_product_versions'],
        'version_status': data['version_status'],
        'author': data['author'],
        'representations': data['representations']
    }
    
    self.activity_panel.set_version(data['version_id'], row_data)
```

### 3. Navigation Updates

```python
# Bound RV events (auto-initialized)
rv.commands.bind("default", "global", "after-graph-view-change", ...)
rv.commands.bind("default", "global", "source-group-complete", ...)
rv.commands.bind("default", "global", "frame-changed", ...)
rv.commands.bind("default", "global", "key-down--(", ...)  # Stack backward
rv.commands.bind("default", "global", "key-down--)", ...)  # Stack forward

# On event → read node metadata → update panel
def _update_for_current_source():
    current_source = _get_current_source()
    metadata = _read_node_metadata(current_source)
    
    if metadata['version_id'] != self.current_version_id:
        self.activity_panel.set_version(metadata['version_id'], metadata)
```

## Node Metadata Storage

```python
# Stored in RV node properties (node.ayon.*)
{
    'version_id': 'uuid',
    'representation_id': 'uuid',
    'file_path': '/path/to/file.exr',
    'product_id': 'uuid',
    'product_name': 'renderMain',
    'task_id': 'uuid',
    'folder_path': '/assets/character',
    'version_name': 'v003',
    'version_status': 'approved',
    'author': 'john.doe',
    'project_name': 'MyProject',
    'versions': '["v001", "v002", "v003"]',  # JSON string
    'all_product_versions': '[...]',          # JSON string
    'representations': '[...]'                # JSON string
}
```

## Version Switching

```python
# User changes version dropdown → ComparisonManager creates stack
def _on_version_changed(new_version):
    # Get current source
    current_source = rv_integration.get_current_source_group()
    
    # Find new version data
    new_version_data = find_version_data(new_version)
    
    # Create comparison stack
    comparison_mgr.create_comparison_stack(
        old_version_data=self.current_version_data,
        new_version_data=new_version_data,
        existing_source=current_source
    )
    
    # Update panel
    self.set_version(new_version_data['version_id'], new_version_data)
```

## Loader Utils

```python
# loader_utils.py

def fetch_all_product_versions(project_name, product_id, logger):
    """GraphQL query for all versions of a product."""
    # Returns sorted list (descending)
    
def build_event_data_with_versions(context, filepath, logger):
    """Build complete event data with versions and representations."""
    all_product_versions = fetch_all_product_versions(...)
    versions = [f"v{v['version']:03d}" for v in all_product_versions]
    representations = get_representations(...)
    
    return {
        'version_id': version_id,
        'versions': versions,
        'all_product_versions': all_product_versions,
        'representations': representations,
        ...
    }
```

## Performance

- **Debouncing**: 500ms for navigation events
- **Version caching**: Skip update if same version_id
- **Progressive loading**: Text first, images async
- **Background threads**: Activity fetching off main thread

## Benefits

- **Decoupled**: OpenRV doesn't import Activity Panel
- **Automatic**: Panel updates without manual refresh
- **Reusable**: Works with any loader plugin
- **Graceful**: Fails silently if components missing
