load("//multitest_transport:adapter.bzl", "ng_module", "per_file_sass_binaries", "third_party_js")

licenses(["notice"])

per_file_sass_binaries(
    name = "styles",
    srcs = glob(["*.scss"]),
    deps = ["//multitest_transport/ui2:constants"],
)

ng_module(
    name = "setup_wizard",
    srcs = [
        "build_channel_setup.ts",
        "setup_wizard_dialog.ts",
        "setup_wizard_module.ts",
        "setup_wizard_stepper.ts",
        "wifi_setup.ts",
    ],
    assets = [
        ":styles",
        "build_channel_setup.ng.html",
        "setup_wizard_dialog.ng.html",
        "setup_wizard_stepper.ng.html",
        "wifi_setup.ng.html",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:core"),
        third_party_js("angular2:material_dialog"),
        third_party_js("angular2:material_stepper"),
        third_party_js("angular2:platform_browser"),
        third_party_js("rxjs"),
        "//multitest_transport/ui2/app/build_channels",
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/settings",
        "//multitest_transport/ui2/app/shared",
    ],
)

ng_module(
    name = "tests",
    testonly = True,
    srcs = [
        "build_channel_setup_test.ts",
        "setup_wizard_dialog_test.ts",
        "setup_wizard_stepper_test.ts",
        "wifi_setup_test.ts",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        ":setup_wizard",
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("angular2:platform_browser_animations"),
        third_party_js("angular2:router_testing"),
        third_party_js("rxjs"),
        third_party_js("typings/jasmine"),
        "//multitest_transport/ui2/app/services",
        "//multitest_transport/ui2/app/shared",
        "//multitest_transport/ui2/app/testing:jasmine_util",
        "//multitest_transport/ui2/app/testing:test_util",
    ],
)