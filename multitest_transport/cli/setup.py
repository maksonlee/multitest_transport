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

"""Setup for mtt cli."""
import setuptools

VERSION = '0.0'

setuptools.setup(
    name='Android_Test_Station_CLI',
    description='CLI for Android Test Station.',
    url='https://source.android.com/compatibility/tests/development/android-test-station/ats-user-guide',
    version=VERSION,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    packages=setuptools.find_packages(),
    # The package works for 3.7 and up, but not for python 4 yet.
    python_requires='~=3.7',
    entry_points={
        'console_scripts': ['mtt=multitest_transport.cli.cli:Main'],
    },
    install_requires=[
        'ansible-base',
        'attrs',
        'fabric',
        'google-api-core',
        'google-api-python-client',
        'google-auth',
        'google-cloud-core',
        'google-cloud-secret-manager',
        'google-cloud-storage',
        'google-cloud-logging',
        'grpcio',
        'packaging',
        'python-dateutil',
        # Temporary fix for proto dependency bug.
        'protobuf == 3.20.1',
        'pytz',
        'pyOpenSSL == 22.0.0',
        'requests == 2.23.0',
        'SecretStorage',
        'six == 1.15.0',
        'strictyaml',
    ]
)
