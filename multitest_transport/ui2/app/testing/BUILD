load("//multitest_transport:adapter.bzl", "ng_module", "third_party_js")

# A package for testing utilities
licenses(["notice"])

package(
    default_applicable_licenses = ["//multitest_transport:license"],
    default_visibility = ["//multitest_transport"],
)

ng_module(
    name = "init_tests",
    testonly = True,
    srcs = ["init_tests.ts"],
    deps = [
        third_party_js("angular2:core_testing"),
        third_party_js("angular2:platform_browser_dynamic_testing"),
    ],
)

ng_module(
    name = "test_util",
    srcs = [
        "mtt_lab_mocks.ts",
        "mtt_mocks.ts",
    ],
    deps = [
        third_party_js("moment:typings"),
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/shared",
    ],
)

ng_module(
    name = "jasmine_util",
    srcs = ["jasmine_util.ts"],
    deps = [
        third_party_js("angular2:core"),
        third_party_js("angular2:platform_browser"),
        third_party_js("typings/jasmine"),
    ],
)

ng_module(
    name = "angular_util",
    srcs = ["activated_route_stub.ts"],
    deps = [
        third_party_js("angular2:router"),
        third_party_js("rxjs"),
    ],
)
