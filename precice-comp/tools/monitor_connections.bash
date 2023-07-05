#!/bin/bash

# fixed parameters
monitoring_dir="../editables/pvc_shared"
target_dir="../editables"

inotifywait -mr $monitoring_dir > "../editables/outputs/monitor_connections.log"