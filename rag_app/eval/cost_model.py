# compares monthly cost at 100k/1m/10m vectors: this project (chroma, self
# hosted) vs pinecone standard (managed).
# usage: python -m eval.cost_model
#
# pinecone numbers (checked pinecone.io/pricing, july 2026):
# $50/mo minimum, storage $0.33/gb/mo, write units $2/million,
# read units $8.25/million (assuming ~5 read units per filtered query)
# vector size = dim*4 bytes + ~200 bytes metadata overhead
#
# self-hosted: just a vm. $12/mo box handles up to ~1m vectors at 384-dim
# (fits in ram, ~1.5gb), $48/mo box for 10m to keep it in ram.
# assumed 5000 queries/month, k=5, no filter.
#
# these are rough numbers to show the shape of the cost curve, not a quote.
QUERY_VOLUME_PER_MONTH = 5000
EMBEDDING_DIM = 384
BYTES_PER_FLOAT = 4
METADATA_OVERHEAD_BYTES = 200

PINECONE_STORAGE_PER_GB = 0.33
PINECONE_WRITE_PER_MILLION = 2.0
PINECONE_READ_PER_MILLION = 8.25
PINECONE_STANDARD_MINIMUM = 50.0
ASSUMED_READ_UNITS_PER_QUERY = 5  # metadata-filtered query, mid-range estimate

SELF_HOSTED_VM_COST = {
    100_000: 12,
    1_000_000: 12,
    10_000_000: 48,
}


def vector_bytes(n_vectors: int) -> int:
    return n_vectors * (EMBEDDING_DIM * BYTES_PER_FLOAT + METADATA_OVERHEAD_BYTES)


def pinecone_monthly_cost(n_vectors: int) -> float:
    gb = vector_bytes(n_vectors) / (1024 ** 3)
    storage_cost = gb * PINECONE_STORAGE_PER_GB
    write_cost = (n_vectors / 1_000_000) * PINECONE_WRITE_PER_MILLION  # one-time ingest, shown monthly
    read_units = QUERY_VOLUME_PER_MONTH * ASSUMED_READ_UNITS_PER_QUERY
    read_cost = (read_units / 1_000_000) * PINECONE_READ_PER_MILLION
    usage_total = storage_cost + write_cost + read_cost
    return max(usage_total, PINECONE_STANDARD_MINIMUM)


def self_hosted_monthly_cost(n_vectors: int) -> float:
    return SELF_HOSTED_VM_COST[n_vectors]


def main():
    print(f"{'Vectors':>10} | {'Self-hosted ($/mo)':>19} | {'Pinecone ($/mo)':>16} | Savings")
    print("-" * 65)
    for n in [100_000, 1_000_000, 10_000_000]:
        self_cost = self_hosted_monthly_cost(n)
        managed_cost = pinecone_monthly_cost(n)
        savings = managed_cost - self_cost
        pct = (savings / managed_cost) * 100
        print(f"{n:>10,} | {self_cost:>19.2f} | {managed_cost:>16.2f} | ${savings:.2f} ({pct:.0f}%)")


if __name__ == "__main__":
    main()
