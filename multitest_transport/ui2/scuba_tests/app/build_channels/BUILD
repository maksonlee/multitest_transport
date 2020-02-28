load("//multitest_transport:adapter.bzl", "karma_web_test_suite", "ng_module", "third_party_js", "ts_development_sources")
load("//testing/karma/karma_scuba_framework:karma_scuba.bzl", "karma_scuba_plugins")

licenses(["notice"])

ng_module(
    name = "build_channels_scuba_tests",
    testonly = True,
    srcs = [
        "build_channel_edit_page_scuba_test.ts",
        "build_channel_item_scuba_test.ts",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        "//multitest_transport/ui2/app/build_channels",
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("angular2:material_dialog"),
        third_party_js("angular2:platform_browser_animations"),
        third_party_js("angular2:router"),
        third_party_js("angular2:router_testing"),
        third_party_js("rxjs"),
        "//javascript/angular2/testing/catalyst",
        "//third_party/javascript/angular2:platform_browser_dynamic_testing",
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/scuba_tests/testing:karma",
    ],
)

ts_development_sources(
    name = "dev_sources_for_test",
    testonly = 1,
    deps = [
        ":build_channels_scuba_tests",
    ],
)

karma_web_test_suite(
    name = "scuba_tests",
    browsers = [
        "//testing/web/browsers:chrome-linux",
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
