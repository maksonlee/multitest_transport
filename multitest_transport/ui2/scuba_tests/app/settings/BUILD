load("//multitest_transport:adapter.bzl", "ng_module", "third_party_js")
load("//multitest_transport/ui2/scuba_tests:build_defs.bzl", "karma_scuba_test")

licenses(["notice"])

karma_scuba_test(
    name = "scuba_tests",
    deps = [
        ":settings_scuba_tests",
    ],
)

ng_module(
    name = "settings_scuba_tests",
    testonly = True,
    srcs = [
        "setting_form_scuba_test.ts",
    ],
    visibility = ["//visibility:private"],
    deps = [
        "//multitest_transport/ui2/app/settings",
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("angular2:material_dialog"),
        third_party_js("angular2:platform_browser_animations"),
        third_party_js("angular2:platform_browser_dynamic_testing"),
        third_party_js("angular2:router"),
        third_party_js("angular2:router_testing"),
        third_party_js("rxjs"),
        "//javascript/angular2/testing/catalyst",
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/testing:test_util",
        "//multitest_transport/ui2/scuba_tests/testing:karma",
    ],
)
