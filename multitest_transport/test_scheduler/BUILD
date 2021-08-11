# A backend service for Multi-Test Transport
load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_test", "pytype_strict_library", "third_party")

package(default_visibility = ["//multitest_transport"])

licenses(["notice"])

pytype_strict_library(
    name = "download_util_lib",
    srcs = [
        "download_util.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        "//multitest_transport/models:build_lib",
        "//multitest_transport/models:event_log_lib",
        "//multitest_transport/models:ndb_models_lib",
        "//multitest_transport/util:file_util_lib",
        "@tradefed_cluster//tradefed_cluster:api_common_lib",
        "@tradefed_cluster//tradefed_cluster:common_lib",
        "@tradefed_cluster//tradefed_cluster/util:ndb_shim_lib",
        third_party("concurrent:futures"),
        third_party("six"),
    ],
)

py_test(
    name = "download_util_test",
    srcs = [
        "download_util_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":download_util_lib",
        "//net/proto2/python/public:use_pure_python",  # Automatically added go/proto_python_default
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "test_kicker_lib",
    srcs = [
        "test_kicker.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":download_util_lib",
        ":test_run_manager_lib",
        "//third_party/py/flask",
        "//multitest_transport/models",
        "//multitest_transport/util",
        "@tradefed_cluster//tradefed_cluster:api_messages_lib",
        "@tradefed_cluster//tradefed_cluster:common_lib",
        "@tradefed_cluster//tradefed_cluster/services:task_scheduler_lib",
        "@tradefed_cluster//tradefed_cluster/util:ndb_shim_lib",
        third_party("googleapiclient"),
        third_party("protorpc"),
        third_party("six"),
    ],
)

py_test(
    name = "test_kicker_test",
    srcs = [
        "test_kicker_test.py",
    ],
    data = [
        "//multitest_transport/gae_configs",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":download_util_lib",
        ":test_kicker_lib",
        "//net/proto2/python/public:use_pure_python",  # Automatically added go/proto_python_default
        "//multitest_transport/models:build_lib",
        "//multitest_transport/models:messages_lib",
        "//multitest_transport/models:ndb_models_lib",
        "//multitest_transport/models:test_run_hook_lib",
        "//multitest_transport/util:analytics_lib",
        "//multitest_transport/util:env_lib",
        "//multitest_transport/util:file_util_lib",
        "//multitest_transport/util:tfc_client_lib",
        "@tradefed_cluster//tradefed_cluster:api_messages_lib",
        "@tradefed_cluster//tradefed_cluster:common_lib",
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        "@tradefed_cluster//tradefed_cluster/util:ndb_shim_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
        third_party("webtest"),
    ],
)

pytype_strict_library(
    name = "test_plan_kicker_lib",
    srcs = [
        "test_plan_kicker.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":download_util_lib",
        ":test_kicker_lib",
        ":test_run_manager_lib",
        "//multitest_transport/models",
        "@tradefed_cluster//tradefed_cluster:common_lib",
        "@tradefed_cluster//tradefed_cluster/services:task_scheduler_lib",
        third_party("croniter"),
        third_party("flask"),
        third_party("pytz"),
        third_party("retry"),
        third_party("six"),
    ],
)

py_test(
    name = "test_plan_kicker_test",
    srcs = [
        "test_plan_kicker_test.py",
    ],
    data = [
        "//multitest_transport/gae_configs",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":test_plan_kicker_lib",
        "//net/proto2/python/public:use_pure_python",  # Automatically added go/proto_python_default
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "test_result_handler_lib",
    srcs = [
        "test_result_handler.py",
    ],
    srcs_version = "PY3",
    deps = [
        "//multitest_transport/models",
        "//multitest_transport/util",
        "@tradefed_cluster//tradefed_cluster/services:task_scheduler_lib",
        "@tradefed_cluster//tradefed_cluster/util:ndb_shim_lib",
    ],
)

py_test(
    name = "test_result_handler_test",
    srcs = [
        "test_result_handler_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":test_result_handler_lib",
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        "@tradefed_cluster//tradefed_cluster/services:task_scheduler_lib",
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "test_scheduler_lib",
    srcs = [
        "test_scheduler.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":test_kicker_lib",
        ":test_plan_kicker_lib",
        ":test_run_manager_lib",
        "//multitest_transport/models",
        "@tradefed_cluster//tradefed_cluster:common_lib",
        "@tradefed_cluster//tradefed_cluster/util:ndb_shim_lib",
        third_party("flask"),
    ],
)

py_test(
    name = "test_scheduler_test",
    srcs = [
        "test_scheduler_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":test_scheduler_lib",
        "//net/proto2/python/public:use_pure_python",  # Automatically added go/proto_python_default
        "//third_party/py/absl/testing:absltest",
        "//multitest_transport/models:messages_lib",
        "//multitest_transport/models:ndb_models_lib",
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "tfc_event_handler_lib",
    srcs = [
        "tfc_event_handler.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        ":test_result_handler_lib",
        ":test_scheduler_lib",
        "//multitest_transport/models",
        "//multitest_transport/util",
        "@tradefed_cluster//tradefed_cluster:api_messages_lib",
        "@tradefed_cluster//tradefed_cluster:common_lib",
        "@tradefed_cluster//tradefed_cluster/services:task_scheduler_lib",
        "@tradefed_cluster//tradefed_cluster/util:ndb_shim_lib",
        third_party("flask"),
        third_party("protorpc"),
    ],
)

py_test(
    name = "tfc_event_handler_test",
    srcs = [
        "tfc_event_handler_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":test_result_handler_lib",
        ":tfc_event_handler_lib",
        "//net/proto2/python/public:use_pure_python",  # Automatically added go/proto_python_default
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "test_run_manager_lib",
    srcs = [
        "test_run_manager.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        "//multitest_transport/models",
        "//multitest_transport/util",
    ],
)

py_test(
    name = "test_run_manager_test",
    srcs = [
        "test_run_manager_test.py",
    ],
    python_version = "PY3",
    srcs_version = "PY3",
    deps = [
        ":test_run_manager_lib",
        "//net/proto2/python/public:use_pure_python",  # Automatically added go/proto_python_default
        "@tradefed_cluster//tradefed_cluster:testbed_dependent_test_lib",
        third_party("mock"),
    ],
)

pytype_strict_library(
    name = "test_scheduler",
    srcs_version = "PY2AND3",
    visibility = ["//multitest_transport"],
    deps = [
        ":test_kicker_lib",
        ":test_plan_kicker_lib",
        ":test_run_manager_lib",
        ":test_scheduler_lib",
    ],
)
