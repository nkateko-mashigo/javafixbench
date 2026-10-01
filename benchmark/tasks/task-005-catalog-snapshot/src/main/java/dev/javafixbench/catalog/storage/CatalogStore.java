package dev.javafixbench.catalog.storage;

import dev.javafixbench.catalog.model.CatalogItem;

import java.util.ArrayList;
import java.util.List;

public final class CatalogStore {
    private List<CatalogItem> items = new ArrayList<>();

    public void replace(List<CatalogItem> replacement) {
        if (replacement == null) {
            throw new IllegalArgumentException(
                    "Items must not be null"
            );
        }

        for (CatalogItem item : replacement) {
            if (item == null) {
                throw new IllegalArgumentException(
                        "Items must not contain null"
                );
            }
        }

        items = new ArrayList<>(replacement);
    }

    public List<CatalogItem> snapshot() {
        return items;
    }

    public int size() {
        return items.size();
    }
}