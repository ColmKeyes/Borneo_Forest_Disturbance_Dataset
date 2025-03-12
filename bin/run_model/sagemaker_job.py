from sagemaker.processing import ScriptProcessor, ProcessingInput, ProcessingOutput
import sagemaker

role = sagemaker.get_execution_role()

script_processor = ScriptProcessor(
    image_uri="YOUR_CUSTOM_IMAGE_URI",
    command=["python3"],
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge"
)

script_processor.run(
    code="inference_entry_point.py",
    inputs=[
        ProcessingInput(source="s3://your-bucket/checkpoints/", destination="/opt/ml/input/data"),
        ProcessingInput(source="s3://your-bucket/input_images/", destination="/opt/ml/input/data/test")
    ],
    outputs=[
        ProcessingOutput(source="/opt/ml/output", destination="s3://your-bucket/inference_results/")
    ],
    arguments=[
        "--checkpoint_name", "best_mIoU_iter_400_coherence.pth",
        "--config_name", "forest_disturbances_config_coherence.py",
        "--input_path", "/opt/ml/input/data/test",
        "--output_path", "/opt/ml/output/inference_results",
        "--bands", "[0,1,2,3,4,5]"
    ]
)
