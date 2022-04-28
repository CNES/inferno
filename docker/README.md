# Docker
To install Docker, please refer to Docker [documentation](https://docs.docker.com/engine/install/ubuntu/).

## Install INFERNO from Docker
To install Inferno from docker:
  - first, copy ```inferno/docker``` folder
  - [Edit docker-compose.yml file](#define-a-volume-from-docker-composeyml)
  - [Build the docker image](#build-the-docker-image)

## Define a volume from docker-compose.yml
Setting a volume enables the exchange of data between the host and the container. To do so, you simply need to replace `<host_path>` in "docker-compose. yaml" with a folder path in the host system.
Example: if we replace `<host_path>:/home/user/share` by `/tmp:/home/user/share`, the folder `/tmp` will appear as `/home/user/share` in the container.


```yaml
version: "3"

services:
  app:
    image: inferno
    build: .
    environment:
      - DISPLAY=${DISPLAY}
    volumes:
      - /tmp/.X11-unix:/tmp/.X11-unix
      - <host_path>:/home/user/share # example : /tmp:/home/user/share
    network_mode: host
```

## Build the docker image
To build the docker image,we need to add the files ```OTB-7.4.0-Linux64.run``` and ```inferno-master.tar.gz``` to the root of the docker folder. To do so, we can run the command below:

```bash
cd docker

# download OTB-7.4.0-Linux64.run in docker folder
wget https://www.orfeo-toolbox.org/packages/OTB-7.4.0-Linux64.run 

# inferno-develop.tar.gz (you can manually put the inferno-develop.tar.gz in docker folder )
wget https://gitlab.cnes.fr/demortr/inferno/-/archive/master/inferno-master.tar.gz

# Build the image 
docker-compose build
```

The docker folder should look like this:

```bash
$: tree ./docker
docker
├── Dockerfile
├── OTB-7.4.0-Linux64.run
├── README.md
├── docker-compose.yml
├── gdal-config
└── inferno-develop.tar.gz
```


## Run Inferno
To run Inferno, run command below:
```bash
docker-compose up
```

## Run treatments on the command line
To run the treatment on the command line, run the command below:

```bash
sudo docker run -it -v <host_path>:/home/user/share inferno -e <Path of ExecConfig.json> 
```

Replace `<host_path>` by the path define in [step 2](#define-a-volume-from-docker-composeyml).  
Replace `<Path of ExecConfig.json>` by the path of ExecConfig.json.


