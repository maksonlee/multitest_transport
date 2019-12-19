load("//multitest_transport:adapter.bzl", "ng_module", "per_file_sass_binaries", "third_party_js")

licenses(["notice"])

per_file_sass_binaries(
    name = "styles",
    srcs = glob(["*.scss"]),
    deps = ["//multitest_transport/ui2:constants"],
)

ng_module(
    name = "devices",
    srcs = [
        "device_list.ts",
        "device_list_page.ts",
        "devices_module.ts",
    ],
    assets = [
        ":styles",
        "device_list.ng.html",
        "device_list_page.ng.html",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:cdk_collections"),
        third_party_js("angular2:core"),
        third_party_js("angular2:platform_browser"),
        third_party_js("rxjs"),
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/shared",
    ],
)

ng_module(
    name = "tests",
    testonly = True,
    srcs = ["device_list_test.ts"],
    visibility = ["//multitest_transport"],
    deps = [
        ":devices",
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("rxjs"),
        third_party_js("typings/jasmine"),
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/testing:jasmine_util",
        "//multitest_transport/ui2/app/testing:test_util",
    ],
)
