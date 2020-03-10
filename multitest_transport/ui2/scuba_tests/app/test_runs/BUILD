load("//multitest_transport:adapter.bzl", "karma_web_test_suite", "ng_module", "third_party_js", "ts_development_sources")
load("//testing/karma/karma_scuba_framework:karma_scuba.bzl", "karma_scuba_plugins")

licenses(["notice"])

ng_module(
    name = "test_runs_scuba_tests",
    testonly = True,
    srcs = [
        "test_run_failures_scuba_test.ts",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("angular2:material_dialog"),
        third_party_js("angular2:platform_browser_animations"),
        third_party_js("angular2:router"),
        third_party_js("angular2:router_testing"),
        third_party_js("rxjs"),
        "//javascript/angular2/testing/catalyst",
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/test_runs",
        "//multitest_transport/ui2/scuba_tests/testing:karma",
    ],
)

ts_development_sources(
    name = "dev_sources_for_test",
    testonly = 1,
    deps = [
        ":test_runs_scuba_tests",
    ],
)

# TODO Define custom build rule to automatically generate build
karma_web_test_suite(
    name = "scuba_tests",
    browsers = [
        "//multitest_transport/ui2/scuba_tests:chrome-linux",
    ],
    data = [
        "//javascript/angular2/components/testing:google_sans.css",
        "//javascript/angular2/components/testing:material_icons.css",
        "//javascript/angular2/components/testing:product_sans.css",
        "//javascript/angular2/components/testing:roboto.css",
        "//multitest_transport/ui2:styles.css",
    ],
    karma_plugins = karma_scuba_plugins(),
    manifest = ":dev_sources_for_test",
)
