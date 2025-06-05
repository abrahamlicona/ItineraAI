from kedro.pipeline import node, pipeline
from . import nodes

def create_pipeline(**kwargs):
    return pipeline([
        node(nodes.clean_reservations,
             inputs="reservations_raw",
             outputs="reservations_clean",
             name="clean"),
        node(nodes.train_cluster,
             inputs=dict(df="reservations_clean",
                         n_clusters="params:n_clusters",
                         random_state="params:random_state"),
             outputs="cluster_model",
             name="train"),
        node(nodes.assign_clusters,
             inputs=["reservations_clean", "cluster_model"],
             outputs="reservations_clustered",
             name="assign"),
        node(nodes.profile_segments,
             inputs="reservations_clustered",
             outputs="segment_profile",
             name="profile"),
    ])
