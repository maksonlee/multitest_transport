load("//multitest_transport:adapter.bzl", "ng_module", "third_party_js")
load("//multitest_transport/ui2/scuba_tests:build_defs.bzl", "karma_scuba_test")

licenses(["notice"])

karma_scuba_test(
    name = "scuba_tests",
    deps = [
        ":shared_scuba_tests",
    ],
)

ng_module(
    name = "shared_scuba_tests",
    testonly = True,
    srcs = [
        "form_error_info_scuba_test.ts",
        "list_form_scuba_test.ts",
        "name_value_pair_list_form_scuba_test.ts",
        "status_button_scuba_test.ts",
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
        "//third_party/javascript/angular2:platform_browser_dynamic_testing",
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/shared",
        "//multitest_transport/ui2/scuba_tests/testing:karma",
    ],
)
