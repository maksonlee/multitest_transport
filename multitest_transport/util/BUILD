load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_library", "py_test", "pytype_strict_library", "third_party")

package(default_visibility = ["//multitest_transport"])

licenses(["notice"])

pytype_strict_library(
    name = "analytics_lib",
    srcs = [
        "analytics.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":env_lib",
        ":tfc_client_lib",
        "@tradefed_cluster//tradefed_cluster:common_lib",
        "@tradefed_cluster//tradefed_cluster/services:task_scheduler_lib",
    ],
)

py_test(
    name = "analytics_test",
    srcs = [
        "analytics_test.py",
    ],
    data = [
        "//multitest_transport/gae_configs",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":analytics_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "analytics_uploader_lib",
    srcs = [
        "analytics_uploader.py",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":util",
        "//multitest_transport/models",
        third_party("flask"),
        third_party("six"),
    ],
)

py_test(
    name = "analytics_uploader_test",
    srcs = [
        "analytics_uploader_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        third_party("six"),
        third_party("absl/testing:absltest"),
        ":analytics_uploader_lib",
        ":env_lib",
        "//multitest_transport/models:ndb_models_lib",
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "env_lib",
    srcs = [
        "env.py",
    ],
    srcs_version = "PY2AND3",
)

pytype_strict_library(
    name = "errors_lib",
    srcs = [
        "errors.py",
    ],
    srcs_version = "PY2AND3",
)

pytype_strict_library(
    name = "oauth2_util_lib",
    srcs = [
        "oauth2_util.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        "@tradefed_cluster//tradefed_cluster/util:ndb_shim_lib",
        third_party("attr"),
        third_party("google/auth:credentials"),
        third_party("google/oauth2:credentials"),
        third_party("google_auth_httplib2"),
        third_party("google_auth_oauthlib"),
        third_party("six"),
    ],
)

py_test(
    name = "oauth2_util_test",
    srcs = [
        "oauth2_util_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":oauth2_util_lib",
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        third_party("mock"),
        third_party("google/oauth2:service_account"),
        third_party("six"),
    ],
)

# Use py_library as sqlalchemy imports don't work with pytype_strict_library
py_library(
    name = "sql_util_lib",
    srcs = ["sql_util.py"],
    srcs_version = "PY2AND3",
    deps = [
        third_party("sqlalchemy"),
        third_party("sqlalchemy_utils"),
    ],
)

py_test(
    name = "sql_util_test",
    srcs = [
        "sql_util_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":sql_util_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
        third_party("protorpc"),
        third_party("sqlalchemy"),
        third_party("sqlalchemy_utils"),
        third_party("sqlite3"),
    ],
)

pytype_strict_library(
    name = "tfc_client_lib",
    srcs = [
        "tfc_client.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":env_lib",
        "@tradefed_cluster//tradefed_cluster:api_messages_lib",
        "@tradefed_cluster//tradefed_cluster:common_lib",
        "@tradefed_cluster//tradefed_cluster/services:app_manager_lib",
        third_party("apiclient"),
        third_party("httplib2"),
        third_party("protorpc"),
        third_party("requests"),
    ],
)

py_test(
    name = "tfc_client_test",
    srcs = [
        "tfc_client_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":tfc_client_lib",
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        "@tradefed_cluster//tradefed_cluster/plugins:base_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_library(
    name = "util",
    visibility = ["//multitest_transport"],
    deps = [
        ":analytics_lib",
        ":env_lib",
        ":errors_lib",
        ":file_util_lib",
        ":noop_handler",
        ":oauth2_util_lib",
        ":sql_util_lib",
        ":tfc_client_lib",
        ":xts_result_lib",
    ],
)

pytype_strict_library(
    name = "file_util_lib",
    srcs = [
        "file_util.py",
    ],
    deps = [
        ":env_lib",
        third_party("apiclient"),
        third_party("attr"),
        third_party("cloudstorage"),
        third_party("six"),
    ],
)

py_test(
    name = "file_util_test",
    srcs = [
        "file_util_test.py",
    ],
    data = [
        "test_data/FILES",
        "test_data/test_package.zip",
        "test_data/test_package-empty.zip",
        "test_data/test_package-invalid.zip",
        "test_data/test_result.xml",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":env_lib",
        ":file_util_lib",
        third_party("absl/testing:absltest"),
        third_party("absl/testing:parameterized"),
        third_party("mock"),
        third_party("six"),
    ],
)

pytype_strict_library(
    name = "noop_handler",
    srcs = [
        "noop_handler.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        "@tradefed_cluster//tradefed_cluster:common_lib",
        third_party("flask"),
    ],
)

pytype_strict_library(
    name = "xts_result_lib",
    srcs = [
        "xts_result.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        third_party("attr"),
        third_party("defusedxml"),
        third_party("protorpc"),
    ],
)

py_test(
    name = "xts_result_test",
    srcs = [
        "xts_result_test.py",
    ],
    data = [
        "test_data/test_result.xml",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":xts_result_lib",
        third_party("absl/testing:absltest"),
    ],
)
