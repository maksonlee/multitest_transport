# Sidekick services for Multi-Test Transport.

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_appengine_library", "py_appengine_test", "third_party")

licenses(["notice"])

py_appengine_library(
    name = "gcs_cleaner_lib",
    srcs = [
        "gcs_cleaner.py",
    ],
    deps = [
        third_party("cloudstorage"),
        "//multitest_transport/models",
        "//multitest_transport/test_scheduler",
    ],
)

py_appengine_test(
    name = "gcs_cleaner_test",
    srcs = [
        "gcs_cleaner_test.py",
    ],
    use_public_sdk = 1,
    deps = [
        ":gcs_cleaner_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "sidekicks",
    srcs = [
        "main.py",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":gcs_cleaner_lib",
        "//multitest_transport/test_scheduler",
        "//multitest_transport/util",
    ],
)
