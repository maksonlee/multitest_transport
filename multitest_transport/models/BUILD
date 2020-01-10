# MTT data models.

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_appengine_library", "py_appengine_test", "third_party")

licenses(["notice"])

PY_APPENGINE_ENVS = [{"runtime": "python27"}]

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
    name = "build_lib",
    srcs = [
        "build.py",
    ],
    envs = PY_APPENGINE_ENVS,
    deps = [
        ":ndb_models_lib",
        "//multitest_transport/plugins",
        "//multitest_transport/util",
        third_party("oauth2client_4_0:oauth2client"),
    ],
)

py_appengine_test(
    name = "build_test",
    srcs = [
        "build_test.py",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":build_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)

py_appengine_library(
    name = "config_encoder_lib",
    srcs = [
        "config_encoder.py",
    ],
    envs = PY_APPENGINE_ENVS,
    deps = [
        ":messages_lib",
    ],
)

py_appengine_test(
    name = "config_encoder_test",
    srcs = [
        "config_encoder_test.py",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":config_encoder_lib",
        third_party("absl/testing:absltest"),
    ],
)

py_appengine_library(
    name = "config_set_helper_lib",
    srcs = [
        "config_set_helper.py",
    ],
    envs = PY_APPENGINE_ENVS,
)

py_appengine_test(
    name = "config_set_helper_test",
    srcs = [
        "config_set_helper_test.py",
    ],
    envs = PY_APPENGINE_ENVS,
    use_public_sdk = 1,
    deps = [
        ":build_lib",
        ":config_encoder_lib",
        ":config_set_helper_lib",
        third_party("absl/testing:absltest"),
        "//multitest_transport/test_scheduler",
    ],
)

py_appengine_library(
    name = "messages_lib",
    srcs = [
        "messages.py",
    ],
    deps = [
        ":build_lib",
        ":ndb_models_lib",
        "//multitest_transport/plugins",
    ],
)

py_appengine_test(
    name = "messages_test",
    srcs = [
        "messages_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":messages_lib",
        third_party("absl/testing:absltest"),
    ],
)

py_appengine_library(
    name = "models",
    visibility = ["//multitest_transport"],
    deps = [
        ":build_lib",
        ":config_encoder_lib",
        ":config_set_helper_lib",
        ":messages_lib",
        ":ndb_models_lib",
        ":test_run_hook_lib",
    ],
)

py_appengine_library(
    name = "ndb_models_lib",
    srcs = [
        "ndb_models.py",
    ],
    envs = PY_APPENGINE_ENVS,
    deps = [
        "//multitest_transport/util",
        third_party("oauth2client_4_0:oauth2client"),
        "@tradefed_cluster//tradefed_cluster:common_lib",
    ],
)

py_appengine_library(
    name = "test_run_hook_lib",
    srcs = ["test_run_hook.py"],
    deps = [
        ":ndb_models_lib",
        "//multitest_transport/plugins",
        third_party("six"),
    ],
)

py_appengine_test(
    name = "test_run_hook_test",
    srcs = [
        "test_run_hook_test.py",
    ],
    deps = [
        ":test_run_hook_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
    ],
)
