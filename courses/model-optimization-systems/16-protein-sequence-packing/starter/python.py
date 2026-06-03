"""Pack variable-length protein sequences into fixed token blocks."""

SEQUENCES = [
    ("kinase_A", 910),
    ("binder_1", 128),
    ("enzyme_B", 640),
    ("mini_helix", 96),
    ("receptor_C", 780),
    ("peptide_x", 64),
    ("domain_D", 350),
    ("antibody_frag", 520),
]

CAPACITY = 1024
NAIVE_BATCH_SIZE = 4


def naive_padded_tokens(sequences, batch_size):
    # TODO: batch in original order and sum batch_size * max length for each batch.
    return ...


def first_fit_decreasing(sequences, capacity):
    # TODO: return a list of bins, where each bin is a list of (name, length).
    return ...


def main():
    naive = naive_padded_tokens(SEQUENCES, NAIVE_BATCH_SIZE)
    packed = first_fit_decreasing(SEQUENCES, CAPACITY)
    packed_tokens = len(packed) * CAPACITY
    real_tokens = sum(length for _, length in SEQUENCES)
    reduction = (naive - packed_tokens) / naive * 100

    print(f"real tokens: {real_tokens}")
    print(f"naive padded tokens: {naive}")
    print(f"packed tokens: {packed_tokens}")
    print(f"waste reduction: {reduction:.1f}%")
    for index, bin_items in enumerate(packed, start=1):
        names = ",".join(name for name, _ in bin_items)
        used = sum(length for _, length in bin_items)
        print(f"pack {index}: used={used} items={names}")


if __name__ == "__main__":
    main()

