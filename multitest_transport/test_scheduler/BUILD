# A backend service for Multi-Test Transport

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_appengine_library", "py_appengine_test", "third_party")

licenses(["notice"])

PY_APPENGINE_ENVS = [
    {
        "runtime": "python27",
        "libraries": {
            "webapp2": "latest",
        },
    },
]

py_appengine_library(
    name = "download_util_lib",
    srcs = [
        "download_util.py",
    ],
    deps = [
        third_party("cloudstorage"),
        "//multitest_transport/models",
    ],
)

py_appengine_test(
    name = "download_util_test",
    srcs = [
        "download_util_test.py",
    ],
    use_public_sdk = 1,
    deps = [
        ":download_util_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "test_kicker_lib",
    srcs = [
        "test_kicker.py",
    ],
    deps = [
        ":download_util_lib",
        ":test_run_manager_lib",
        "//multitest_transport/models",
        "//multitest_transport/util",
        "//multitest_transport/util:analytics",
        "@tradefed_cluster//tradefed_cluster:api_messages_lib",
    ],
)

py_appengine_test(
    name = "test_kicker_test",
    srcs = [
        "test_kicker_test.py",
    ],
    data = [
        "queue.yaml",
    ],
    use_public_sdk = 1,
    deps = [
        ":test_kicker_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
        third_party("webtest"),
    ],
)

py_appengine_library(
    name = "test_plan_kicker_lib",
    srcs = [
        "test_plan_kicker.py",
    ],
    deps = [
        ":download_util_lib",
        ":test_kicker_lib",
        ":test_run_manager_lib",
        third_party("croniter"),
        "//multitest_transport/models",
        third_party("pytz"),
    ],
)

py_appengine_test(
    name = "test_plan_kicker_test",
    srcs = [
        "test_plan_kicker_test.py",
    ],
    data = [
        "queue.yaml",
    ],
    use_public_sdk = 1,
    deps = [
        ":test_plan_kicker_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "test_output_uploader_lib",
    srcs = [
        "test_output_uploader.py",
    ],
    deps = [
        "//multitest_transport/models",
        "//multitest_transport/util",
    ],
)

py_appengine_test(
    name = "test_output_uploader_test",
    srcs = [
        "test_output_uploader_test.py",
    ],
    data = [
        "queue.yaml",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":test_output_uploader_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "tfc_event_handler_lib",
    srcs = [
        "tfc_event_handler.py",
    ],
    deps = [
        ":test_output_uploader_lib",
        "//multitest_transport/models",
        "//multitest_transport/util:analytics",
        "@tradefed_cluster//tradefed_cluster:api_messages_lib",
    ],
)

py_appengine_test(
    name = "tfc_event_handler_test",
    srcs = [
        "tfc_event_handler_test.py",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":tfc_event_handler_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "test_run_manager_lib",
    srcs = [
        "test_run_manager.py",
    ],
    deps = [
        ":tfc_event_handler_lib",
        "//multitest_transport/models",
        "//multitest_transport/util",
    ],
)

py_appengine_test(
    name = "test_run_manager_test",
    srcs = [
        "test_run_manager_test.py",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":test_run_manager_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "test_scheduler",
    srcs = [
        "test_scheduler.py",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":test_kicker_lib",
        ":test_plan_kicker_lib",
        ":test_run_manager_lib",
        ":tfc_event_handler_lib",
        "//multitest_transport/models",
        "//multitest_transport/util",
    ],
)

py_appengine_test(
    name = "test_scheduler_test",
    srcs = [
        "test_scheduler_test.py",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":test_scheduler",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)
