load("//multitest_transport:adapter.bzl", "ng_module", "third_party_js")

licenses(["notice"])

ng_module(
    name = "auth",
    srcs = [
        "auth_module.ts",
        "auth_return_page.ts",
    ],
    visibility = ["//multitest_transport"],
    deps = [
        third_party_js("angular2:core"),
        "//multitest_transport/ui2/app/shared",
    ],
)
