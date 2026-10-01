package dev.javafixbench.orders;

import java.util.List;

public final class OrderSummary {
    public long totalQuantity(List<OrderLine> lines) {
        long total = 0;

        for (OrderLine line : lines) {
            total += line.quantity();
        }

        return total;
    }
}