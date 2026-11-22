#!/bin/bash
# Starts RViz in a clean environment without snap conflicts

# Clear the VS Code snap variables
unset XDG_CONFIG_DIRS_VSCODE_SNAP_ORIG
unset GDK_BACKEND_VSCODE_SNAP_ORIG
unset GIO_MODULE_DIR_VSCODE_SNAP_ORIG
unset XDG_DATA_HOME
unset GSETTINGS_SCHEMA_DIR
unset GTK_EXE_PREFIX
unset VSCODE_GIT_ASKPASS_NODE
unset GIT_ASKPASS
unset GSETTINGS_SCHEMA_DIR_VSCODE_SNAP_ORIG
unset GTK_IM_MODULE_FILE_VSCODE_SNAP_ORIG
unset GTK_PATH
unset GTK_PATH_VSCODE_SNAP_ORIG
unset LOCPATH
unset XDG_DATA_HOME_VSCODE_SNAP_ORIG
unset GTK_EXE_PREFIX_VSCODE_SNAP_ORIG
unset XDG_DATA_DIRS_VSCODE_SNAP_ORIG
unset VSCODE_GIT_ASKPASS_MAIN
unset XDG_DATA_DIRS
unset GTK_IM_MODULE_FILE
unset LOCPATH_VSCODE_SNAP_ORIG
unset GIO_MODULE_DIR
unset GIO_LAUNCHED_DESKTOP_FILE

# Remove the snap paths from PATH
export PATH="/opt/ros/humble/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Restore the ROS environment
source /opt/ros/humble/setup.bash

# Start RViz
exec rviz2 "$@"
