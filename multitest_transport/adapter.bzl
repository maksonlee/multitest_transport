"""Bazel adapter for build rules.

This file maps build rules used in the project to Bazel build rules.
"""

load("@io_bazel_rules_sass//:defs.bzl", _sass_binary = "sass_binary", _sass_library = "sass_library")
load("@npm_angular_bazel//:index.bzl", _ng_module = "ng_module")
load("@npm_bazel_terser//:index.bzl", _terse_minified = "terser_minified")
load("@npm_bazel_typescript//:index.bzl", _ts_library = "ts_library")

# A map to convert library aliases to npm package names.
# When adding a new dependency, one should make the following changes:
# 1) Add a mapping from a library alias (e.g. angular2:core) to npm package name (e.g. @angular/core).
# 2) Add a new npm package to ui2/package.json.
_PACKAGE_MAP = {
    "angular2:core": "@angular/core",
    "angular2:cdk_a11y": "@angular/cdk",
    "angular2:cdk_collections": "@angular/cdk",
    "angular2:cdk_drag_drop": "@angular/cdk",
    "angular2:cdk_keycodes": "@angular/cdk",
    "angular2:cdk_tree": "@angular/cdk",
    "angular2:common": "@angular/common",
    "angular2:common_http": "@angular/common",
    "angular2:common_http_testing": "@angular/common",
    "angular2:core_testing": "@angular/core",
    "angular2:flex-layout": "@angular/flex-layout",
    "angular2:forms": "@angular/forms",
    "angular2:material_button": "@angular/material",
    "angular2:material_card": "@angular/material",
    "angular2:material_checkbox": "@angular/material",
    "angular2:material_chips": "@angular/material",
    "angular2:material_dialog": "@angular/material",
    "angular2:material_divider": "@angular/material",
    "angular2:material_expansion": "@angular/material",
    "angular2:material_form_field": "@angular/material",
    "angular2:material_grid_list": "@angular/material",
    "angular2:material_icon": "@angular/material",
    "angular2:material_input": "@angular/material",
    "angular2:material_list": "@angular/material",
    "angular2:material_menu": "@angular/material",
    "angular2:material_paginator": "@angular/material",
    "angular2:material_progress_bar": "@angular/material",
    "angular2:material_progress_spinner": "@angular/material",
    "angular2:material_radio": "@angular/material",
    "angular2:material_select": "@angular/material",
    "angular2:material_sidenav": "@angular/material",
    "angular2:material_snack_bar": "@angular/material",
    "angular2:material_stepper": "@angular/material",
    "angular2:material_table": "@angular/material",
    "angular2:material_tabs": "@angular/material",
    "angular2:material_toolbar": "@angular/material",
    "angular2:material_tooltip": "@angular/material",
    "angular2:material_tree": "@angular/material",
    "angular2:platform_browser": "@angular/platform-browser",
    "angular2:platform_browser_animations": "@angular/platform-browser",
    "angular2:router": "@angular/router",
    "angular2:router_testing": "@angular/router",
    "angular2/testing:browser_dynamic_testing": "@angular",
    "angular2_material:theming": "@angular/material",
    "jasmine": "jasmine",
    "moment": "moment",
    "moment:moment_minified": "moment",
    "moment:typings": "moment",
    "moment_duration_format": "moment-duration-format",
    "rxjs": "rxjs",
    "typings/jasmine": "@types/jasmine",
}

# Closure compilation flags
COMPILER_FLAGS = []

MATERIAL_SASS_INCLUDE_PATHS = [
    "//multitest_transport/ui2/node_modules/@angular/material",
]

def _autoprefixer(
        name,
        src,
        out,
        browsers = "> 1%",
        visibility = None,
        compatible_with = None,
        verbose = False):
    """Runs autoprefixer on the given source files located in the given fileset.

    Args:
      name: A unique label for this rule.
      src: Source file or target.
      out: Output file.
      browsers: Browers to target, in browserlist format (e.g., "last 1 version",
                or "> 5%, > 2% in US, Firefox > 20").
                See https://github.com/ai/browserslist for more queries. If empty
                or blank, include all known prefixes. Default is '> 1%'.
      visibility: Standard BUILD visibility.
      compatible_with: Standard BUILD compatible_with.
      verbose: Whether to log all browsers prefixes are being generated for.
    """

    tool = "@npm//autoprefixer/bin:autoprefixer"

    command_line = [
        # Pass the BROWSERSLIST config as an environment var, as the node wrapper
        # script ignores and mismanages quotes/spaces in the browser config.
        "export BROWSERSLIST=\"{}\";".format(browsers or ""),
        "$(location {}) < $(SRCS) > $@".format(tool),
    ]
    if verbose:
        command_line.append("--verbose")

    native.genrule(
        name = name,
        message = "Invoking autoprefixer",
        srcs = [src],
        outs = [out],
        cmd = " ".join(command_line),
        tools = [tool],
        output_to_bindir = 1,
        visibility = visibility,
        compatible_with = compatible_with,
    )

def _dedup_deps(kwargs):
    if "deps" in kwargs:
        deps = kwargs["deps"]
        kwargs["deps"] = {dep: True for dep in deps}.keys()

def _js_bundle_impl(ctx):
    srcs = ctx.files.srcs + ctx.files.deps
    js_files = []
    js_filenames = []
    for f in srcs:
        if not f.basename.endswith(".js"):
            continue
        js_files.append(f)
        js_filenames.append(f.path)
    bundle_js = ctx.actions.declare_file(ctx.label.name)
    ctx.actions.run_shell(
        inputs = js_files,
        outputs = [bundle_js],
        mnemonic = "JsBundle",
        command = "cat %s > %s" % (" ".join(js_filenames), bundle_js.path),
        use_default_shell_env = True,
    )
    return DefaultInfo(files = depset([bundle_js]))

_js_bundle = rule(
    attrs = {
        "srcs": attr.label_list(allow_files = True),
        "deps": attr.label_list(),
    },
    executable = False,
    implementation = _js_bundle_impl,
)

def js_binary(name, srcs = [], deps = [], compile = True, visibility = None, **kwargs):
    bundle_name = name + "-bundle.js"
    _js_bundle(
        name = bundle_name,
        srcs = srcs,
        deps = deps,
        visibility = visibility,
    )
    if compile:
        _terse_minified(
            name = name + ".js",
            src = ":%s" % bundle_name,
            visibility = visibility,
        )

def karma_web_test_suite(**kwargs):
    # TODO: make this rule work with Bazel.
    pass

def ng_module(**kwargs):
    kwargs.pop("runtime_deps", None)
    _dedup_deps(kwargs)
    _ng_module(**kwargs)

def per_file_sass_binaries(name, srcs, **kwargs):
    """Compiles each scss file provided into its own css file.

    It generates a separate .css file for every src. MATERIAL_SASS_INCLUDE_PATHS
    is also added to include_paths. Each css file is autoprefixed to support
    older browsers.Finally, a fileset rule is defined which contains all the
    resulting css files.

    Args:
      name: The name of the rule. Used to name a fileset containing all the
          generated files.
      srcs: The Sass files to compile (may import other files).
          The input file names will be stripped of the .scss suffix and the
          generated files will append .css to the stripped filename.  The
          generated files will be in the same output location as the input files.
      **kwargs:  All other args are passed directly to the sass_binary rule.
    """
    binary_targets = []
    for src_file in srcs:
        base_file = ".".join(src_file.split(".")[:-1])
        bin_name = "gen_" + name + "_" + base_file
        binary_targets.append(":" + bin_name)

        # Include material include paths.
        kwargs["include_paths"] = kwargs.get("include_paths", []) + MATERIAL_SASS_INCLUDE_PATHS

        _sass_binary(
            name = bin_name,
            src = src_file,
            sourcemap = False,
            output_name = "%s-sass.css" % base_file,
            **kwargs
        )

        _autoprefixer(
            name = "autoprefixer_%s" % base_file,
            # The src can be a source file or target. We're using the sass_binary
            # target defined above so that sass is compiled to css before
            # autoprefixing.
            src = bin_name,
            out = "%s.css" % base_file,
        )

    # Create a filegroup containing all the generated files.
    filenames = [s.split(".")[0] for s in srcs]
    native.filegroup(
        name = name,
        srcs = ["%s.css" % f for f in filenames],
    )

sass_binary = _sass_binary

sass_library = _sass_library

def ts_config(**kwargs):
    # TODO: make this rule work with Bazel.
    pass

def ts_development_sources(**kwargs):
    # TODO: make this rule work with Bazel.
    pass

ts_library = _ts_library

def third_party_js(package_name):
    if package_name not in _PACKAGE_MAP:
        fail("Unknown library alias %s" % package_name)
    return "@npm//%s" % _PACKAGE_MAP.get(package_name)
