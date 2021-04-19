# Android Test Station local file server.
load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_library", "py_strict_test", "pytype_strict_binary", "pytype_strict_library", "third_party")

licenses(["notice"])

# TODO: change to pytype_strict_library once b/168841142 is fixed.
py_library(
    name = "file_server_lib",
    srcs = [
        "file_server.py",
        "gunicorn_config.py",
    ],
    srcs_version = "PY3",
    visibility = ["//multitest_transport"],
    deps = [
        third_party("absl:app"),
        third_party("absl/flags"),
        third_party("attr"),
        third_party("flask"),
    ],
)

py_strict_test(
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
        third_party("werkzeug"),
    ],
)

pytype_strict_binary(
    name = "file_server",
    srcs = ["file_server.py"],
    main = "file_server.py",
    python_version = "PY3",
    deps = [
        ":file_server_lib",
        third_party("absl:app"),
        third_party("absl/flags"),
        third_party("flask"),
    ],
)

pytype_strict_library(
    name = "proxy_lib",
    srcs = [
        "proxy.py",
    ],
    srcs_version = "PY2AND3",
    visibility = ["//multitest_transport"],
    deps = [
        "//multitest_transport/util",
        third_party("flask"),
        third_party("six"),
    ],
)

py_test(
    name = "proxy_test",
    srcs = [
        "proxy_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":proxy_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
        third_party("webtest"),
        "//net/proto2/python/public:use_pure_python",  # Automatically added go/proto_python_default
    ],
)
