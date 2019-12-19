# MTT core services.

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
    name = "config_loader_lib",
    srcs = [
        "config_loader.py",
    ],
    deps = [
        "//multitest_transport/models",
        third_party("yaml"),
    ],
)

py_appengine_test(
    name = "config_loader_test",
    srcs = [
        "config_loader_test.py",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":config_loader_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
        third_party("webtest"),
    ],
)

py_appengine_library(
    name = "cron_kicker_lib",
    srcs = [
        "cron_kicker.py",
    ],
    srcs_version = "PY2AND3",
    deps = [
        third_party("antlr3:v3_1_1"),
        third_party("pytz"),
        third_party("six"),
        third_party("yaml"),
    ],
)

py_appengine_test(
    name = "cron_kicker_test",
    srcs = [
        "cron_kicker_test.py",
    ],
    data = [
        "queue.yaml",
    ],
    envs = PY_APPENGINE_TEST_ENVS,
    use_public_sdk = 1,
    deps = [
        ":cron_kicker_lib",
        third_party("absl/testing:absltest"),
        third_party("mock"),
        third_party("webtest"),
    ],
)

py_appengine_library(
    name = "app_lib",
    srcs = [
        "app.py",
    ],
    deps = [
        ":config_loader_lib",
        ":cron_kicker_lib",
        "//multitest_transport/util",
    ],
)

py_appengine_library(
    name = "core",
    visibility = ["//multitest_transport"],
    deps = [
        ":app_lib",
    ],
)
