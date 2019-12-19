load("//multitest_transport:adapter.bzl", "ng_module", "per_file_sass_binaries", "third_party_js")

licenses(["notice"])

per_file_sass_binaries(
    name = "styles",
    srcs = glob(["*.scss"]),
    deps = ["//multitest_transport/ui2:constants"],
)

ng_module(
    name = "device_actions",
    srcs = [
        "device_action_edit_page.ts",
        "device_action_list.ts",
        "device_action_picker.ts",
        "device_actions_module.ts",
        "target_preparer_form.ts",
        "target_preparer_option_form.ts",
    ],
    assets = [
        ":styles",
        "device_action_edit_page.ng.html",
        "device_action_list.ng.html",
        "device_action_picker.ng.html",
        "target_preparer_form.ng.html",
        "target_preparer_option_form.ng.html",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:cdk_collections"),
        third_party_js("angular2:cdk_drag_drop"),
        third_party_js("angular2:core"),
        third_party_js("angular2:forms"),
        third_party_js("angular2:material_button"),
        third_party_js("angular2:material_table"),
        third_party_js("angular2:platform_browser"),
        third_party_js("angular2:router"),
        third_party_js("rxjs"),
        "//multitest_transport/ui2/app/build_channels",
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/shared",
    ],
)

ng_module(
    name = "tests",
    testonly = True,
    srcs = [
        "device_action_edit_page_test.ts",
        "device_action_list_test.ts",
        "device_action_picker_test.ts",
        "target_preparer_form_test.ts",
        "target_preparer_option_form_test.ts",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":device_actions",
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("angular2:platform_browser"),
        third_party_js("angular2:platform_browser_animations"),
        third_party_js("angular2:router"),
        third_party_js("angular2:router_testing"),
        third_party_js("rxjs"),
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/testing:jasmine_util",
        "//multitest_transport/ui2/app/testing:test_util",
    ],
)
