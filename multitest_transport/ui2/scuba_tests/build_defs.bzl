"""Common Scuba build rules"""

load("//testing/karma/karma_scuba_framework:karma_scuba.bzl", "karma_scuba_plugins")
load("//third_party/py/multitest_transport:adapter.bzl", "karma_web_test_suite", "third_party_js", "ts_development_sources")

_DEFAULT_BROWSER_LIST = ["//third_party/py/multitest_transport/ui2/scuba_tests:chrome-linux"]
_DEFAULT_KARMA_DATA_LIST = [
    "//javascript/angular2/components/testing:google_sans.css",
    "//javascript/angular2/components/testing:material_icons.css",
    "//javascript/angular2/components/testing:product_sans.css",
    "//javascript/angular2/components/testing:roboto.css",
    "//third_party/py/multitest_transport/ui2:styles.css",
]

def karma_scuba_test(
        name,
        deps,
        browsers = _DEFAULT_BROWSER_LIST,
        data = []):
    """Creates a scuba build file component for use under Test Station

    Args:
       name: name for karma_web_test_suite
       deps: dependencies that ts_development_sources requires
       browsers: browser to use for this test
       data: extra data needed for karma_web_test_suite to work properly
    """
    ts_development_sources(
        name = name + "_sources",
        testonly = 1,
        deps = deps,
        runtime_deps = [
            third_party_js("moment:moment_minified"),
            third_party_js("moment_duration_format"),
        ],
    )

    karma_web_test_suite(
        name = name,
        browsers = browsers,
        data = _DEFAULT_KARMA_DATA_LIST + data,
        karma_plugins = karma_scuba_plugins(),
        manifest = ":" + name + "_sources",
    )
