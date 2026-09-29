package dev.javafixbench.orders;

import dev.javafixbench.pricing.DiscountPolicy;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;

import static org.junit.jupiter.api.Assertions.assertEquals;

class OrderServiceTest {
    private final OrderService service =
            new OrderService(new DiscountPolicy());

    @Test
    void appliesLoyaltyDiscountAboveThreshold() {
        BigDecimal total = service.calculateTotal(
                new BigDecimal("1500.00"),
                true
        );

        assertEquals(new BigDecimal("1350.00"), total);
    }

    @Test
    void appliesLoyaltyDiscountAtThreshold() {
        BigDecimal total = service.calculateTotal(
                new BigDecimal("1000.00"),
                true
        );

        assertEquals(new BigDecimal("900.00"), total);
    }

    @Test
    void doesNotDiscountNonMembers() {
        BigDecimal total = service.calculateTotal(
                new BigDecimal("1500.00"),
                false
        );

        assertEquals(new BigDecimal("1500.00"), total);
    }

    @Test
    void doesNotDiscountOrdersBelowThreshold() {
        BigDecimal total = service.calculateTotal(
                new BigDecimal("999.99"),
                true
        );

        assertEquals(new BigDecimal("999.99"), total);
    }
}