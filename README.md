# GENERIC-PYTHON3-COMP

Dapta sample components with a generic python 3 interface. 
Each'dockerfile_...' folder contains the Dockerfile required to build a different derivative component.

## Testing a component locally

Requires [docker](https://www.docker.com/get-started/). 
The components can be tested with sample data locally before running them in the cloud: 

```
# 1. build the component - replace [COMP] with chose component
docker build -f dockerfile_[COMP]/dockerfile -t [COMP]:latest .

# 2. run the container
docker run --rm --name=[COMP] [COMP]

# 3. execute the python scripts within the component
docker exec -it [COMP] /bin/bash
python3 component.py
```

## License

Copyright 2023 Dapta LTD

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
