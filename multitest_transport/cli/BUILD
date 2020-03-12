# MTT Command Line Interfaces

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "Fileset", "FilesetEntry", "py2and3_test", "py_library", "pytype_strict_binary", "third_party", "zip_dir")

licenses(["notice"])

pytype_strict_binary(
    name = "cli",
    srcs = ["cli.py"],
    python_version = "PY3",
    srcs_version = "PY2AND3",
    test_lib = True,
    visibility = ["//visibility:private"],
    deps = [
        ":cli_lib",
    ],
)

py_library(
    name = "cli_lib",
    srcs = [
        "cli.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":cli_util_lib",
        ":command_util_lib",
        ":host_util_lib",
        third_party("six"),
    ],
)

py_library(
    name = "cli_util_lib",
    srcs = [
        "cli_util.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":command_util_lib",
        ":gcs_file_util_lib",
        ":google_auth_util_lib",
        third_party("six"),
    ],
)

py_library(
    name = "cluster_lib",
    srcs = [
        "cluster.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":command_util_lib",
    ],
)

py_library(
    name = "command_util_lib",
    srcs = [
        "command_util.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":google_auth_util_lib",
        third_party("six"),
    ],
)

py_library(
    name = "gcs_file_util_lib",
    srcs = [
        "gcs_file_util.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        third_party("google/cloud/storage:storage_future"),
    ],
)

py_library(
    name = "google_auth_util_lib",
    srcs = [
        "google_auth_util.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        third_party("concurrent:futures"),
        third_party("google/auth:transport/requests"),
        third_party("google/oauth2:credentials"),
        third_party("google/oauth2:service_account"),
    ],
)

pytype_strict_binary(
    name = "lab_cli",
    srcs = ["lab_cli.py"],
    python_version = "PY3",
    srcs_version = "PY2AND3",
    test_lib = True,
    deps = [
        ":lab_cli_lib",
    ],
)

py_library(
    name = "lab_cli_lib",
    srcs = [
        "lab_cli.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":cli_util_lib",
        ":host_util_lib",
    ],
)

py_library(
    name = "host_util_lib",
    srcs = [
        "host_util.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":command_util_lib",
        ":gcs_file_util_lib",
        ":google_auth_util_lib",
        "@tradefed_cluster//tradefed_cluster/configs:lab_config_lib",
    ],
)

py_library(
    name = "unittest_util_lib",
    testonly = 1,
    srcs = [
        "unittest_util.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        third_party("six"),
    ],
)

# Test

py2and3_test(
    name = "cli_test",
    srcs = [
        "cli_test.py",
    ],
    deps = [
        ":cli_lib",
        ":command_util_lib",
        ":unittest_util_lib",
        third_party("absl/testing:absltest"),
        third_party("absl/testing:parameterized"),
        third_party("mock"),
    ],
)

py2and3_test(
    name = "cli_util_test",
    srcs = [
        "cli_util_test.py",
    ],
    deps = [
        ":cli_util_lib",
        ":unittest_util_lib",
        third_party("absl/testing:absltest"),
        third_party("absl/testing:parameterized"),
        third_party("mock"),
    ],
)

py2and3_test(
    name = "command_util_test",
    srcs = [
        "command_util_test.py",
    ],
    deps = [
        ":command_util_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py2and3_test(
    name = "gcs_file_util_test",
    srcs = [
        "gcs_file_util_test.py",
    ],
    deps = [
        ":gcs_file_util_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
        "@tradefed_cluster//tradefed_cluster/configs:lab_config_lib",
    ],
)

py2and3_test(
    name = "host_util_test",
    srcs = [
        "host_util_test.py",
    ],
    deps = [
        ":host_util_lib",
        third_party("absl/testing:absltest"),
        third_party("absl/testing:parameterized"),
        third_party("concurrent:futures"),
        third_party("mock"),
    ],
)

# Run with blaze test cli:integration_test --test_arg=...
py_test(
    name = "integration_test",
    srcs = [
        "integration_test.py",
    ],
    python_version = "PY3",
    tags = ["local"],
    deps = [
        third_party("absl/testing:absltest"),
    ],
)

py2and3_test(
    name = "lab_cli_test",
    srcs = [
        "lab_cli_test.py",
    ],
    deps = [
        ":lab_cli_lib",
        ":unittest_util_lib",
        third_party("absl/testing:absltest"),
        third_party("absl/testing:parameterized"),
        third_party("mock"),
    ],
)

