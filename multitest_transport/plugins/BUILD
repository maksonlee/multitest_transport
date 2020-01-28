# MTT default plugins.

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_appengine_library", "py_appengine_test", "third_party")

licenses(["notice"])


py_library(
    name = "file_upload_hook_lib",
    srcs = [
        "file_upload_hook.py",
    ],
    deps = [
        ":plugin_base",
        "//multitest_transport/util",
    ],
)

py_appengine_test(
    name = "file_upload_hook_test",
    srcs = [
        "file_upload_hook_test.py",
    ],
    deps = [
        ":file_upload_hook_lib",
        "//multitest_transport/models",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_library(
    name = "gcs_lib",
    srcs = [
        "gcs.py",
    ],
    deps = [
        ":file_upload_hook_lib",
        ":plugin_base",
        "//multitest_transport/util",
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
        ":plugin_base",
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
        ":plugin_base",
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
        ":plugin_base",
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
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":plugin_base",
        ":gcs_lib",
        ":google_drive_lib",
        ":local_file_store_lib",
        ":partner_android_build_lib",
        ":web_hook_lib",
        third_party("apiclient"),
    ],
)

py_library(
    name = "plugin_base",
    srcs = [
        "base.py",
        "constant.py",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":registry_lib",
        third_party("six"),
        "//multitest_transport/util",
    ],
)

py_library(
    name = "registry_lib",
    srcs = [
        "registry.py",
    ],
)

py_appengine_test(
    name = "registry_test",
    srcs = [
        "registry_test.py",
    ],
    deps = [
        ":registry_lib",
        third_party("absl/testing:absltest"),
        third_party("six"),
    ],
)

py_appengine_library(
    name = "web_hook_lib",
    srcs = [
        "web_hook.py",
    ],
    deps = [
        ":plugin_base",
    ],
)

py_appengine_test(
    name = "web_hook_test",
    srcs = [
        "web_hook_test.py",
    ],
    deps = [
        ":web_hook_lib",
        "//multitest_transport/models",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)
