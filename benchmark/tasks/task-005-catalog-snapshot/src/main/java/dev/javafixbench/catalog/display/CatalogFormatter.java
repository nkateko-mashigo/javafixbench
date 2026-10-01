package dev.javafixbench.catalog.display;

import dev.javafixbench.catalog.model.CatalogItem;

public final class CatalogFormatter {
    public String label(CatalogItem item) {
        return item.sku() + ": " + item.name();
    }
}