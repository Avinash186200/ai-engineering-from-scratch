"""LoRA parameter arithmetic: why fine-tuning with adapters is cheap.

A full weight matrix W is d x k. LoRA freezes W and learns B (d x r) and A (r x k),
so trainable params per matrix = r * (d + k) instead of d * k.
Run:  python day07_ml/lora_params.py
"""


def lora_params(d, k, r):
    return r * (d + k)


def model_table(name, hidden, layers, matrices_per_layer=4, ranks=(4, 8, 16, 64)):
    full = hidden * hidden * matrices_per_layer * layers
    print(f"\n{name}: hidden={hidden}, layers={layers}, {matrices_per_layer} attention matrices/layer")
    print(f"  full fine-tune of those matrices: {full:,} params")
    for r in ranks:
        lora = lora_params(hidden, hidden, r) * matrices_per_layer * layers
        print(f"  LoRA r={r:<3} -> {lora:>12,} params  ({lora / full:.3%} of full)")


if __name__ == "__main__":
    print("one 4096 x 4096 matrix:", f"{4096 * 4096:,}", "params; LoRA r=8:", f"{lora_params(4096, 4096, 8):,}")
    model_table("small model (illustrative)", hidden=2048, layers=24)
    model_table("7B-class model (illustrative)", hidden=4096, layers=32)
    bytes_fp16 = lora_params(4096, 4096, 8) * 4 * 32 * 2
    print(f"\nr=8 adapter file for the 7B-class model at fp16: ~{bytes_fp16 / 1e6:.0f} MB")
