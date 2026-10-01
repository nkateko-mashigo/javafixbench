package dev.javafixbench.orders;

import dev.javafixbench.catalog.model.CatalogItem;

public record OrderLine(CatalogItem item, int quantity) {
}