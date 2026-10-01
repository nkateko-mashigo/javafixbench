package dev.javafixbench.statistics;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class StatisticsServiceTest {
    private static final double DELTA = 0.000_000_001;
    private final StatisticsService service = new StatisticsService();

    @Test
    void averagePreservesPositiveFraction() {
        assertEquals(1.5, service.average(List.of(1, 2)), DELTA);
    }

    @Test
    void averagePreservesNegativeFraction() {
        assertEquals(-1.5, service.average(List.of(-1, -2)), DELTA);
    }

    @Test
    void averagePreservesFractionAcrossZero() {
        assertEquals(
                -1.0 / 3,
                service.average(List.of(-2, 0, 1)),
                DELTA
        );
    }

    @Test
    void wholeNumberAverageRemainsCorrect() {
        assertEquals(4.0, service.average(List.of(2, 4, 6)), DELTA);
    }

    @Test
    void singleValueReturnsThatValue() {
        assertEquals(7.0, service.average(List.of(7)), DELTA);
    }

    @Test
    void averageOfZerosIsZero() {
        assertEquals(0.0, service.average(List.of(0, 0)), DELTA);
    }

    @Test
    void largePositiveValuesDoNotOverflow() {
        assertEquals(
                (double) Integer.MAX_VALUE,
                service.average(List.of(
                        Integer.MAX_VALUE,
                        Integer.MAX_VALUE
                )),
                DELTA
        );
    }

    @Test
    void largeNegativeValuesDoNotOverflow() {
        assertEquals(
                (double) Integer.MIN_VALUE,
                service.average(List.of(
                        Integer.MIN_VALUE,
                        Integer.MIN_VALUE
                )),
                DELTA
        );
    }

    @Test
    void rejectsNullList() {
        assertThrows(
                IllegalArgumentException.class,
                () -> service.average(null)
        );
    }

    @Test
    void rejectsEmptyList() {
        assertThrows(
                IllegalArgumentException.class,
                () -> service.average(List.of())
        );
    }

    @Test
    void rejectsNullElement() {
        assertThrows(
                IllegalArgumentException.class,
                () -> service.average(Arrays.asList(1, null, 3))
        );
    }

    @Test
    void leavesInputValuesUnchanged() {
        List<Integer> values = new ArrayList<>(List.of(1, 2, 3));

        service.average(values);

        assertEquals(List.of(1, 2, 3), values);
    }
}