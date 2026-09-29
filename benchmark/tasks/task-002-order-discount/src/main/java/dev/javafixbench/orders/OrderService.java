package dev.javafixbench.orders;

import dev.javafixbench.pricing.DiscountPolicy;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Objects;

public final class OrderService {
    private final DiscountPolicy discountPolicy;

    public OrderService(DiscountPolicy discountPolicy) {
        this.discountPolicy = Objects.requireNonNull(
                discountPolicy,
                "Discount policy must not be null"
        );
    }

    public BigDecimal calculateTotal(
            BigDecimal subtotal,
            boolean loyaltyMember
    ) {
        BigDecimal discount = discountPolicy.discountFor(
                subtotal,
                loyaltyMember
        );

        return subtotal
                .subtract(discount)
                .setScale(2, RoundingMode.HALF_UP);
    }
}