#!/bin/bash
set -e -u

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --environment | -e) ENVIRONMENT="$2";;
    *) echo "Unknown argument $1"; exit 1; # fail-fast on unknown key
  esac
  shift # skip key
  shift # skip value
done

ENVIRONMENT="${ENVIRONMENT:-prod}"

if [[ ! ${ENVIRONMENT} =~ ^(prod|dogfood|latest)$ ]]; then
  echo "--environment must prod, dogfood or latest."
  exit 1
fi

MTT_URL="https://storage.googleapis.com/android-mtt.appspot.com/${ENVIRONMENT}/mtt"
HOME_BIN_DIR="$HOME/bin"

function install_docker {
  docker_version=$(docker --version 2> /dev/null || echo "")
  if [ -z "$docker_version" ]
  then
    echo "Install Docker Engine..."
    # Follow https://docs.docker.com/install/linux/docker-ce/ubuntu/
    # to install docker.
    sudo apt-get update
    sudo apt-get install -y \
      apt-transport-https \
      ca-certificates \
      curl \
      gnupg-agent \
      software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    sudo add-apt-repository \
      "deb [arch=amd64] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) \
      stable"
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
  else
    echo "\"$docker_version\" is installed. Skip installing."
  fi
}

function setup_sudoless_docker {
  if ! groups $USER | grep -q '\bdocker\b'
  then
    echo "Add $USER to 'docker' group."
    sudo usermod -a -G docker $USER
    newgrp docker
  else
    echo "$USER is already in 'docker' group."
  fi
}

function download_mtt {
  mtt_version=$(mtt version 2> /dev/null || echo "")
  if [[ -z "$mtt_version" ]]
  then
    echo "Android Test Station is not installed."
  elif [[ ! "$mtt_version" =~ "$ENVIRONMENT" ]]
  then
    echo "Android Test Station is '${mtt_version}', not from ${ENVIRONMENT}."
  else
    echo "\"Android Test Station $mtt_version\" is installed. Skip installing."
    return
  fi
  echo "Install MTT CLI to $HOME_BIN_DIR."

  mkdir -p $HOME_BIN_DIR
  curl -o ${HOME_BIN_DIR}/mtt $MTT_URL
  chmod +x ${HOME_BIN_DIR}/mtt
  which_mtt=$(which mtt 2> /dev/null || echo "")
  if [ -z "$which_mtt" ]
  then
    echo PATH=${HOME_BIN_DIR}:\$PATH >> $HOME/.bashrc
    export PATH=${HOME_BIN_DIR}:$PATH
    mtt version
  fi
}

function install_python {
  python3_version=$(python3 --version 2> /dev/null)
  if [ -z "$python3_version" ]
  then
    echo "Python 3 is not installed. Install Python 3..."
    sudo apt-get update
    sudo apt-get install -y python3
  else
    echo "\"${python3_version}\" is installed. Skip installing."
  fi
  python3_version=$(ls -1 /usr/bin/python* | grep '3.[0-9]$' | sort -r | head -n 1)
  current_link=$(update-alternatives --query python3 | grep "Value:" | cut -d ' ' -f 2)
  if [[ "$current_link" != "$python3_version" ]]; then
    echo "${python3_version} is the highest python3 version installed. Linking /usr/bin/python3 to ${python3_version}."
    sudo update-alternatives --install /usr/bin/python3 python3 "${python3_version}" 1
  fi
  if ! python3 -m "distutils.util"; then
    echo "\"python3-distutils\" not installed, Install python3-distutils..."
    sudo apt-get install -y python3-distutils
  else
    echo "\"python3-distutils\" is installed. Skip installing."
  fi
}

install_docker
install_python
download_mtt
# setup_sudoless_docker have to be the last line since it will start a
# new bash to login as docker group.
setup_sudoless_docker
