load("//multitest_transport:adapter.bzl", "ng_module", "third_party_js", "ts_library")

# A package for testing utilities
licenses(["notice"])

ts_library(
    name = "test_util",
    srcs = [
        "test_util.ts",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        third_party_js("moment:typings"),
        "//multitest_transport/ui2/app/services",
    ],
)

ng_module(
    name = "jasmine_util",
    srcs = ["jasmine_util.ts"],
    visibility = ["//multitest_transport"],
    deps = [
        third_party_js("angular2:core"),
        third_party_js("angular2:platform_browser"),
        third_party_js("typings/jasmine"),
    ],
)
