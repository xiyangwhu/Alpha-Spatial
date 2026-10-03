"""Portable inference entry point derived from the archived Yale request format.

CPU validation is separately executable; tested runtime is documented with the release.
"""
import argparse
import json
import math
import os
from pathlib import Path

# Match the archived inference runtime; avoid an unnecessary FlashInfer JIT.
os.environ.setdefault('VLLM_USE_FLASHINFER_SAMPLER', '0')


def make_prompt(row):
    box = json.dumps(row['bbox_norm'], separators=(',', ':'))
    return (f"Focus on the <|object_ref_start|>cell<|object_ref_end|>"
            f"<|box_start|>{box}<|box_end|> in this {row['disease']} section. "
            f"Using the {row['panel']}, predict the cell's transcriptomic profile. "
            "Return non-zero gene counts in descending order as a JSON object.")


def parse_counts(text):
    def unique_pairs(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError('Duplicate gene key')
            out[key] = value
        return out
    try:
        d = json.loads(text, object_pairs_hook=unique_pairs)
        ok = isinstance(d, dict) and all(
            isinstance(k, str) and bool(k) and
            isinstance(v, (int, float)) and not isinstance(v, bool) and
            math.isfinite(v) and v >= 0 for k, v in d.items())
        return d if ok else None
    except (ValueError, TypeError, OverflowError):
        return None


def load_requests(path):
    from PIL import Image
    path = Path(path).resolve()
    rows, seen = [], set()
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rid = row['request_id']
        if not isinstance(rid, str) or not rid or rid in seen:
            raise ValueError('Empty or duplicate request ID')
        seen.add(rid)
        bb = row['bbox_norm']
        if not (isinstance(bb, list) and len(bb) == 4 and
                all(type(x) is int for x in bb) and
                0 <= bb[0] <= bb[2] < 1000 and 0 <= bb[1] <= bb[3] < 1000):
            raise ValueError(f'Invalid normalized box: {rid}')
        for key in ('disease', 'panel'):
            if not isinstance(row[key], str) or not row[key].strip():
                raise ValueError(f'Missing {key}: {rid}')
        image = (path.parent / row['image']).resolve()
        if not image.is_relative_to(path.parent):
            raise ValueError('Image must be inside the input directory')
        with Image.open(image) as im:
            if im.size != (512, 512) or im.mode != 'RGB':
                raise ValueError(f'Expected 512x512 RGB image: {rid}')
        row['_image_path'] = str(image)
        rows.append(row)
    if not rows:
        raise ValueError('No requests')
    return rows


def run(args, rows):
    import time
    from PIL import Image
    from transformers import AutoProcessor
    from vllm import LLM, SamplingParams
    cfg = json.loads(Path(args.config).read_text())
    model = Path(args.model).resolve()
    if not (model / 'config.json').is_file():
        raise ValueError('Model directory lacks config.json')
    out = Path(args.output)
    if out.exists():
        raise FileExistsError('Output already exists; use a new filename')
    if cfg['temperature'] != 0:
        raise ValueError('The demonstration uses deterministic temperature zero')
    start = time.monotonic()
    # Remote-code execution is disabled; audited custom code requires explicit adaptation.
    processor = AutoProcessor.from_pretrained(str(model), trust_remote_code=False,
                                              local_files_only=True)
    llm = LLM(model=str(model), tokenizer=str(model), trust_remote_code=False,
              tensor_parallel_size=1, dtype='bfloat16', swap_space=0,
              max_model_len=cfg['max_model_len'], max_num_seqs=cfg['max_num_seqs'],
              max_num_batched_tokens=cfg['max_num_batched_tokens'],
              gpu_memory_utilization=cfg['gpu_memory_utilization'],
              enable_prefix_caching=False, disable_custom_all_reduce=True,
              attention_config={'backend': 'TRITON_ATTN'},
              limit_mm_per_prompt={'image': 1, 'video': 0},
              mm_processor_kwargs={'max_pixels': 512 * 512})
    sampling = SamplingParams(temperature=0, max_tokens=cfg['max_tokens'], seed=cfg['seed'])
    # Exclusive create prevents replacement of any previous results.
    with out.open('x') as handle:
        for row in rows:
            with Image.open(row['_image_path']) as image:
                image = image.copy()
            messages = [{'role': 'user', 'content': [
                {'type': 'image'}, {'type': 'text', 'text': make_prompt(row)}]}]
            chat = processor.apply_chat_template(messages, tokenize=False,
                                                  add_generation_prompt=True)
            result = llm.generate([{'prompt': chat, 'multi_modal_data': {'image': image}}],
                                  sampling_params=sampling, use_tqdm=False)[0].outputs[0]
            counts = parse_counts(result.text)
            status = ('truncated' if result.finish_reason == 'length' else
                      'valid' if result.finish_reason == 'stop' and counts is not None else 'invalid')
            record = dict(request_id=row['request_id'], status=status,
                          finish_reason=result.finish_reason, raw_text=result.text,
                          output_tokens=len(result.token_ids),
                          predicted_expression=counts if status == 'valid' else None)
            handle.write(json.dumps(record) + '\n')
            handle.flush()
    print(json.dumps({'requests': len(rows), 'elapsed_seconds': time.monotonic()-start,
                      'output': str(out), 'complete': True}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='action', required=True)
    sub.add_parser('validate').add_argument('--requests', required=True)
    runp = sub.add_parser('run')
    for name in ('requests', 'model', 'config', 'output'):
        runp.add_argument('--' + name, required=True)
    args = p.parse_args()
    rows = load_requests(args.requests)
    if args.action == 'validate':
        print(json.dumps({'requests': len(rows), 'unique_images': len({r['_image_path'] for r in rows}),
                          'input_validation': 'PASS'}))
    else:
        run(args, rows)


if __name__ == '__main__':
    main()
