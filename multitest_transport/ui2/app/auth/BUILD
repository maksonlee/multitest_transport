load("//multitest_transport:adapter.bzl", "ng_module", "per_file_sass_binaries", "third_party_js")

licenses(["notice"])

per_file_sass_binaries(
    name = "styles",
    srcs = glob(["*.scss"]),
    visibility = ["//visibility:private"],
    deps = ["//multitest_transport/ui2:constants"],
)

ng_module(
    name = "auth",
    srcs = [
        "auth_module.ts",
        "auth_return_page.ts",
        "login_button.ts",
    ],
    assets = [
        ":styles",
        "login_button.ng.html",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        third_party_js("angular2:core"),
        "//third_party/javascript/rxjs",
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/shared",
    ],
)

ng_module(
    name = "tests",
    testonly = True,
    srcs = [
        "login_button_test.ts",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":auth",
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("angular2:material_dialog"),
        third_party_js("angular2:platform_browser_animations"),
        third_party_js("angular2:router"),
        third_party_js("angular2:router_testing"),
        third_party_js("rxjs"),
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/shared",
        "//multitest_transport/ui2/app/testing:jasmine_util",
        "//multitest_transport/ui2/app/testing:test_util",
    ],
)
