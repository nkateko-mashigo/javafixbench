package dev.javafixbench.catalog.api;

import dev.javafixbench.catalog.model.CatalogItem;
import dev.javafixbench.catalog.storage.CatalogStore;

import java.util.List;

public final class CatalogService {
    private final CatalogStore store = new CatalogStore();

    public void replaceItems(List<CatalogItem> items) {
        store.replace(items);
    }

    public List<CatalogItem> items() {
        return store.snapshot();
    }

    public int size() {
        return store.size();
    }
}