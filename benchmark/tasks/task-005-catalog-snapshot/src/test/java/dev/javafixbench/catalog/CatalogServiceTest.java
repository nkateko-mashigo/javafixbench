package dev.javafixbench.catalog;

import dev.javafixbench.catalog.api.CatalogService;
import dev.javafixbench.catalog.model.CatalogItem;

import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class CatalogServiceTest {
    private final CatalogService service = new CatalogService();
    private final CatalogItem first = new CatalogItem("A1", "Notebook");
    private final CatalogItem second = new CatalogItem("B2", "Pencil");

    @Test
    void clearingSnapshotDoesNotChangeCatalog() {
        service.replaceItems(List.of(first, second));
        service.items().clear();
        assertEquals(List.of(first, second), service.items());
    }

    @Test
    void addingToSnapshotDoesNotChangeCatalog() {
        service.replaceItems(List.of(first));
        service.items().add(second);
        assertEquals(List.of(first), service.items());
    }

    @Test
    void reorderingSnapshotDoesNotChangeCatalog() {
        service.replaceItems(List.of(first, second));
        Collections.reverse(service.items());
        assertEquals(List.of(first, second), service.items());
    }

    @Test
    void startsWithEmptyCatalog() {
        assertEquals(List.of(), service.items());
        assertEquals(0, service.size());
    }

    @Test
    void acceptsEmptyReplacement() {
        service.replaceItems(List.of(first));
        service.replaceItems(List.of());
        assertEquals(List.of(), service.items());
    }

    @Test
    void preservesInsertionOrder() {
        service.replaceItems(List.of(second, first));
        assertEquals(List.of(second, first), service.items());
    }

    @Test
    void preservesDuplicateItems() {
        service.replaceItems(List.of(first, first));
        assertEquals(List.of(first, first), service.items());
    }

    @Test
    void copiesReplacementList() {
        List<CatalogItem> input = new ArrayList<>(List.of(first));
        service.replaceItems(input);
        input.clear();
        assertEquals(List.of(first), service.items());
    }

    @Test
    void replacesPreviousItemsAndUpdatesSize() {
        service.replaceItems(List.of(first, second));
        service.replaceItems(List.of(second));
        assertEquals(List.of(second), service.items());
        assertEquals(1, service.size());
    }

    @Test
    void olderSnapshotKeepsContentsAfterReplacement() {
        service.replaceItems(List.of(first));
        List<CatalogItem> snapshot = service.items();
        service.replaceItems(List.of(second));
        assertEquals(List.of(first), snapshot);
    }

    @Test
    void rejectsNullReplacement() {
        assertThrows(IllegalArgumentException.class,
                () -> service.replaceItems(null));
    }

    @Test
    void rejectsNullElement() {
        assertThrows(IllegalArgumentException.class,
                () -> service.replaceItems(Arrays.asList(first, null)));
    }
}