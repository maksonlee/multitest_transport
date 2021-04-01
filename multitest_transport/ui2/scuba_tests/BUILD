load("//tools/build_defs/testing:bzl_library.bzl", "bzl_library")

# Scuba related test files
load("//testing/web/build_defs:web.bzl", "custom_browser")

licenses(["notice"])

custom_browser(
    name = "chrome-linux",
    browser = "//testing/web/browsers:chrome-linux",
    metadata = ["chrome-linux-metadata.json"],
    visibility = ["//multitest_transport"],
)

bzl_library(
    name = "build_defs_bzl",
    srcs = ["build_defs.bzl"],
    parse_tests = False,
    visibility = ["//visibility:private"],
)
