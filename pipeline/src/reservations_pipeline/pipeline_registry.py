from kedro.pipeline import Pipeline
from reservations_pipeline.pipelines.clustering import pipeline as clustering

def register_pipelines() -> dict[str, Pipeline]:
    return {
        "clustering": clustering.create_pipeline(),
        "__default__": clustering.create_pipeline(),
    }
