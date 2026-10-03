# Alpha Spatial

**Language-guided prediction of single-cell spatial gene expression from histology**

AlphaSpatial predicts cell-associated gene expression from H&E images using target-cell coordinates, tissue or disease context, and a gene-panel prompt. This repository provides inference code, a small example dataset and patient-level treatment-response analysis.

## Installation

Use Linux with Python 3.11, a CUDA-13-compatible NVIDIA driver and an NVIDIA GPU. The example was tested on a 32-GB GPU.

```bash
python -m pip install -r environment/requirements.txt
```

See [environment setup](environment/SETUP.md) for runtime and Code Ocean settings.

## Model and data

- [Model weights](https://doi.org/10.6084/m9.figshare.34062837)
- [Predicted expression and spatial coordinates](https://doi.org/10.6084/m9.figshare.34060014)

Download and extract the model into `data/`:

```bash
curl -fL --retry 3 -o AlphaSpatial-multitissue-v1.zip \
  https://ndownloader.figshare.com/files/69599094
unzip AlphaSpatial-multitissue-v1.zip -d data/
```

Keep all model files together in `data/AlphaSpatial-multitissue-v1/`, including the tokenizer, processor and chat template.

## Run the example

The included example contains two H&E tiles and 12 target cells, together with state counts for 81 patients.

```bash
CUDA_VISIBLE_DEVICES=0 bash code/run
```

Results are written to `results/`:

- `predictions.jsonl`: generated expression and prediction status for each target cell.
- `expression/expression.csv`: cell-by-gene predicted counts.
- `expression/out_of_target.csv`: generated genes outside the supplied target list.
- `response_statistics/`: patient state burdens and treatment-response comparisons.
- `inference_check.json` and `run_summary.json`: execution checks.

Use a new output directory for each run. Paths can be configured with `AS_MODEL_DIR`, `AS_DATA_ROOT`, `AS_RESULTS_ROOT`, `AS_CACHE_ROOT` and `AS_PYTHON`.

To run the patient-level analysis without a GPU:

```bash
python code/reproduce_response.py \
  --data data/patient_endpoints --output results_cpu
```

## Use your own images

Prepare 512 × 512 RGB PNG tiles and a JSONL request file following [the example](data/inference_demo/requests.jsonl). Each request specifies:

| Field | Description |
| --- | --- |
| `request_id` | Unique target-cell identifier |
| `image` | Image path relative to the request file |
| `bbox_norm` | Target box in `[xmin, ymin, xmax, ymax]` order |
| `disease` | Tissue or disease context |
| `panel` | Gene-panel name |

Place images within the input directory. Convert each box coordinate from tile pixels using `int(pixel / 512 * 1000)`; accepted coordinates range from 0 to 999. Cell segmentation and spatial calibration precede inference.

```bash
python code/infer.py validate --requests my_input/requests.jsonl

python code/infer.py run \
  --requests my_input/requests.jsonl \
  --model data/AlphaSpatial-multitissue-v1 \
  --config data/inference_demo/inference_config.json \
  --output predictions.jsonl

python code/export_expression.py \
  --predictions predictions.jsonl \
  --genes my_input/target_genes.json \
  --output expression
```

Provide the appropriate context, panel and target-gene list for your data. The gene-list file accepts a JSON list of symbols or an object with a `genes` list. Expression is exported without normalization. For valid predictions, omitted target genes are assigned zero; invalid or truncated predictions remain missing.

## Citation

Yang, X. (2026). *Spatial transcriptomics data*. Figshare. https://doi.org/10.6084/m9.figshare.34060014

Yang, X. (2026). *MultitissueModel*. Figshare. https://doi.org/10.6084/m9.figshare.34062837

## License

AlphaSpatial code and model weights are released under [Apache 2.0](LICENSE). Example H&E images are derived from TCIA HER2-TUMOR-ROIS under CC BY 4.0. See [third-party notices](metadata/THIRD_PARTY_NOTICES.md) for source attribution.
