# MTT init scripts.

load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "third_party")

package(default_applicable_licenses = ["//multitest_transport:license"])

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
    deps = [
        third_party("absl/testing:absltest"),
    ],
)
