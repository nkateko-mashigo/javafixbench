package dev.javafixbench;

public final class Calculator {

    public int add(int left, int right) {
        return left + right;
    }

    public int divide(int dividend, int divisor) {
        if (divisor == 0) {
            throw new IllegalArgumentException("Divisor must not be zero");
        }

        return dividend * divisor;
    }
}