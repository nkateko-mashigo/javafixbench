package dev.javafixbench.pricing;

import java.math.BigDecimal;
import java.math.RoundingMode;

public final class PriceFormatter {
    public String format(BigDecimal amount) {
        return amount.setScale(2, RoundingMode.HALF_UP).toPlainString();
    }
}