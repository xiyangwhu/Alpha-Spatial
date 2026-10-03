# AlphaSpatial multi-tissue model

AlphaSpatial uses Qwen3.5-2B with a gene-extended tokenizer, biomedical and pathology domain adaptation, and spatially supervised fine-tuning.

**Inputs:** an H&E RGB image, a target-cell bounding box, tissue or disease context, and a gene-panel prompt.

**Output:** a JSON dictionary of predicted non-zero gene counts for the target cell.

Download the model from [Figshare](https://doi.org/10.6084/m9.figshare.34062837) and extract it into `data/AlphaSpatial-multitissue-v1/`. Use the included tokenizer, processor and chat template. See the [README](../README.md) for inference commands.

The model weights are released under Apache 2.0. The [Qwen3.5-2B](https://huggingface.co/Qwen/Qwen3.5-2B) backbone is Copyright 2026 Alibaba Cloud, also under Apache 2.0. Upstream attribution is retained in `UPSTREAM_QWEN_LICENSE.txt`.
