# MTT integration tests.

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "py_library", "py_test", "third_party")

licenses(["notice"])

py_library(
    name = "integration_util",
    srcs = [
        "integration_util.py",
    ],
    deps = [
        third_party("absl/testing:absltest"),
        third_party("docker"),
        third_party("portpicker"),
        third_party("requests"),
        third_party("retry"),
    ],
)

py_test(
    name = "base_integration_test",
    srcs = [
        "base_integration_test.py",
    ],
    python_version = "PY3",
    tags = ["local"],
    deps = [
        ":integration_util",
    ],
)

py_test(
    name = "event_handler_integration_test",
    srcs = [
        "event_handler_integration_test.py",
    ],
    python_version = "PY3",
    shard_count = 2,
    tags = ["local"],
    deps = [
        ":integration_util",
    ],
)

py_test(
    name = "file_server_integration_test",
    srcs = [
        "file_server_integration_test.py",
    ],
    data = [
        "test_data/android-cts.zip",
        "test_data/stdout.txt",
        "test_data/test_result.xml",
    ],
    python_version = "PY3",
    tags = ["local"],
    deps = [
        ":integration_util",
    ],
)

py_test(
    name = "test_scheduler_integration_test",
    srcs = [
        "test_scheduler_integration_test.py",
    ],
    python_version = "PY3",
    tags = ["local"],
    deps = [
        ":integration_util",
    ],
)

# Run with blaze test integration_test:image_tests --test_arg="--docker_image=<image to test>" --cache_test_results=no --flaky_test_attempts=3
test_suite(
    name = "image_tests",
    tests = [
        ":base_integration_test",
        ":event_handler_integration_test",
        ":file_server_integration_test",
        ":test_scheduler_integration_test",
    ],
)

# Combination of all integration tests for CI
test_suite(
    name = "integration_test",
    tests = [
        ":image_tests",
        "//multitest_transport/cli:integration_test",
    ],
)