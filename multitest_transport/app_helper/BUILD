# Helpers for off-cloud environment.
load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_test", "pytype_strict_library", "third_party")

package(default_visibility = ["//multitest_transport"])

licenses(["notice"])

pytype_strict_library(
    name = "launcher_lib",
    srcs = [
        "launcher.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":rabbitmq_plugin_lib",
        "//multitest_transport/models:test_run_hook_lib",
        "@tradefed_cluster//tradefed_cluster:common_lib",
        "@tradefed_cluster//tradefed_cluster:env_config_lib",
        "@tradefed_cluster//tradefed_cluster/plugins:base_lib",
        "@tradefed_cluster//tradefed_cluster/util:ndb_shim_lib",
        third_party("absl:app"),
        third_party("absl/flags"),
        third_party("attr"),
        third_party("gunicorn"),
        third_party("requests"),
        third_party("six"),
    ],
)

py_test(
    name = "launcher_test",
    srcs = [
        "launcher_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":launcher_lib",
        third_party("absl/testing:absltest"),
        third_party("absl/testing:parameterized"),
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "rabbitmq_plugin_lib",
    srcs = [
        "rabbitmq_plugin.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        "@tradefed_cluster//tradefed_cluster/plugins:base_lib",
        third_party("pika"),
        third_party("pytz"),
        third_party("six"),
    ],
)

py_test(
    name = "rabbitmq_plugin_test",
    srcs = [
        "rabbitmq_plugin_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":rabbitmq_plugin_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "rabbitmq_puller_lib",
    srcs = [
        "rabbitmq_puller.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        third_party("absl:app"),
        third_party("absl/flags"),
        third_party("pika"),
        third_party("six"),
        third_party("yaml"),
    ],
)

py_test(
    name = "rabbitmq_puller_test",
    srcs = [
        "rabbitmq_puller_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":rabbitmq_puller_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
        third_party("six"),
    ],
)
