#!/usr/bin/env python3
"""
Entry point script to run the AYON Activity Panel application.
For development purposes only.

NOTE: This script automatically configures paths to use AYON's bundled dependencies.
No additional pip installations needed if AYON is installed at the default location.
"""

import sys
import os
import json
import glob

os.environ["AYON_SERVER_URL"] = "http://localhost:5000/"
os.environ["AYON_API_KEY"] = "e6e865e4f0d8ce133ecec8ef26d9fa8a03348e4a7441aa16f6767b921a46734d"

# TODO: Remove the hardcoding of environment variables above before production use 

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
addons_dir = os.path.dirname(parent_dir)

ayon_install = r"C:\Program Files\Ynput\AYON 1.4.1"
dep_packages_dir = r"C:\Users\mahesh\AppData\Local\Ynput\AYON\dependency_packages"

# Read installed addon versions from addons.json
addons_json_path = os.path.join(addons_dir, "addons.json")
installed_addons = {}

if os.path.exists(addons_json_path):
    with open(addons_json_path, 'r') as f:
        addons_data = json.load(f)
        for addon_name, versions in addons_data.items():
            latest_version = max(versions.keys(), key=lambda v: [int(x) for x in v.split('.')])
            installed_addons[addon_name] = latest_version

# Build paths dynamically
paths_to_add = [
    os.path.join(ayon_install, "common"),
    os.path.join(ayon_install, "dependencies"),
]

# Add core vendor path first if core exists
if 'core' in installed_addons:
    core_vendor_path = os.path.join(addons_dir, f"core_{installed_addons['core']}", "ayon_core", "vendor", "python")
    paths_to_add.insert(0, core_vendor_path)

# Add all installed addons
for addon_name, version in installed_addons.items():
    addon_dir = os.path.join(addons_dir, f"{addon_name}_{version}")
    if os.path.exists(addon_dir):
        paths_to_add.append(addon_dir)

# Add dependency packages
if os.path.exists(dep_packages_dir):
    for dep_zip in glob.glob(os.path.join(dep_packages_dir, "ayon_*_windows.zip")):
        dep_path = os.path.join(dep_zip, "dependencies")
        if os.path.exists(dep_path):
            paths_to_add.append(dep_path)

for path in paths_to_add:
    if os.path.exists(path):
        sys.path.insert(0, path)

sys.path.insert(0, current_dir)

from qtpy.QtWidgets import QApplication, QMainWindow
from qtpy.QtGui import QIcon

try:
    from ayon_core.style import load_stylesheet, get_app_icon_path
except ImportError:
    load_stylesheet = None
    get_app_icon_path = None

from ayon_activity_panel.widget import ActivityPanel

if not os.environ.get("AYON_SERVER_URL"):
    print("WARNING: AYON_SERVER_URL not set. Please set environment variables.")
    print("Example: set AYON_SERVER_URL=http://localhost:5000")
    print("         set AYON_API_KEY=your_api_key")
    sys.exit(1)

if not os.environ.get("AYON_API_KEY"):
    print("WARNING: AYON_API_KEY not set. Please set environment variables.")
    sys.exit(1)


def run_version_mode():
    """Run Activity Panel with version ID (Review Browser mode)."""
    app = QApplication(sys.argv)
    app.setOrganizationName("AYON")
    app.setApplicationName("ActivityPanel")

    if load_stylesheet:
        app.setStyleSheet(load_stylesheet())

    if get_app_icon_path:
        app.setWindowIcon(QIcon(get_app_icon_path()))

    window = QMainWindow()
    window.setWindowTitle("AYON Activity Panel - Version Mode")

    panel = ActivityPanel(bind_rv_events=False)
    window.setCentralWidget(panel)

    panel.set_project("space_project")
    panel.set_version("59d2fdb600de11f1961ba002a5bd0d80")

    window.resize(800, 600)
    window.show()

    # Save splitter sizes on window close
    def on_close():
        panel._save_splitter_sizes()

    window.closeEvent = lambda event: (on_close(), event.accept())

    sys.exit(app.exec_())


def run_dcc_mode():
    """Run Activity Panel with task ID (DCC mode)."""
    import ayon_api

    app = QApplication(sys.argv)
    app.setOrganizationName("AYON")
    app.setApplicationName("ActivityPanel")

    if load_stylesheet:
        app.setStyleSheet(load_stylesheet())

    if get_app_icon_path:
        app.setWindowIcon(QIcon(get_app_icon_path()))

    window = QMainWindow()
    window.setWindowTitle("AYON Activity Panel - DCC Mode")

    panel = ActivityPanel(bind_rv_events=False)
    window.setCentralWidget(panel)

    # Build DCC mode version_data manually (no version_id key)
    project_name = "space_project"
    task_id = "b855b950f92411f0b3e737e68d3021cd"

    task = ayon_api.get_task_by_id(project_name, task_id)
    folder = ayon_api.get_folder_by_id(project_name, task['folderId'])

    version_data = {
        "project_name": project_name,
        "task_id": task_id,
        "task_name": task.get('name', 'N/A'),
        "task_type": task.get('taskType', 'N/A'),
        "version_status": task.get('status', 'N/A'),
        "path": folder.get('path', 'N/A'),
        "author": "N/A",
        "versions": [],
        "representations": []
    }

    panel.set_project(project_name)
    panel.set_version(task_id, version_data)

    window.resize(800, 600)
    window.show()

    # Save splitter sizes on window close
    def on_close():
        panel._save_splitter_sizes()

    window.closeEvent = lambda event: (on_close(), event.accept())

    sys.exit(app.exec_())


def main():
    # Hardcoded test mode: 'version' or 'dcc'
    mode = 'dcc'

    if mode == 'dcc':
        run_dcc_mode()
    else:
        run_version_mode()


if __name__ == "__main__":
    main()
