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

FROM ubuntu:16.04
MAINTAINER Moon Kim <moonk@google.com>

ARG MTT_VERSION=dev

ENV MTT_VERSION ${MTT_VERSION}
ENV MTT_STORAGE_PATH /data
ENV MTT_MASTER_PORT 8000

ENV MTT_CUSTOM_TF_CONFIG_FILE ${MTT_STORAGE_PATH}/host-config.xml
ENV MTT_LOG_DIR ${MTT_STORAGE_PATH}/log
ENV MTT_TEST_OUTPUT_DIR ${MTT_STORAGE_PATH}/app_default_bucket/test_runs
ENV MTT_TEST_WORK_DIR ${MTT_STORAGE_PATH}/tmp
ENV PATH /tmp/custom_sdk_tools:/mtt/prebuilts/tradefed:${PATH}

# Authenticate on GCE (ignored if running locally or file not provided)
ENV GOOGLE_APPLICATION_CREDENTIALS /tmp/keyfile/key.json

RUN apt-get update && apt-get install -y \
        apt-utils \
        cron \
        curl \
        daemontools \
        git \
        iputils-ping \
        libc++-dev \
        python-enum34 \
        python-pip \
        usbutils \
        unzip \
        wget \
        zip
RUN pip install\
        browsepy\
        google-cloud-storage\
        virtualenv

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
RUN mkdir -p /sdk_tools
RUN curl -L https://dl.google.com/android/repository/build-tools_r29.0.2-linux.zip -o build-tools.zip \
    && unzip -jq build-tools.zip -d /sdk_tools android-10/aapt \
    && rm build-tools.zip
# TODO: Use platform-tools-latest-linux.zip to get latest version
RUN curl -L https://dl.google.com/android/repository/platform-tools_r29.0.4-linux.zip -o platform-tools.zip \
    && unzip -jq platform-tools.zip -d /sdk_tools \
        platform-tools/adb \
        platform-tools/fastboot \
        platform-tools/mke2fs \
    && rm platform-tools.zip
ENV PATH /tmp/custom_sdk_tools:/sdk_tools:${PATH}

# Install App Engine SDK
RUN curl -O https://storage.googleapis.com/appengine-sdks/featured/google_appengine_1.9.82.zip \
    && unzip -q google_appengine_1.9.82.zip \
    && rm google_appengine_1.9.82.zip
# This is to workaround https://issuetracker.google.com/35901176
RUN rm /google_appengine/lib/cacerts/urlfetch_cacerts.txt
ENV PATH /google_appengine:${PATH}

# TODO: remove the following hacks once migrated to Python 3.
# Modify App Enging SDK to avoid using FancyProxyHandler which does not respect no_proxy.
RUN sed -i s/fancy_urllib.FancyProxyHandler/urllib2.ProxyHandler/g \
    /google_appengine/google/appengine/tools/appengine_rpc.py
# Fix a bug in urllib2.ProxyHandler to use one proxy settings.
RUN sed -i s/proxy_bypass\(req.host\)/proxy_bypass\(req.host,proxies=self.proxies\)/g \
    /usr/lib/python2.7/urllib2.py

COPY . /mtt
# dev_appserver.py errors if there exists Dockerfile.
RUN rm /mtt/Dockerfile
RUN unzip -q /mtt/prebuilts/tradefed/tradefed.zip -d /mtt/prebuilts/tradefed
ENV PATH /mtt/prebuilts/tradefed:${PATH}

# Setup scripts
RUN chmod 755 /mtt/scripts/init.sh
RUN chmod 755 /mtt/scripts/file_cleaner.sh

VOLUME /data

CMD ["/mtt/scripts/init.sh"]