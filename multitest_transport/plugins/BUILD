# MTT default plugins.
load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_test", "pytype_strict_library", "third_party")

licenses(["notice"])

pytype_strict_library(
    name = "android_lib",
    srcs = [
        "android.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":plugin_base",
        "//multitest_transport/util:env_lib",
        "//multitest_transport/util:errors_lib",
        "//multitest_transport/util:file_util_lib",
        "//multitest_transport/util:oauth2_util_lib",
        third_party("apiclient"),
        third_party("httplib2"),
    ],
)

py_test(
    name = "android_test",
    srcs = [
        "android_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":android_lib",
        third_party("absl/testing:absltest"),
    ],
)


pytype_strict_library(
    name = "file_upload_hook_lib",
    srcs = [
        "file_upload_hook.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":plugin_base",
        "//multitest_transport/util",
    ],
)

py_test(
    name = "file_upload_hook_test",
    srcs = [
        "file_upload_hook_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":file_upload_hook_lib",
        "//multitest_transport/models",
        third_party("absl/testing:absltest"),
    ],
)

pytype_strict_library(
    name = "gcs_lib",
    srcs = [
        "gcs.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":file_upload_hook_lib",
        ":plugin_base",
        "//multitest_transport/models",
        "//multitest_transport/util",
        third_party("apiclient"),
    ],
)

py_test(
    name = "gcs_test",
    srcs = [
        "gcs_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":gcs_lib",
        third_party("absl/testing:absltest"),
        third_party("apiclient"),
    ],
)

pytype_strict_library(
    name = "google_drive_lib",
    srcs = [
        "google_drive.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":plugin_base",
        "//multitest_transport/util:env_lib",
        "//multitest_transport/util:errors_lib",
        "//multitest_transport/util:file_util_lib",
        "//multitest_transport/util:oauth2_util_lib",
        third_party("apiclient"),
    ],
)

py_test(
    name = "google_drive_test",
    srcs = [
        "google_drive_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":google_drive_lib",
        third_party("absl/testing:absltest"),
        third_party("apiclient"),
    ],
)

pytype_strict_library(
    name = "plugins",
    srcs = [
        "__init__.py",
    ],
    srcs_version = "PY2AND3",
    visibility = ["//multitest_transport"],
    deps = [
        ":android_lib",
        ":plugin_base",
        ":gcs_lib",
        ":google_drive_lib",
        ":web_hook_lib",
        third_party("apiclient"),
    ],
)

pytype_strict_library(
    name = "plugin_base",
    srcs = [
        "base.py",
        "constant.py",
    ],
    srcs_version = "PY2AND3",
    visibility = ["//multitest_transport"],
    deps = [
        ":registry_lib",
        "//multitest_transport/util",
        third_party("attr"),
        third_party("six"),
    ],
)

pytype_strict_library(
    name = "registry_lib",
    srcs = [
        "registry.py",
    ],
    srcs_version = "PY2AND3",
)

py_test(
    name = "registry_test",
    srcs = [
        "registry_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":registry_lib",
        third_party("absl/testing:absltest"),
        third_party("six"),
    ],
)

pytype_strict_library(
    name = "web_hook_lib",
    srcs = [
        "web_hook.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":plugin_base",
        "@tradefed_cluster//tradefed_cluster/services:app_manager_lib",
        third_party("six"),
    ],
)

py_test(
    name = "web_hook_test",
    srcs = [
        "web_hook_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":web_hook_lib",
        "//multitest_transport/models",
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        third_party("absl/testing:absltest"),
    ],
)
