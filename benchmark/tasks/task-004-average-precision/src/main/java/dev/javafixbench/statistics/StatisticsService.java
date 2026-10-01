package dev.javafixbench.statistics;

import dev.javafixbench.statistics.calculation.MeanCalculator;

import java.util.List;

public final class StatisticsService {
    private final MeanCalculator calculator = new MeanCalculator();

    public double average(List<Integer> values) {
        return calculator.mean(values);
    }
}