# B79 — quantization counterparts exist; deployment is the constraint

Checked 2026-09-10, read-only public Hugging Face API/model cards and Kaggle pages. No weights downloaded, GPU used, credentials read, or submission spent.

**Resolution:** both counterparts exist on Hugging Face. Do not close this row as “not separable with available weights.” A 27B FP8/NVFP4 comparison is memory-feasible on 96GB; Flash-Next FP8 is not a drop-in for the current single-96GB, PLE-only-offload serving profile. Existing artifacts establish candidates, not a measured quantization effect or byte-identical source revisions.

## Verified inventory

Exact `.safetensors` file bytes, summed from `GET https://huggingface.co/api/models/{repo}?blobs=true`. All four responses reported `private:false`, `gated:false`; metadata availability does not prove a full download or successful load. Sizes include tensor-file headers and exclude tokenizer/config files, KV cache and runtime allocations.

| Repository | Pinned revision | Tensor files / bytes | License / declared base |
|---|---|---:|---|
| [Qwen/Qwen3.8-Flash-Next-FP8](https://huggingface.co/Qwen/Qwen3.8-Flash-Next-FP8/tree/236dfdf285828023ca3bcd3f37366c58a3469b13) | `236dfdf285828023ca3bcd3f37366c58a3469b13` | 131 / 185,523,317,458 | Qwen Community License 1.0; Qwen/Qwen3.8-Flash-Next |
| [RadixArk/Qwen3.8-Flash-Next-NVFP4](https://huggingface.co/RadixArk/Qwen3.8-Flash-Next-NVFP4/tree/7b719225242aacd3dbd3f9407468c2ee9a9d2594) | `7b719225242aacd3dbd3f9407468c2ee9a9d2594` | 206 / 135,195,303,851 | `other`, defers to source model terms; same declared base |
| [Qwen/Qwen3.8-27B-FP8](https://huggingface.co/Qwen/Qwen3.8-27B-FP8/tree/017b9c7af6b5689d5dd426a76e0bc077eb5ca20a) | `017b9c7af6b5689d5dd426a76e0bc077eb5ca20a` | 66 / 30,866,866,928 | Apache-2.0; Qwen/Qwen3.8-27B |
| [unsloth/Qwen3.8-27B-NVFP4](https://huggingface.co/unsloth/Qwen3.8-27B-NVFP4/tree/f0b7c9e722f5565102fff8481c99e4d86ae099c7) | `f0b7c9e722f5565102fff8481c99e4d86ae099c7` | 2 / 23,417,592,488 | Apache-2.0; Qwen/Qwen3.8-27B |

The Flash [LICENSE](https://huggingface.co/Qwen/Qwen3.8-Flash-Next-FP8/blob/236dfdf285828023ca3bcd3f37366c58a3469b13/LICENSE) is a custom license, not Apache-2.0. Preserve its terms when packaging; this research does not adjudicate competition redistribution rights.

## Identity and what an experiment would isolate

The [RadixArk card](https://huggingface.co/RadixArk/Qwen3.8-Flash-Next-NVFP4/blob/7b719225242aacd3dbd3f9407468c2ee9a9d2594/README.md) identifies routed-expert NVFP4 W4A4, with other main components and MTP retained in BF16. It uses FP8 PLE tables from the updated official FP8 release. This is mixed precision, not every tensor in FP4. The card explicitly warns that earlier BF16-reference revision deltas were not established.

The official FP8 release uses fine-grained block-128 quantization. [Unsloth config](https://huggingface.co/unsloth/Qwen3.8-27B-NVFP4/blob/f0b7c9e722f5565102fff8481c99e4d86ae099c7/config.json) uses compressed-tensors mixed precision: 8-bit attention and later MLP groups alongside NVFP4 MLP groups. Its same-base declaration is sufficient to nominate a counterpart, but not to assert identical pre-quantization source bytes. Pin/check provenance, tokenizer/template, retained tensors, MTP, KV precision and serving settings before calling a future result a quantization-only effect. Do not substitute a fine-tuned, abliterated or pruned model.

## 96GB boundary

The [official vLLM recipe](https://recipes.vllm.ai/Qwen/Qwen3.8-Flash-Next) lists FP8 checkpoint size 172.78 GiB, at least 51GB host memory for N-gram offload, and validated multi-GPU deployments. Independent metadata arithmetic strengthens the single-card bound: map all index keys containing `ple` or `ngram` to their shard files; 33 such files total 52,259,869,154 bytes. Even removing those **entire** files leaves 133,263,448,304 bytes (124.11 GiB), above 96GB before KV/runtime memory. This generous shard-removal bound is not a measured resident-memory profile. Further expert/weight offload or multiple GPUs changes the serving profile and needs separate validation.

27B tensor storage is only 30.87GB FP8 / 23.42GB NVFP4. This clears a weight-capacity screen, not the full runtime/context/concurrency test. A matched 27B comparison is the practical future experiment; it does not automatically transfer its quantization effect to Flash-Next.

## Kaggle availability: bounded result

Primary pages verify existing [27B FP8 repack](https://www.kaggle.com/models/foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/) (`pytorch/hf-fp8/1`, 30.89GB, Apache-2.0) and [Flash NVFP4 asset](https://www.kaggle.com/models/keithtyser/qwen3-8-flash-next-nvfp4) (`radixark-modelopt-fp4`, version 1), whose card pins the RadixArk revision above and reports 135,253,622,894 total source bytes. The latter card says “Private”; a publicly readable card is not an authenticated access check.

Web queries `site:kaggle.com/models "Qwen3.8" "FP8"` and the NVFP4 equivalent found these existing arms, not verified counterpart asset handles. **Kaggle counterpart attachment/access remains unverified, not nonexistent.** No authenticated Kaggle catalog query was made. An HF candidate would still need an allowed offline Kaggle asset and a successful load before campaign use.

B79 closes the availability research. It authorizes no extra GPU run: B78 remains the current MTP-off experiment, while source-provenance and 27B runtime checks are prerequisites for a later quantization experiment.
