from metaform.compose import MetaFormer


tf = MetaFormer(name = "metaform_example")
host = tf.data("aws_ssm_parameter", "dbrx_host", name="dbrx_host")
token = tf.data("aws_ssm_parameter", "dbrx_token", name="dbrx_token", path=host["name"])
tf.provider.add("aws", source="hashicorp/aws", version="~> 0.1", region="us-east-1a")
tf.provider.add(
    "databricks",
    source="databricks/databricks",
    version="0.0.1",
    alias="mws",
    host=host["value"],
    token=token["value"],
)
libs = tf.property("library", location="s3://bucket", entry_point="src.main")
job = tf.resource(
    "databricks_job",
    "dbrx_job",
    library=libs,
    name="dbrx_job",
    host=host["name"],
    token=token["name"],
)

tf.build()
