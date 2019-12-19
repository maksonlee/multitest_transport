# Android testing lab software for Android device partners

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_appengine_binary", "py_appengine_library", "py_appengine_test", "third_party")

licenses(["notice"])

exports_files(["LICENSE"])

package_group(
    name = "multitest_transport",
    packages = [
        "//multitest_transport/...",
    ],
)

PY_APPENGINE_ENVS = [{"runtime": "python27"}]

exports_files(["serve.sh"])

py_appengine_test(
    name = "appengine_config_test",
    srcs = [
        "appengine_config.py",
        "appengine_config_test.py",
    ],
    use_public_sdk = 1,
    deps = [
        ":main",
        third_party("absl/testing:absltest"),
    ],
)

py_appengine_library(
    name = "gcs_proxy_lib",
    srcs = [
        "gcs_proxy.py",
    ],
    envs = PY_APPENGINE_ENVS,
    deps = [
        "//multitest_transport/models",
    ],
)

filegroup(
    name = "prebuilts",
    srcs = glob([
        "prebuilts/**",
    ]),
)

filegroup(
    name = "scripts",
    srcs = glob([
        "scripts/**",
    ]),
)

config_setting(
    name = "dev_mode",
    define_values = {
        "dev_mode": "true",
    },
)

py_appengine_binary(
    name = "main",
    configs = [
        "appengine_config.py",
        "config.yaml",
        "//multitest_transport/gae_configs",
    ],
    data = select({
        ":dev_mode": [
            "//multitest_transport/ui2:dev_sources",
        ],
        "//conditions:default": [
            "Dockerfile",
            "//multitest_transport/ui2:app",
        ],
    }) + [
        ":prebuilts",
        ":scripts",
        "//multitest_transport:serve.sh",
        "//multitest_transport/ui2:static_files",
    ],
    deps = [
        ":gcs_proxy_lib",
        "//multitest_transport/api",
        "//multitest_transport/core",
        "//multitest_transport/sidekicks",
        "//multitest_transport/test_scheduler",
        "//multitest_transport/ui2",
        "@tradefed_cluster//tradefed_cluster:app_lib",
    ],
)

# To run the server locally, use:
# $ iblaze run mtt_server
# To run the server with javascript recompiling on page refresh, use:
# $ iblaze run mtt_server --define dev_mode=true
# Additional arguments can be added as -- --param_name param_value, e.g.:
# $ iblaze run mtt_server --define dev_mode=true -- --storage_path /tmp/mtt
sh_binary(
    name = "mtt_server",
    srcs = ["//multitest_transport:serve.sh"],
    args = select({
        "dev_mode": [
            "--dev_mode true",
            "--use_mtime_file_watcher true",
        ],
        "//conditions:default": [],
    }) + [
        "--config_dir '..'",
    ],
    data = [
        ":main",
    ],
)

