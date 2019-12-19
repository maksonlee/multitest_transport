# MTT GAE configs.

licenses(["notice"])

filegroup(
    name = "gae_configs",
    srcs = [
        "app.yaml",
        "core.yaml",
        "cron.yaml",
        "tfc.yaml",
        ":index_yaml",
        ":queue_yaml",
        "@tradefed_cluster//tradefed_cluster/gae_configs:handler_yamls",
    ],
    visibility = ["//multitest_transport"],
)

genrule(
    name = "index_yaml",
    srcs = [
        "index_ext.yaml",
        "@tradefed_cluster//tradefed_cluster/gae_configs:index_yaml",
    ],
    outs = ["index.yaml"],
    cmd = "$(location @tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls) $(SRCS) > \"$@\"",
    tools = ["@tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls"],
)

genrule(
    name = "queue_yaml",
    srcs = [
        "queue_ext.yaml",
        "@tradefed_cluster//tradefed_cluster/gae_configs:queue_yaml",
    ],
    outs = ["queue.yaml"],
    cmd = "$(location @tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls) $(SRCS) > \"$@\"",
    tools = ["@tradefed_cluster//tradefed_cluster/gae_configs:merge_yamls"],
)
