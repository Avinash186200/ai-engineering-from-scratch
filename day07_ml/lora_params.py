"""LoRA parameter arithmetic: why fine-tuning with adapters is cheap.

A full weight grid W is d_out x d_in. LoRA freezes W and learns A (r x d_in) and B (d_out x r),
so the trainable count is r * (d_in + d_out) instead of d_in * d_out.
Run:  python day07_ml/lora_params.py
"""


def lora_params(d_in, d_out, r):
    full = d_in * d_out              # every weight in the grid
    lora = r * (d_in + d_out)        # A is r x d_in, B is d_out x r
    return full, lora


def model_table(name, hidden, layers, matrices_per_layer=4, ranks=(4, 8, 16, 64)):
    full_one, _ = lora_params(hidden, hidden, 1)
    full = full_one * matrices_per_layer * layers
    print(f"\n{name}: hidden={hidden}, layers={layers}, {matrices_per_layer} attention matrices/layer")
    print(f"  full fine-tune of those matrices: {full:,} params")
    for r in ranks:
        lora = lora_params(hidden, hidden, r)[1] * matrices_per_layer * layers
        print(f"  LoRA r={r:<3} -> {lora:>12,} params  ({lora / full:.3%} of full)")


if __name__ == "__main__":
    full, lora = lora_params(4096, 4096, r=8)
    print(f"full: {full:,}  lora: {lora:,}  share: {lora/full:.2%}")
    # full: 16,777,216  lora: 65,536  share: 0.39%
    full16, lora16 = lora_params(4096, 4096, r=16)
    print(f"r=16 -> lora: {lora16:,}  share: {lora16/full16:.2%}")
    model_table("small model (illustrative)", hidden=2048, layers=24)
    model_table("7B-class model (illustrative)", hidden=4096, layers=32)
    bytes_fp16 = lora * 4 * 32 * 2
    print(f"\nr=8 adapter file for the 7B-class model at fp16: ~{bytes_fp16 / 1e6:.0f} MB")
