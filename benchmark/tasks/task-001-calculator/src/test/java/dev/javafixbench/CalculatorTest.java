package dev.javafixbench;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class CalculatorTest {

    private final Calculator calculator = new Calculator();

    @Test
    void dividesPositiveNumbers() {
        assertEquals(4, calculator.divide(20, 5));
    }

    @Test
    void dividesNegativeNumbers() {
        assertEquals(-3, calculator.divide(-9, 3));
    }

    @Test
    void rejectsDivisionByZero() {
        assertThrows(
            IllegalArgumentException.class,
            () -> calculator.divide(10, 0)
        );
    }
}