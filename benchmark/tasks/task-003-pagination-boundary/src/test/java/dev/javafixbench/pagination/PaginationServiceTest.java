package dev.javafixbench.pagination;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertThrows;

class PaginationServiceTest {
    private final PaginationService service = new PaginationService();
    private final List<String> items = List.of("a", "b", "c", "d", "e");

    @Test
    void firstPageContainsAllRequestedItems() {
        assertEquals(List.of("a", "b"), service.page(items, 1, 2));
    }

    @Test
    void middlePageContainsAllRequestedItems() {
        assertEquals(List.of("c", "d"), service.page(items, 2, 2));
    }

    @Test
    void exactFinalPageContainsAllRemainingItems() {
        assertEquals(
                List.of("c", "d"),
                service.page(List.of("a", "b", "c", "d"), 2, 2)
        );
    }

    @Test
    void partialFinalPageContainsRemainingItems() {
        assertEquals(List.of("e"), service.page(items, 3, 2));
    }

    @Test
    void emptyListReturnsEmptyPage() {
        assertEquals(List.of(), service.page(List.of(), 1, 2));
    }

    @Test
    void pageBeyondListReturnsEmptyPage() {
        assertEquals(List.of(), service.page(items, 4, 2));
    }

    @Test
    void rejectsZeroPageNumber() {
        assertThrows(
                IllegalArgumentException.class,
                () -> service.page(items, 0, 2)
        );
    }

    @Test
    void rejectsZeroPageSize() {
        assertThrows(
                IllegalArgumentException.class,
                () -> service.page(items, 1, 0)
        );
    }

    @Test
    void largePageSizeReturnsAllItems() {
        assertEquals(
                items,
                service.page(items, 1, Integer.MAX_VALUE)
        );
    }

    @Test
    void largePageNumberReturnsEmptyPage() {
        assertEquals(
                List.of(),
                service.page(items, Integer.MAX_VALUE, 2)
        );
    }
}