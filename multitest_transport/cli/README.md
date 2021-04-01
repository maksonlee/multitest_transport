# Android Test Station CLI(f.k.a. MTT CLI)

This is a command-line toolkit to simplify Android Test Station lab setups.

## Installation

Download CLI tools from [cloud project][1]. Please use "mtt" for single host management, and use "mtt_lab" for multi-host management in the lab.


## User Manual

### Basics

#### Test Station CLI Commands

To start a test station on a host:

```bash
$ [sudo] mtt start [<host_config.yaml>] [--service_account_json_key_path <path/to/account_key>] [--force_update] [--port <port_number>]
```

To restart a test station on a host:

```bash
$ [sudo] mtt restart [<host_config.yaml>] [--service_account_json_key_path <path/to/account_key>] [--force_update] [--port <port_number>] [--wait]
```

To update a test station on a host:

```bash
$ [sudo] mtt update [<host_config.yaml>] [--service_account_json_key_path <path/to/account_key>] [--force_update] [--port <port_number>] [--wait]
```

To stop a test station on a host:

```bash
$ [sudo] mtt stop [<host_config.yaml>] [--wait]
```

*  `sudo` is optional, but it is required when the command is going to turn on or off `auto-update` or any other daemon features.
*  `host_config.yaml` is optional, apply this to use a non-default config file.
*  `service_account_json_key_path` is optional, apply this for account key verifications, and it can be configured in the config as well.
*  `force_update` updates the current available docker image, even if the local version is up-to-date already.
*  `wait` let the CLI wait until all the running tests finish.
*  `port` specify a customized value to the control server port.

##### Example of host_config.yaml
```yaml
cluster_configs:
- cluster_name: dockerized-tf
  docker_image: gcr.io/dockerized-tradefed/tradefed:golden
  enable_autoupdate: true
  host_configs:
  - {hostname: atz-003}
  host_login_name: android-test
  master_url: https://androidengprod-pa.googleapis.com
  owners: [android-test]
  tf_global_config_path: configs/cluster/dockerized-tf/host-config.xml
service_account_json_key_path: /var/lib/mtt/keyfile/key.json
```

#### Test Station Lab CLI Commands

To start a test station hosts in the Lab:

```bash
$ mtt_lab start <lab_config.yaml> [cluster-name] [--service_account_json_key_path <path/to/account_key>] [--ask_sudo_password] [--parallel] [--ssh_key <path/to/ssh_key>]
```

To restart a test station hosts in the lab:

```bash
$ mtt_lab restart <lab_config.yaml> [cluster-name] [--service_account_json_key_path <path/to/account_key>] [--ask_sudo_password] [--parallel] [--ssh_key <path/to/ssh_key>]
```

To update a test station hosts in the lab:

```bash
$ mtt_lab update <lab_config.yaml> [cluster-name] [--service_account_json_key_path <path/to/account_key>] [--ask_sudo_password] [--parallel] [--ssh_key <path/to/ssh_key>]
```

To stop a test station hosts in the lab:

```bash
$ mtt_lab stop <lab_config.yaml> [cluster-name] [--ask_sudo_password] [--parallel] [--ssh_key <path/to/ssh_key>]
```

  *  `lab_config.yaml` is required in mtt_lab command.
     * `cluster-name` is optional, apply this to operation on only one cluster, instead of the whole lab.
  *  `service_account_json_key_path` is optional, apply this for account key verifications.
  *  `ask_sudo_password` is optional, but it is required when the command is going to turn on or off `auto-update` or any other daemon features on hosts.
  *  `ssh_key` is optional, apply this to specify an SSH key.
  *  `parallel` is optional, apply this to execute commands on hosts in parallel.

##### Example of lab_config.yaml
```yaml
service_account_json_key_path: /google/data/ro/teams/tradefed/configs/tradefed.json
cluster_configs:
- cluster_name: dockerized-tf
  host_login_name: android-test
  owners:
  - android-test
  tf_global_config_path: configs/cluster/dockerized-tf/host-config.xml
  master_url: https://androidengprod-pa.googleapis.com
  docker_image: gcr.io/dockerized-tradefed/tradefed:golden
  host_configs:
  - hostname: atz-003
  - hostname: atz-004
  enable_autoupdate: true

- cluster_name: dockerized-tf-exp
  host_login_name: android-test
  owners:
  - android-test
  tf_global_config_path: configs/cluster/dockerized-tf/host-config.xml
```

### Advanced Features

#### Test Station Auto-Update

Auto-Update keeps your docker images on host up-to-date.

##### Enable auto-update:

* Set `enable_autoupdate: true` in the "host_config.yaml", and run `sudo mtt [start/update/restart] ...`, or
* Set `enable_autoupdate: true` in the "lab_config.yaml", and run `mtt_lab [start/update/restart] ... --ask_sudo_password`.

These commands starts a "systemd" daemon process on the server that continuously check new version of dockerized TF image, and upgrade when available.

##### Disable auto-update:

* Set `enable_autoupdate: false` in the "host_config.yaml", and run `sudo mtt restart ...`, or
* Set `enable_autoupdate: false` in the "lab_config.yaml", and run `mtt_lab restart ... --ask_sudo_password`.

These commands close daemon process and test station container, and start a test station container alone.

[1]: https://pantheon.corp.google.com/storage/browser/android-mtt.appspot.com/dogfood?project=android-mtt
