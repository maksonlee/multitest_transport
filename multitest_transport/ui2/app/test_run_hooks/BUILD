load("//multitest_transport:adapter.bzl", "ng_module", "per_file_sass_binaries", "third_party_js")

licenses(["notice"])

per_file_sass_binaries(
    name = "styles",
    srcs = glob(["*.scss"]),
    deps = ["//multitest_transport/ui2:constants"],
)

ng_module(
    name = "test_run_hooks",
    srcs = [
        "test_run_hook_list.ts",
        "test_run_hook_picker.ts",
        "test_run_hooks_module.ts",
    ],
    assets = [
        ":styles",
        "test_run_hook_list.ng.html",
        "test_run_hook_picker.ng.html",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:core"),
        third_party_js("angular2:cdk_collections"),
        third_party_js("angular2:cdk_drag_drop"),
        third_party_js("rxjs"),
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/shared",
    ],
)

ng_module(
    name = "tests",
    testonly = True,
    srcs = [
        "test_run_hook_list_test.ts",
        "test_run_hook_picker_test.ts",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":test_run_hooks",
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("angular2:platform_browser_animations"),
        third_party_js("rxjs"),
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/testing:jasmine_util",
    ],
)
