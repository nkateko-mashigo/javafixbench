package dev.javafixbench.inventory;

import java.util.List;

public final class StockSummary {
    public long totalUnits(List<StockEntry> entries) {
        long total = 0;

        for (StockEntry entry : entries) {
            total += entry.quantity();
        }

        return total;
    }
}