# WebAOA workflow and action editor
load("//multitest_transport:adapter.bzl", "ng_module", "per_file_sass_binaries", "third_party_js")

licenses(["notice"])  # Apache 2.0

package(default_visibility = ["//multitest_transport/tools/webaoa:__subpackages__"])

per_file_sass_binaries(
    name = "styles",
    srcs = glob(["*.scss"]),
    deps = [third_party_js("angular2_material:theming")],
)

ng_module(
    name = "editor",
    srcs = [
        "action.ts",
        "action_editor.ts",
        "editor_module.ts",
        "touch_screen.ts",
        "wake_lock.ts",
        "workflow_editor.ts",
    ],
    assets = [
        ":styles",
        "action_editor.ng.html",
        "touch_screen.ng.html",
        "workflow_editor.ng.html",
    ],
    deps = [
        "//multitest_transport/tools/webaoa/device",
        third_party_js("angular2:cdk_clipboard"),
        third_party_js("angular2:cdk_drag_drop"),
        third_party_js("angular2:common"),
        third_party_js("angular2:core"),
        third_party_js("angular2:forms"),
        third_party_js("angular2:material_button"),
        third_party_js("angular2:material_card"),
        third_party_js("angular2:material_dialog"),
        third_party_js("angular2:material_form_field"),
        third_party_js("angular2:material_icon"),
        third_party_js("angular2:material_input"),
        third_party_js("angular2:material_list"),
        third_party_js("angular2:material_mdc_dialog"),
        third_party_js("angular2:material_mdc_progress_bar"),
        third_party_js("angular2:material_mdc_snack_bar"),
        third_party_js("angular2:material_mdc_tooltip"),
        third_party_js("angular2:material_progress_bar"),
        third_party_js("angular2:material_select"),
        third_party_js("rxjs"),
    ],
)

ng_module(
    name = "tests",
    testonly = True,
    srcs = [
        "action_editor_test.ts",
        "action_test.ts",
        "touch_screen_test.ts",
        "wake_lock_test.ts",
        "workflow_editor_test.ts",
    ],
    deps = [
        ":editor",
        "//multitest_transport/tools/webaoa/device",
        third_party_js("angular2:cdk_clipboard"),
        third_party_js("angular2:core"),
        third_party_js("angular2:core_testing"),
        third_party_js("angular2:material_dialog"),
        third_party_js("angular2:material_mdc_dialog"),
        third_party_js("angular2:material_mdc_snack_bar"),
        third_party_js("angular2:platform_browser"),
        third_party_js("angular2:platform_browser_animations"),
        third_party_js("rxjs"),
        "//multitest_transport/ui2/app/testing:jasmine_util",
    ],
)
