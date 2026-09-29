package dev.javafixbench.pricing;

import java.math.BigDecimal;

public final class DiscountPolicy {
    private static final BigDecimal QUALIFYING_SUBTOTAL =
            new BigDecimal("1000.00");

    private static final BigDecimal LOYALTY_DISCOUNT_RATE =
            new BigDecimal("0.05");

    public BigDecimal discountFor(
            BigDecimal subtotal,
            boolean loyaltyMember
    ) {
        if (subtotal == null) {
            throw new IllegalArgumentException(
                    "Subtotal must not be null"
            );
        }

        if (subtotal.signum() < 0) {
            throw new IllegalArgumentException(
                    "Subtotal must not be negative"
            );
        }

        if (!loyaltyMember
                || subtotal.compareTo(QUALIFYING_SUBTOTAL) < 0) {
            return BigDecimal.ZERO;
        }

        return subtotal.multiply(LOYALTY_DISCOUNT_RATE);
    }
}