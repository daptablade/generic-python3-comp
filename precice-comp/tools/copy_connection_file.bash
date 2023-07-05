#!/bin/bash

# cmd arguments
current_participant=$1 # "Calculix1" 
participant_to_component=$2 # '{"Calculix1":"beam-1", "Calculix2":"beam-2"}'

# fixed parameters
monitoring_dir="../editables/pvc_shared"
target_dir="../editables/pvc_shared_copy"
monitor_event="moved_to"
open_ports_url="http://{$BE_API_HOST}/be-api/v1/openports"
IFS="/" read -a fpath <<< $USER_FILES_PATH 
user=${fpath[-1]}

# monitor_event="modify" # for local debugging
# open_ports_url="http://127.0.0.1:5000/be-api/v1/openports" # for local debugging

inotifywait -mr $monitoring_dir -e $monitor_event | 
    while read dir action file; do 
        
        # read new connection file and extract port ID, Acceptor and Requester IDs
        sf="${dir}${file}" 
        echo "new connection file:${sf}"

        COUNTER=0
        declare -A connection

        while IFS= read -r line || [[ -n "$line" ]]; do 
            COUNTER=$[$COUNTER+1]
            if [  $COUNTER -eq 1 ]
            then
                IFS=":" read -a arr1 <<< $line
                connection["Port"]=${arr1[1]}
            fi
            if [  $COUNTER -eq 2 ]
            then
                IFS=',' read -a vars <<< $line
                for i in "${vars[@]}"; do
                    read a b <<< $( echo $i | awk '{$1=$1;print}' | awk -F': ' '{print $1" "$2}' )
                    connection[$a]=$b
                done
            fi
        done <  $sf
        
        msg_body=$(for key in "${!connection[@]}"; do
            echo "\"$key\""
            val="${connection[$key]}"
            if echo "$participant_to_component" | jq "." | jq --arg val $val -e 'has($val)' > /dev/null
            then
                component=$(echo $participant_to_component | jq ".$val")
                echo "$component"
            else
                echo "\"$val\""
            fi
        done | 
        jq -n 'reduce inputs as $i ({}; . + { ($i): input })')
        # echo $msg_body
        
        if [[ "$current_participant" == "${connection["Requester"]}" ]]
        then
            resp="be-api msg: "$(curl --silent --write-out ' status:'%{http_code}\\n --output - $open_ports_url -X POST -H "auth0token: $user" -H 'Content-Type: application/json' -d "${msg_body}") 
            echo $resp

            # resp_status=${resp:0-3}
            # if [[ $resp_status == "200" ]] # only copy file if be-api call was successful
            # then
            tf="$target_dir${dir:$(expr length $monitoring_dir)}${file}"
            mkdir -p "$target_dir${dir:$(expr length $monitoring_dir)}"
            cp $sf $tf
            echo "Copied file ${sf} to ${tf}"
            # fi
        fi

    done