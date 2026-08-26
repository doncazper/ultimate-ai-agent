from __future__ import annotations

import math
import random
from collections.abc import Mapping, Sequence


TAW00_MAX_BINOMIAL_DENOMINATOR = 10_000


def binomial_one_sided_upper_bound(
    event_count: int,
    denominator: int,
    *,
    confidence: float = 0.95,
) -> float:
    """Exact Clopper-Pearson one-sided upper bound for a binomial rate."""
    if denominator < 1 or event_count < 0 or event_count > denominator:
        raise ValueError("invalid binomial event count or denominator")
    if denominator > TAW00_MAX_BINOMIAL_DENOMINATOR:
        raise ValueError("binomial denominator exceeds the bounded verification limit")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between zero and one")
    if event_count == denominator:
        return 1.0

    alpha = 1.0 - confidence

    def cumulative_probability(probability: float) -> float:
        if probability <= 0:
            return 1.0
        if probability >= 1:
            return 0.0

        def probability_mass(observed: int) -> float:
            log_mass = (
                math.lgamma(denominator + 1)
                - math.lgamma(observed + 1)
                - math.lgamma(denominator - observed + 1)
                + observed * math.log(probability)
                + (denominator - observed) * math.log1p(-probability)
            )
            return math.exp(log_mass)

        if event_count <= denominator // 2:
            observed = event_count
            term = probability_mass(observed)
            total = term
            while observed > 0:
                term *= (
                    observed
                    / (denominator - observed + 1)
                    * (1.0 - probability)
                    / probability
                )
                total += term
                observed -= 1
            return min(1.0, total)

        observed = event_count + 1
        term = probability_mass(observed)
        upper_tail = term
        while observed < denominator:
            term *= (
                (denominator - observed)
                / (observed + 1)
                * probability
                / (1.0 - probability)
            )
            upper_tail += term
            observed += 1
        return max(0.0, 1.0 - upper_tail)

    low = event_count / denominator
    high = 1.0
    for _ in range(96):
        midpoint = (low + high) / 2.0
        if cumulative_probability(midpoint) > alpha:
            low = midpoint
        else:
            high = midpoint
    return high


def holm_adjusted_alpha(
    p_values_by_ref: Mapping[str, float], *, familywise_alpha: float = 0.05
) -> dict[str, float]:
    """Return each hypothesis's step-down Holm threshold in stable order."""
    if not 0 < familywise_alpha < 1:
        raise ValueError("familywise_alpha must be between zero and one")
    if not p_values_by_ref:
        raise ValueError("Holm family cannot be empty")
    for ref, value in p_values_by_ref.items():
        if not ref or not 0 <= value <= 1:
            raise ValueError("Holm family contains an invalid ref or p-value")
    ordered = sorted(p_values_by_ref.items(), key=lambda item: (item[1], item[0]))
    size = len(ordered)
    return {
        ref: familywise_alpha / (size - index) for index, (ref, _) in enumerate(ordered)
    }


def paired_bootstrap_mean_interval(
    baseline: Sequence[float],
    candidate: Sequence[float],
    *,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Deterministic percentile interval for paired candidate-minus-baseline means."""
    if len(baseline) != len(candidate) or not baseline:
        raise ValueError("paired samples must be nonempty and equal length")
    if not 0 < confidence < 1 or resamples < 1_000:
        raise ValueError("invalid confidence or insufficient bootstrap resamples")
    deltas = [float(right) - float(left) for left, right in zip(baseline, candidate)]
    if any(not math.isfinite(value) for value in deltas):
        raise ValueError("paired samples must be finite")
    rng = random.Random(seed)
    count = len(deltas)
    estimates = sorted(
        sum(deltas[rng.randrange(count)] for _ in range(count)) / count
        for _ in range(resamples)
    )
    tail = (1 - confidence) / 2
    lower_index = max(0, min(resamples - 1, math.floor(tail * resamples)))
    upper_index = max(0, min(resamples - 1, math.ceil((1 - tail) * resamples) - 1))
    return sum(deltas) / count, estimates[lower_index], estimates[upper_index]


def paired_bootstrap_one_sided_bound(
    baseline: Sequence[float],
    candidate: Sequence[float],
    *,
    side: str,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int = 0,
) -> tuple[float, float]:
    """One-sided paired candidate-minus-baseline mean bound."""
    if side not in {"lower", "upper"}:
        raise ValueError("side must be lower or upper")
    if len(baseline) != len(candidate) or not baseline:
        raise ValueError("paired samples must be nonempty and equal length")
    if not 0 < confidence < 1 or resamples < 1_000:
        raise ValueError("invalid confidence or insufficient bootstrap resamples")
    deltas = [float(right) - float(left) for left, right in zip(baseline, candidate)]
    if any(not math.isfinite(value) for value in deltas):
        raise ValueError("paired samples must be finite")
    rng = random.Random(seed)
    count = len(deltas)
    estimates = sorted(
        sum(deltas[rng.randrange(count)] for _ in range(count)) / count
        for _ in range(resamples)
    )
    index = (
        math.floor((1 - confidence) * resamples)
        if side == "lower"
        else math.ceil(confidence * resamples) - 1
    )
    index = max(0, min(resamples - 1, index))
    return sum(deltas) / count, estimates[index]


def paired_bootstrap_p95_difference_upper_bound(
    baseline: Sequence[float],
    candidate: Sequence[float],
    *,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int = 0,
) -> tuple[float, float]:
    """One-sided upper bound for candidate-minus-baseline p95 latency."""
    if len(baseline) != len(candidate) or not baseline:
        raise ValueError("paired samples must be nonempty and equal length")
    if not 0 < confidence < 1 or resamples < 1_000:
        raise ValueError("invalid confidence or insufficient bootstrap resamples")
    left = [float(value) for value in baseline]
    right = [float(value) for value in candidate]
    if any(not math.isfinite(value) for value in (*left, *right)):
        raise ValueError("paired samples must be finite")

    def percentile_95(values: Sequence[float]) -> float:
        ordered = sorted(values)
        return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]

    point = percentile_95(right) - percentile_95(left)
    rng = random.Random(seed)
    count = len(left)
    estimates: list[float] = []
    for _ in range(resamples):
        indexes = [rng.randrange(count) for _ in range(count)]
        estimates.append(
            percentile_95([right[index] for index in indexes])
            - percentile_95([left[index] for index in indexes])
        )
    estimates.sort()
    index = max(0, min(resamples - 1, math.ceil(confidence * resamples) - 1))
    return point, estimates[index]


def clustered_bootstrap_mean_interval(
    values_by_cluster: Mapping[str, Sequence[float]],
    *,
    confidence: float = 0.95,
    resamples: int = 10_000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Bootstrap whole evaluator/request clusters rather than individual judgments."""
    if not values_by_cluster:
        raise ValueError("clustered sample cannot be empty")
    clusters = sorted(values_by_cluster)
    normalized = {
        ref: tuple(float(value) for value in values_by_cluster[ref]) for ref in clusters
    }
    if any(not values for values in normalized.values()) or any(
        not math.isfinite(value) for values in normalized.values() for value in values
    ):
        raise ValueError("clusters must contain finite observations")
    if not 0 < confidence < 1 or resamples < 1_000:
        raise ValueError("invalid confidence or insufficient bootstrap resamples")

    def mean_for(cluster_refs: Sequence[str]) -> float:
        values = [value for ref in cluster_refs for value in normalized[ref]]
        return sum(values) / len(values)

    rng = random.Random(seed)
    estimates = sorted(
        mean_for([clusters[rng.randrange(len(clusters))] for _ in clusters])
        for _ in range(resamples)
    )
    tail = (1 - confidence) / 2
    lower_index = max(0, min(resamples - 1, math.floor(tail * resamples)))
    upper_index = max(0, min(resamples - 1, math.ceil((1 - tail) * resamples) - 1))
    return mean_for(clusters), estimates[lower_index], estimates[upper_index]


def krippendorff_alpha_ordinal(
    ratings_by_item: Mapping[str, Sequence[int | None]],
    *,
    minimum: int = 1,
    maximum: int = 5,
) -> float:
    """Compute ordinal Krippendorff alpha for complete or missing ratings."""
    if minimum >= maximum or not ratings_by_item:
        raise ValueError("invalid ordinal scale or empty ratings")
    clean_items: list[list[int]] = []
    pooled: list[int] = []
    expected_rater_count: int | None = None
    for ratings in ratings_by_item.values():
        if expected_rater_count is None:
            expected_rater_count = len(ratings)
        elif len(ratings) != expected_rater_count:
            raise ValueError("ordinal agreement items require equal rater slots")
        clean = [value for value in ratings if value is not None]
        if any(value < minimum or value > maximum for value in clean):
            raise ValueError("rating falls outside the ordinal scale")
        if len(clean) >= 2:
            clean_items.append(clean)
        pooled.extend(clean)
    if not clean_items or len(pooled) < 2:
        raise ValueError("insufficient duplicate ratings")

    frequencies = {value: pooled.count(value) for value in range(minimum, maximum + 1)}
    total = len(pooled)

    def ordinal_distance(left: int, right: int) -> float:
        if left == right:
            return 0.0
        low, high = sorted((left, right))
        cumulative = sum(frequencies[value] for value in range(low, high + 1))
        edge = (frequencies[low] + frequencies[high]) / 2
        return ((cumulative - edge) / total) ** 2

    observed_sum = 0.0
    observed_pairs = 0
    for ratings in clean_items:
        for left_index, left in enumerate(ratings):
            for right in ratings[left_index + 1 :]:
                observed_sum += ordinal_distance(left, right)
                observed_pairs += 1
    observed = observed_sum / observed_pairs

    expected_sum = 0.0
    expected_pairs = 0
    for left_index, left in enumerate(pooled):
        for right in pooled[left_index + 1 :]:
            expected_sum += ordinal_distance(left, right)
            expected_pairs += 1
    expected = expected_sum / expected_pairs
    if expected == 0:
        return 1.0 if observed == 0 else 0.0
    return 1 - observed / expected
