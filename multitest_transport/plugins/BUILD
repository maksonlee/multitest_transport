# MTT default plugins.

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_appengine_library", "py_appengine_test", "third_party")

licenses(["notice"])


py_library(
    name = "base_lib",
    srcs = [
        "base.py",
        "constant.py",
    ],
    deps = [
        "//multitest_transport/util",
    ],
)

py_library(
    name = "gcs_lib",
    srcs = [
        "gcs.py",
    ],
    deps = [
        ":base_lib",
        ":stream_uploader",
        third_party("apiclient"),
    ],
)

py_appengine_test(
    name = "gcs_test",
    srcs = [
        "gcs_test.py",
    ],
    deps = [
        ":gcs_lib",
        third_party("absl/testing:absltest"),
        third_party("apiclient"),
        third_party("mock"),
    ],
)

py_library(
    name = "google_drive_lib",
    srcs = [
        "google_drive.py",
    ],
    deps = [
        ":base_lib",
        third_party("apiclient"),
    ],
)

py_appengine_test(
    name = "google_drive_test",
    srcs = [
        "google_drive_test.py",
    ],
    deps = [
        ":google_drive_lib",
        third_party("absl/testing:absltest"),
        third_party("apiclient"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "local_file_store_lib",
    srcs = [
        "local_file_store.py",
    ],
    deps = [
        ":base_lib",
    ],
)

py_appengine_test(
    name = "local_file_store_test",
    srcs = [
        "local_file_store_test.py",
    ],
    use_public_sdk = 1,
    deps = [
        ":local_file_store_lib",
        third_party("absl/testing:absltest"),
    ],
)

py_appengine_library(
    name = "partner_android_build_lib",
    srcs = [
        "partner_android_build.py",
    ],
    deps = [
        ":base_lib",
    ],
)

py_appengine_test(
    name = "partner_android_build_test",
    srcs = [
        "partner_android_build_test.py",
    ],
    python_version = "PY2",
    deps = [
        ":partner_android_build_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_library(
    name = "plugins",
    srcs = [
        "__init__.py",
        "base.py",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":gcs_lib",
        ":google_drive_lib",
        ":local_file_store_lib",
        ":partner_android_build_lib",
        third_party("apiclient"),
    ],
)

py_library(
    name = "stream_uploader",
    srcs = [
        "stream_uploader.py",
    ],
    deps = [
        third_party("apiclient"),
    ],
)

py_appengine_test(
    name = "stream_uploader_test",
    srcs = [
        "stream_uploader_test.py",
    ],
    deps = [
        ":stream_uploader",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)
