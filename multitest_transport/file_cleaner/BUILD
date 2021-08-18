# MTT file cleaner to clean up unused files inside docker.
load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_test", "pytype_strict_library", "third_party")

package(default_visibility = ["//multitest_transport"])

licenses(["notice"])

pytype_strict_library(
    name = "criterion_lib",
    srcs = ["criterion.py"],
    srcs_version = "PY3",
)

py_test(
    name = "criterion_test",
    srcs = ["criterion_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":criterion_lib",
        third_party("absl/testing:absltest"),
        third_party("pyfakefs:fake_filesystem_unittest"),
    ],
)

pytype_strict_library(
    name = "operation_lib",
    srcs = ["operation.py"],
    srcs_version = "PY3",
    deps = [
        "//multitest_transport/util:file_util_lib",
    ],
)

py_test(
    name = "operation_test",
    srcs = ["operation_test.py"],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":operation_lib",
        "//multitest_transport/util:env_lib",
        third_party("absl/testing:absltest"),
        third_party("pyfakefs:fake_filesystem_unittest"),
    ],
)
