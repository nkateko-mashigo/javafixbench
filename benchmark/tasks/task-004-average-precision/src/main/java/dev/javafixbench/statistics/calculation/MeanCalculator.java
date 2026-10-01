package dev.javafixbench.statistics.calculation;

import java.util.List;

public final class MeanCalculator {
    public double mean(List<Integer> values) {
        if (values == null || values.isEmpty()) {
            throw new IllegalArgumentException(
                    "Values must not be null or empty"
            );
        }

        long total = 0;

        for (Integer value : values) {
            if (value == null) {
                throw new IllegalArgumentException(
                        "Values must not contain null"
                );
            }

            total += value;
        }

        return total / values.size();
    }
}