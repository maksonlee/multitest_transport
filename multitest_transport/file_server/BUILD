# Android Test Station local file server.
load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_appengine_library", "py_appengine_test", "py_binary", "py_library", "py_test", "third_party")

licenses(["notice"])

py_library(
    name = "file_server_lib",
    srcs = [
        "file_server.py",
    ],
    srcs_version = "PY3",
    visibility = ["//multitest_transport"],
    deps = [
        third_party("absl/flags"),
        third_party("attr"),
        third_party("cachetools"),
        third_party("flask"),
    ],
)

py_test(
    name = "file_server_test",
    srcs = [
        "file_server_test.py",
    ],
    data = [
        "test_data/test.txt",
    ],
    python_version = "PY3",
    deps = [
        ":file_server_lib",
        third_party("absl/testing:absltest"),
    ],
)

py_binary(
    name = "file_server",
    srcs = ["file_server.py"],
    main = "file_server.py",
    python_version = "PY3",
    deps = [
        ":file_server_lib",
    ],
)

py_appengine_library(
    name = "proxy_lib",
    srcs = [
        "proxy.py",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        "//multitest_transport/util",
        third_party("six"),
    ],
)

py_appengine_test(
    name = "proxy_test",
    srcs = [
        "proxy_test.py",
    ],
    use_public_sdk = 1,
    deps = [
        ":proxy_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)
