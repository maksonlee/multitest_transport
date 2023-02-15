# MTT GAE configs.

package(default_applicable_licenses = ["//multitest_transport:license"])

licenses(["notice"])

filegroup(
    name = "gae_configs",
    srcs = [
        "app.yaml",
        "core.yaml",
        "tfc.yaml",
        ":cron_yaml",
        ":index_yaml",
        ":queue_yaml",
    ],
    visibility = ["//multitest_transport"],
)

genrule(
    name = "cron_yaml",
    srcs = [
        "cron_ext.yaml",
        "@tradefed_cluster//tradefed_cluster/gae_configs:cron_yaml",
    ],
    outs = ["cron.yaml"],
    cmd = "$(location @tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls) $(SRCS) > \"$@\"",
    exec_tools = ["@tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls"],
)

genrule(
    name = "index_yaml",
    srcs = [
        "index_ext.yaml",
        "@tradefed_cluster//tradefed_cluster/gae_configs:index_yaml",
    ],
    outs = ["index.yaml"],
    cmd = "$(location @tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls) $(SRCS) > \"$@\"",
    exec_tools = ["@tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls"],
)

genrule(
    name = "queue_yaml",
    srcs = [
        "queue_ext.yaml",
        "@tradefed_cluster//tradefed_cluster/gae_configs:queue_yaml",
    ],
    outs = ["queue.yaml"],
    cmd = "$(location @tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls) $(SRCS) > \"$@\"",
    exec_tools = ["@tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls"],
)
