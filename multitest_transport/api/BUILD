# MTT API handlers.

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_appengine_library", "py_appengine_test", "third_party")

licenses(["notice"])

PY_APPENGINE_TEST_ENVS = [
    {
        "runtime": "python27",
        "libraries": {
            "webapp2": "latest",
            "PIL": "latest",
        },
    },
]

py_appengine_library(
    name = "api",
    visibility = ["//multitest_transport"],
    deps = [
        ":server_lib",
    ],
)

py_appengine_library(
    name = "api_test_util_lib",
    srcs = [
        "api_test_util.py",
    ],
    deps = [
        third_party("absl/testing:absltest"),
        third_party("webtest"),
    ],
)

py_appengine_library(
    name = "base_lib",
    srcs = [
        "base.py",
    ],
    deps = [
        "//multitest_transport/models",
    ],
)

py_appengine_library(
    name = "build_channel_api_lib",
    srcs = [
        "build_channel_api.py",
    ],
    deps = [
        ":base_lib",
    ],
)

py_appengine_test(
    name = "build_channel_api_test",
    srcs = [
        "build_channel_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":build_channel_api_lib",
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "build_channel_provider_api_lib",
    srcs = [
        "build_channel_provider_api.py",
    ],
    deps = [
        ":base_lib",
    ],
)

py_appengine_test(
    name = "build_channel_provider_api_test",
    srcs = [
        "build_channel_provider_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":build_channel_provider_api_lib",
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "config_set_api_lib",
    srcs = [
        "config_set_api.py",
    ],
    deps = [
        ":base_lib",
        "//multitest_transport/test_scheduler",
    ],
)

py_appengine_test(
    name = "config_set_api_test",
    srcs = [
        "config_set_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":config_set_api_lib",
    ],
)

py_appengine_library(
    name = "device_action_api_lib",
    srcs = [
        "device_action_api.py",
    ],
    deps = [
        ":base_lib",
    ],
)

py_appengine_test(
    name = "device_action_api_test",
    srcs = [
        "device_action_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":device_action_api_lib",
    ],
)

py_appengine_library(
    name = "node_config_api_lib",
    srcs = [
        "node_config_api.py",
    ],
    deps = [
        ":base_lib",
    ],
)

py_appengine_test(
    name = "node_config_api_test",
    srcs = [
        "node_config_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":node_config_api_lib",
    ],
)

py_appengine_library(
    name = "private_node_config_api_lib",
    srcs = [
        "private_node_config_api.py",
    ],
    deps = [
        ":base_lib",
    ],
)

py_appengine_test(
    name = "private_node_config_api_test",
    srcs = [
        "private_node_config_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":private_node_config_api_lib",
    ],
)

py_appengine_library(
    name = "server_lib",
    srcs = [
        "server.py",
    ],
    deps = [
        ":build_channel_api_lib",
        ":build_channel_provider_api_lib",
        ":config_set_api_lib",
        ":device_action_api_lib",
        ":node_config_api_lib",
        ":private_node_config_api_lib",
        ":test_api_lib",
        ":test_plan_api_lib",
        ":test_run_action_api_lib",
        ":test_run_api_lib",
        "@tradefed_cluster//tradefed_cluster:api_lib",
    ],
)

py_appengine_library(
    name = "test_api_lib",
    srcs = [
        "test_api.py",
    ],
    deps = [
        ":base_lib",
    ],
)

py_appengine_test(
    name = "test_api_test",
    srcs = [
        "test_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":test_api_lib",
    ],
)

py_appengine_library(
    name = "test_plan_api_lib",
    srcs = [
        "test_plan_api.py",
    ],
    deps = [
        ":base_lib",
        third_party("croniter"),
        "//multitest_transport/test_scheduler",
    ],
)

py_appengine_test(
    name = "test_plan_api_test",
    srcs = [
        "test_plan_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":test_plan_api_lib",
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "test_run_action_api_lib",
    srcs = [
        "test_run_action_api.py",
    ],
    deps = [
        ":base_lib",
        "//multitest_transport/util",
    ],
)

py_appengine_test(
    name = "test_run_action_api_test",
    srcs = [
        "test_run_action_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":test_run_action_api_lib",
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "test_run_api_lib",
    srcs = [
        "test_run_api.py",
    ],
    deps = [
        ":base_lib",
        "//multitest_transport/test_scheduler",
        "@tradefed_cluster//tradefed_cluster:datastore_util_lib",
    ],
)

py_appengine_test(
    name = "test_run_api_test",
    srcs = [
        "test_run_api_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":api_test_util_lib",
        ":test_run_api_lib",
        third_party("mock"),
    ],
)
