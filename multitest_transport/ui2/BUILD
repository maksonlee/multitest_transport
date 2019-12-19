# Frontend application for MTT

load("//multitest_transport:adapter.bzl", "COMPILER_FLAGS", "MATERIAL_SASS_INCLUDE_PATHS", "js_binary", "karma_web_test_suite", "ng_module", "sass_binary", "sass_library", "third_party_js", "ts_config", "ts_development_sources")
load("@tradefed_cluster//tradefed_cluster:adapter.bzl", "Fileset", "FilesetEntry", "py_appengine_library", "third_party")

licenses(["notice"])

# Main Angular module
ng_module(
    name = "app_lib",
    srcs = [
        "main.ts",
    ],
    assets = [
        "index.html",
    ],
    deps = [
        third_party_js("angular2:core"),
        third_party_js("angular2:platform_browser"),
        "//multitest_transport/ui2/app",
    ],
)

################################################################################
# Styles                                                                       #
################################################################################

# Sass constants
sass_library(
    name = "constants",
    srcs = ["_constants.scss"],
    visibility = ["//multitest_transport"],
)

# shared styles for mtt lab
sass_library(
    name = "styles_lib",
    srcs = ["styles.scss"],
    visibility = ["//multitest_transport"],
    deps = [
        ":constants",
    ],
)

# Material theme and styling
sass_binary(
    name = "styles",
    src = "styles.scss",
    include_paths = MATERIAL_SASS_INCLUDE_PATHS,
    output_name = "styles.css",
    deps = [
        ":constants",
    ],
)

################################################################################
# Static files                                                                 #
################################################################################

filegroup(
    name = "images",
    srcs = glob(["images/*"]),
)

Fileset(
    name = "static_files",
    out = "static",
    entries = [
        FilesetEntry(
            files = [":styles"],
            destdir = "css",
        ),
        FilesetEntry(
            files = glob(["images/*"]),
            destdir = "images",
        ),
    ],
    visibility = ["//multitest_transport"],
)

################################################################################
# Development mode                                                             #
################################################################################

ts_development_sources(
    name = "dev_sources",
    visibility = ["//multitest_transport"],
    runtime_deps = [
        third_party_js("moment"),
        third_party_js("moment_duration_format"),
    ],
    deps = [
        ":app_lib",
    ],
)

################################################################################
# Production mode                                                              #
################################################################################

THIRD_PARTY_JS = [
    third_party_js("moment:moment_minified"),
    third_party_js("moment_duration_format"),
]

# Compiled production binary
js_binary(
    name = "compiled",
    defs = COMPILER_FLAGS,
    externs_list = [
        "//third_party/javascript/moment:externs",
    ],
    deps = [
        ":app_lib",
    ],
)

js_binary(
    name = "uncompiled",
    compile = False,
    deps = THIRD_PARTY_JS,
)

genrule(
    name = "app",
    srcs = [
        ":compiled.js",
        ":uncompiled-bundle.js",
    ],
    outs = ["app.js"],
    cmd = "cat $(SRCS) > $@",
    visibility = ["//multitest_transport"],
)

# Python server
py_appengine_library(
    name = "ui2",
    srcs = [
        "javascript_sources.py",
        "main.py",
    ],
    data = [
        "index.html",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        third_party("jinja2"),
        third_party("webapp2"),
    ],
)

################################################################################
# Testing                                                                      #
################################################################################

ts_development_sources(
    name = "dev_sources_for_testing",
    testonly = 1,
    runtime_deps = THIRD_PARTY_JS,
    deps = [
        "//multitest_transport/ui2/app:tests",
        "//multitest_transport/ui2/app/build_channels:tests",
        "//multitest_transport/ui2/app/device_actions:tests",
        "//multitest_transport/ui2/app/devices:tests",
        "//multitest_transport/ui2/app/services:tests",
        "//multitest_transport/ui2/app/settings:tests",
        "//multitest_transport/ui2/app/setup_wizard:tests",
        "//multitest_transport/ui2/app/shared:tests",
        "//multitest_transport/ui2/app/test_plans:tests",
        "//multitest_transport/ui2/app/test_runs:tests",
        "//multitest_transport/ui2/app/tests:tests_",
    ],
)

# TypeScript IDE configuration
ts_config(
    name = "tsconfig",
    deps = [
        ":app_lib",
        "//multitest_transport/ui2/app:tests",
        "//multitest_transport/ui2/app/build_channels:tests",
        "//multitest_transport/ui2/app/device_actions:tests",
        "//multitest_transport/ui2/app/devices:tests",
        "//multitest_transport/ui2/app/services:tests",
        "//multitest_transport/ui2/app/settings:tests",
        "//multitest_transport/ui2/app/setup_wizard:tests",
        "//multitest_transport/ui2/app/shared:tests",
        "//multitest_transport/ui2/app/test_plans:tests",
        "//multitest_transport/ui2/app/test_runs:tests",
        "//multitest_transport/ui2/app/tests:tests_",
    ],
)

karma_web_test_suite(
    name = "unit_tests",
    browsers = [
        "//testing/web/browsers:chrome-linux",
    ],
    data = [
        "styles.css",
        "tsconfig",
    ],
    manifest = ":dev_sources_for_testing",
)

