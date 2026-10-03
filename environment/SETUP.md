# Environment setup

## Inference

The tested runtime uses Linux, Python 3.11.14, PyTorch 2.11.0+cu130, vLLM 0.21.0 and Transformers 5.9.0 on one 32-GB NVIDIA GPU. A CUDA-13-compatible NVIDIA driver is required.

```bash
python -m pip install -r environment/requirements.txt
```

The requirements select the CUDA 13.0 PyTorch build. The launcher configures offline inference, disables the FlashInfer sampler and uses Triton attention.

## CPU analysis

Patient-level statistics require NumPy, pandas and SciPy. Input validation also uses Pillow.

```bash
python -m pip install numpy==2.4.6 pandas==2.3.3 scipy==1.17.1 Pillow==11.3.0
```

## Code Ocean configuration

Mount inputs and the model under `/data`, use `/code/run` as the entry point, and configure:

```bash
AS_DATA_ROOT=/data
AS_MODEL_DIR=/data/AlphaSpatial-multitissue-v1
AS_RESULTS_ROOT=/results
AS_CACHE_ROOT=/tmp/alphaspatial-cache
```

Install dependencies and download weights before execution. The results directory must initially be empty.
