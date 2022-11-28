import sys
import os
sys.path.insert(
        0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "metaform")
    )
from compose import MetaFormer


tf = MetaFormer()
provider = tf.provider("aws", source="hashicorp/aws", version="~> 0.1")
host = tf.data("aws_ssm_parameter", "dbrx_host", name="dbrx_host")
token = tf.data("aws_ssm_parameter", "dbrx_token", name="dbrx_token", path=host["name"])
libs = tf.property("library", location="s3://bucket", entry_point="src.main")
job = tf.resource(
    "databricks_job",
    "dbrx_job",
    library=libs,
    name="dbrx_job",
    host=host["name"],
    token=token["name"],
)
# assert set(tf.registry) == {
#     "data.aws_ssm_parameter.dbrx_host",
#     "data.aws_ssm_parameter.dbrx_token",
#     "library",
#     "resource.databricks_job.dbrx_job",
# }
# assert tf.collect() == [host, token, job]


if __name__ == "__main__":
    tf.build()
