#!/bin/bash

# fixed parameters
monitoring_dir="../editables/pvc_shared"
target_dir="../editables/pvc_shared_copy"
monitor_event="delete"

inotifywait -mr $monitoring_dir -e $monitor_event | 
    while read dir action file; do 
        
        # read new connection file and extract port ID, Acceptor and Requester IDs
        sf="${dir}${file}" 
        
        tf="$target_dir${dir:$(expr length $monitoring_dir)}${file}"
        rm -rf $tf
        echo "deleted connection file or folder:${tf}"

    done > "../editables/outputs/connection_file_delete.log"