# Third-party sources

## Demonstration H&E images

Source: HER2-TUMOR-ROIS, The Cancer Imaging Archive (TCIA).
Dataset DOI: https://doi.org/10.7937/E65C-AM96
Collection: https://www.cancerimagingarchive.net/collection/her2-tumor-rois/
License: Creative Commons Attribution 4.0 International,
https://creativecommons.org/licenses/by/4.0/ .

Associated publication: Farahmand et al. Deep learning trained on hematoxylin
and eosin tumor region of Interest predicts HER2 status and trastuzumab treatment
response in HER2+ breast cancer. Modern Pathology 35, 44–51 (2022).
https://doi.org/10.1038/s41379-021-00911-w

The demonstration consists of derived crops from specimen O09-03495, not the
complete source slide. Crops were alpha-composited onto white, converted to RGB
and bilinearly resized to 512 × 512 pixels, matching the archived model inputs.
Derived cell coordinates and model predictions are identified separately.
The CC BY attribution does not imply endorsement of AlphaSpatial by the source
authors or TCIA.

## Model backbone

Qwen3.5-2B, Alibaba Cloud, https://huggingface.co/Qwen/Qwen3.5-2B .
The upstream license identifies Apache 2.0. Its original license is included with
the model package. AlphaSpatial fine-tuning changes and new code are distributed
under Apache 2.0; see `LICENSE` and `NOTICE`.

Software dependencies retain their respective upstream licenses and are installed
through the environment specification; their source trees are not vendored here.
