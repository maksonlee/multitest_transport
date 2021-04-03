# MTT init scripts.

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "third_party")

licenses(["notice"])

filegroup(
    name = "scripts",
    srcs = glob(
        ["**"],
        exclude = [
            "BUILD",
            "**/*_test.py",
        ],
    ),
    visibility = ["//multitest_transport"],
)

py_test(
    name = "gen_subnets_test",
    srcs = [
        "gen_subnets.py",
        "gen_subnets_test.py",
    ],
    python_version = "PY3",
    deps = [
        third_party("absl/testing:absltest"),
    ],
)
