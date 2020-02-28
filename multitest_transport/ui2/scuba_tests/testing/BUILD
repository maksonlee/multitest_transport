load("//multitest_transport:adapter.bzl", "ts_library")

ts_library(
    name = "karma",
    testonly = True,
    srcs = [
        "karma_env.ts",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        "//testing/js/jasmine/axe",
        "//testing/karma/karma_scuba_framework",
        "//testing/screendiffing/typescript/proto_parsing:proto_types",
        "//third_party/javascript/typings/css_font_loading_module",
        "//third_party/javascript/typings/jasmine",
    ],
)
