load("//multitest_transport:adapter.bzl", "ng_module", "third_party_js")
load("//multitest_transport/ui2/scuba_tests:build_defs.bzl", "karma_scuba_test")

licenses(["notice"])

karma_scuba_test(
    name = "scuba_tests",
    deps = [
        ":devices_actions_scuba_tests",
    ],
)

ng_module(
    name = "devices_actions_scuba_tests",
    testonly = True,
    srcs = [
        "device_action_list_scuba_test.ts",
        "device_action_picker_scuba_test.ts",
        "target_preparer_form_scuba_test.ts",
        "tradefed_config_option_form_scuba_test.ts",
    ],
    visibility = ["//visibility:private"],
    deps = [
        "//multitest_transport/ui2/app/device_actions",
        "//multitest_transport/ui2/app/testing:test_util",
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
