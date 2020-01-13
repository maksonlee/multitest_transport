load("//multitest_transport:adapter.bzl", "ng_module", "per_file_sass_binaries", "third_party_js")

# MTT service package
licenses(["notice"])

package(default_visibility = ["//multitest_transport"])

per_file_sass_binaries(
    name = "styles",
    srcs = glob(["*.scss"]),
    deps = ["//multitest_transport/ui2:constants"],
)

ng_module(
    name = "services",
    srcs = [
        "analytics_service.ts",
        "app_data.ts",
        "auth_dialog.ts",
        "auth_service.ts",
        "error_dialog.ts",
        "file_reader_service.ts",
        "file_upload_service.ts",
        "index.ts",
        "mtt_client.ts",
        "mtt_models.ts",
        "notifier.ts",
        "notifier_dialog.ts",
        "services_module.ts",
        "strict_params.ts",
        "tfc_client.ts",
        "tfc_models.ts",
    ],
    assets = [
        ":styles",
        "auth_dialog.ng.html",
        "error_dialog.ng.html",
        "notifier_dialog.ng.html",
    ],
    deps = [
        third_party_js("angular2:cdk_a11y"),
        third_party_js("angular2:common_http"),
        third_party_js("angular2:core"),
        third_party_js("angular2:forms"),
        third_party_js("angular2:material_button"),
        third_party_js("angular2:material_dialog"),
        third_party_js("angular2:material_expansion"),
        third_party_js("angular2:material_form_field"),
        third_party_js("angular2:material_icon"),
        third_party_js("angular2:material_input"),
        third_party_js("angular2:material_snack_bar"),
        third_party_js("rxjs"),
    ],
)

ng_module(
    name = "tests",
    testonly = True,
    srcs = [
        "analytics_service_test.ts",
        "file_reader_service_test.ts",
        "file_upload_service_test.ts",
        "mtt_client_test.ts",
        "strict_params_test.ts",
        "tfc_client_test.ts",
    ],
    deps = [
        ":services",
        third_party_js("angular2:common_http"),
        third_party_js("angular2:common_http_testing"),
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("rxjs"),
        third_party_js("typings/jasmine"),
        "//multitest_transport/ui2/app/testing:test_util",
    ],
)