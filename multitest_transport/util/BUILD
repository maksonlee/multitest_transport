load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_appengine_library", "py_appengine_test", "third_party")

licenses(["notice"])

# Get all the go/appsh rules. py_appengine_binary is part of the default
# build system, but for py_appengine_test and py_appengine_library you need:

PY_APPENGINE_ENVS = [{"runtime": "python27"}]

py_appengine_library(
    name = "analytics",
    srcs = [
        "analytics.py",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":util",
        "//multitest_transport/models",
    ],
)

py_appengine_test(
    name = "analytics_test",
    srcs = [
        "analytics_test.py",
    ],
    deps = [
        ":analytics",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_library(
    name = "env_lib",
    srcs = [
        "env.py",
    ],
)

py_library(
    name = "errors_lib",
    srcs = [
        "errors.py",
    ],
    srcs_version = "PY2AND3",
)

py_appengine_library(
    name = "gcs_util_lib",
    srcs = [
        "gcs_util.py",
    ],
    deps = [
        ":env_lib",
        ":file_util_lib",
        third_party("cloudstorage"),
    ],
)

py_appengine_test(
    name = "gcs_util_test",
    srcs = [
        "gcs_util_test.py",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":gcs_util_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "oauth2_util_lib",
    srcs = [
        "oauth2_util.py",
    ],
    deps = [
        # TODO: switch to oauth2client_4_0
        third_party("apiclient"),
    ],
)

py_appengine_test(
    name = "oauth2_util_test",
    srcs = [
        "oauth2_util_test.py",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":oauth2_util_lib",
        third_party("absl/testing:absltest"),
    ],
)

py_appengine_library(
    name = "tfc_client_lib",
    srcs = [
        "tfc_client.py",
    ],
    deps = [
        third_party("apiclient"),
        "@tradefed_cluster//tradefed_cluster:api_messages_lib",
    ],
)

py_appengine_test(
    name = "tfc_client_test",
    srcs = [
        "tfc_client_test.py",
    ],
    deps = [
        ":tfc_client_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "util",
    visibility = ["//multitest_transport"],
    deps = [
        ":env_lib",
        ":errors_lib",
        ":file_util_lib",
        ":gcs_util_lib",
        ":noop_handler",
        ":oauth2_util_lib",
        ":tfc_client_lib",
    ],
)

py_appengine_library(
    name = "file_util_lib",
    srcs = [
        "file_util.py",
    ],
    deps = [
        ":env_lib",
        third_party("apiclient"),
        third_party("cloudstorage"),
    ],
)

py_appengine_test(
    name = "file_util_test",
    srcs = [
        "file_util_test.py",
    ],
    data = [
        "test_data/test_package.zip",
        "test_data/test_package-empty.zip",
        "test_data/test_package-invalid.zip",
        "test_data/test_result.xml",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":file_util_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_library(
    name = "noop_handler",
    srcs = [
        "noop_handler.py",
    ],
)
