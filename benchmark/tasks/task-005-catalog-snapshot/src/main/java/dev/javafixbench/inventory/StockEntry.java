package dev.javafixbench.inventory;

import dev.javafixbench.catalog.model.CatalogItem;

public record StockEntry(CatalogItem item, int quantity) {
}