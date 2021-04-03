# Copyright 2019 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM ubuntu:20.04
MAINTAINER Moon Kim <moonk@google.com>

ENV PATH /tmp/custom_sdk_tools:${PATH}

# Make sure apt-get retries on failures
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80retries

# TODO: rabbitmq-server is fixed to an old version because
#                    3.8.2-0ubuntu1.1 takes one minute to start.
RUN export DEBIAN_FRONTEND=noninteractive && apt-get update && apt-get install -y \
        apt-utils \
        cron \
        daemontools \
        git \
        iputils-ping \
        libc++-dev \
        lsof \
        python \
        python3 \
        mariadb-server \
        python3-pip \
        rabbitmq-server=3.8.2-0ubuntu1 \
        socat \
        tzdata \
        usbutils \
        unzip \
        wget \
        zip
RUN pip3 install \
        absl-py \
        attrs \
        browsepy \
        cachetools \
        flask \
        grpcio \
        gunicorn
# Install python2 pip.
RUN wget -q --retry-connrefused -O /tmp/get-pip.py https://bootstrap.pypa.io/pip/2.7/get-pip.py && \
    python /tmp/get-pip.py && \
    rm /tmp/get-pip.py
# Install a version of six that supports ensure_* methods.
RUN pip install six==1.12.0

# Installing dependencies for VTS
# Reference: https://cs.android.com/android/platform/superproject/+/master:test/vts/script/setup.sh
RUN export DEBIAN_FRONTEND=noninteractive && apt-get update && apt-get install -y \
        python-dev \
        python-protobuf \
        protobuf-compiler \
        python-setuptools \
        # python-pip \
        # python3-pip \
        # python-virtualenv \
        build-essential \
        python-tk \
        libjpeg-dev \
        libtiff-dev
# Pin the virtualenv version to use a one with a proven compatibility with VTS.
RUN pip install virtualenv==20.0.31

# Install JDK9 from AOSP (https://android.googlesource.com/platform/prebuilts/jdk/jdk9.git/+/375786699dcb340ab2d08de7f5d13dba6637f221)
RUN mkdir -p /jdk/jdk9 && \
    cd /jdk/jdk9 && \
    git init && \
    git remote add origin https://android.googlesource.com/platform/prebuilts/jdk/jdk9.git && \
    git config core.sparseCheckout true && \
    echo "linux-x86/" >> .git/info/sparse-checkout && \
    git fetch origin 375786699dcb340ab2d08de7f5d13dba6637f221 --depth 1 && \
    git checkout 375786699dcb340ab2d08de7f5d13dba6637f221 && \
    rm -rf .git/ && \
    cd -
ENV JAVA_HOME /jdk/jdk9/linux-x86
ENV PATH ${JAVA_HOME}/bin:${PATH}

# Install SDK tools (aapt, adb, fastboot, mke2fs)
RUN mkdir -p /sdk_tools/lib64
# Use wget for more reliable retries
RUN wget -q --retry-connrefused -O build-tools.zip https://dl.google.com/android/repository/build-tools_r29.0.3-linux.zip \
    && unzip -jq build-tools.zip -d /sdk_tools android-10/aapt \
    && unzip -jq build-tools.zip -d /sdk_tools/lib64 android-10/lib64/* \
    && rm build-tools.zip
RUN wget -q --retry-connrefused -O platform-tools.zip https://dl.google.com/android/repository/platform-tools_r29.0.6-linux.zip \
    && unzip -jq platform-tools.zip -d /sdk_tools \
        platform-tools/adb \
        platform-tools/fastboot \
        platform-tools/mke2fs \
    && rm platform-tools.zip
ENV PATH /tmp/custom_sdk_tools:/sdk_tools:${PATH}
ENV LD_LIBRARY_PATH /sdk_tools/lib64:${LD_LIBRARY_PATH}

# Install Google Cloud SDK
# Reference: https://github.com/GoogleCloudPlatform/cloud-sdk-docker/blob/master/Dockerfile
ENV CLOUD_SDK_VERSION=334.0.0
ENV CLOUD_SDK_ROOT=/usr/lib/google-cloud-sdk
RUN apt-get -qqy update && apt-get install -qqy \
        curl \
        gcc \
        python3-dev \
        python3-pip \
        apt-transport-https \
        openssh-client \
        git \
        make \
        gnupg && \
    pip3 install -U crcmod && \
    export CLOUD_SDK_REPO="cloud-sdk" && \
    echo "deb https://packages.cloud.google.com/apt $CLOUD_SDK_REPO main" > /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key add - && \
    apt-get update && \
    apt-get install -y --allow-unauthenticated \
        google-cloud-sdk=${CLOUD_SDK_VERSION}-0 \
        google-cloud-sdk-datastore-emulator=${CLOUD_SDK_VERSION}-0

# grpcio is required to use Cloud Datastore emulator.
# Reference: https://cloud.google.com/appengine/docs/standard/python/tools/migrate-cloud-datastore-emulator#failing_grpc_imports
RUN pip install grpcio

# Install cuttlefish-common
# debuild -d skips checking the dependency of debhelper-compat 12.
ARG CUTTLEFISH_COMMON_COMMIT=09546cf4a618563071beb42508fc7b4a5336ad29
RUN git clone https://github.com/google/android-cuttlefish --no-checkout --single-branch /tmp/cuttlefish-common/src && \
    cd /tmp/cuttlefish-common/src && \
    git checkout ${CUTTLEFISH_COMMON_COMMIT} && \
    apt-get install -y devscripts config-package-dev debhelper-compat && \
    debuild -i -us -uc -b -d && \
    apt-get install -y ../cuttlefish-common_*_amd64.deb iproute2 rsyslog && \
    cd - && \
    rm -rf /tmp/cuttlefish-common/src
# TODO: Remove this flag after a couple of releases.
ENV MTT_SUPPORT_BRIDGE_NETWORK true

# Install acloud
# TODO: Replace /url with ?alt=media when it works
ARG ACLOUD_DOWNLOAD_URL='https://www.googleapis.com/android/internal/build/v3/builds/7087482/aosp_cf_x86_64_phone-userdebug/attempts/latest/artifacts/acloud_prebuilt/url'
ENV ACLOUD_PREBUILT_PATH=/bin/acloud_prebuilt
RUN wget -q --retry-connrefused -O ${ACLOUD_PREBUILT_PATH} ${ACLOUD_DOWNLOAD_URL} \
    && chmod +x ${ACLOUD_PREBUILT_PATH}

# Install libusb-1.0 with udev disabled, as it doesn't work without --net=host
ARG LIBUSB_VERSION=libusb-1.0.24
RUN wget -q --retry-connrefused -O ${LIBUSB_VERSION}.tar.bz2 http://downloads.sourceforge.net/project/libusb/libusb-1.0/${LIBUSB_VERSION}/${LIBUSB_VERSION}.tar.bz2 \
    && tar -xf ${LIBUSB_VERSION}.tar.bz2 \
    && cd ${LIBUSB_VERSION} \
    && ./configure --disable-udev \
    && make install \
    && ldconfig \
    && cd - \
    && rm -rf ${LIBUSB_VERSION}.tar.bz2 ${LIBUSB_VERSION}

# Docker builds image by layers. If a layer changes, all the following layers
# will need to be rebuilt. So less frequent changes, e.g. install packages, will
# be built in the base layers. And frequent changes, e.g. set env, will be in
# later layers.
ARG MTT_GOOGLE_OAUTH2_CLIENT_ID=
ARG MTT_GOOGLE_OAUTH2_CLIENT_SECRET=
ARG MTT_TRADEFED_PREBUILT=tradefed.zip
ARG MTT_VERSION=dev

ENV MTT_GOOGLE_OAUTH2_CLIENT_ID ${MTT_GOOGLE_OAUTH2_CLIENT_ID}
ENV MTT_GOOGLE_OAUTH2_CLIENT_SECRET ${MTT_GOOGLE_OAUTH2_CLIENT_SECRET}
ENV MTT_VERSION ${MTT_VERSION}
ENV MTT_STORAGE_PATH /data
ENV MTT_SERVER_LOG_LEVEL info

ENV MTT_CUSTOM_TF_CONFIG_FILE ${MTT_STORAGE_PATH}/host-config.xml
ENV MTT_LOG_DIR ${MTT_STORAGE_PATH}/log
ENV MTT_TEST_OUTPUT_DIR ${MTT_STORAGE_PATH}/app_default_bucket/test_runs
ENV MTT_TEST_WORK_DIR ${MTT_STORAGE_PATH}/tmp
ENV MTT_USE_HOST_ADB ""

# Authenticate on GCE (ignored if running locally or file not provided)
ENV GOOGLE_APPLICATION_CREDENTIALS /tmp/keyfile/key.json

COPY . /mtt
# Unzip the selected prebuilt TF runner
RUN unzip -q /mtt/prebuilts/tradefed/${MTT_TRADEFED_PREBUILT} -d /tradefed
RUN rm -rf /mtt/prebuilts/tradefed
ENV PATH /tradefed:${PATH}

# Setup scripts
RUN chmod 755 \
        /mtt/scripts/init.sh \
        /mtt/scripts/file_cleaner.sh \
        /mtt/scripts/gen_subnets.py

VOLUME /data

CMD ["/mtt/scripts/init.sh"]
