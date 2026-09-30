package dev.javafixbench.pagination;

import dev.javafixbench.pagination.bounds.PageBounds;

import java.util.ArrayList;
import java.util.List;

public final class PaginationService {
    private final PageBounds bounds = new PageBounds();

    public <T> List<T> page(List<T> items, int pageNumber, int pageSize) {
        if (items == null) {
            throw new IllegalArgumentException("Items must not be null");
        }

        if (pageNumber <= 0 || pageSize <= 0) {
            throw new IllegalArgumentException(
                    "Page number and size must be positive"
            );
        }

        long start = (long) (pageNumber - 1) * pageSize;

        if (start >= items.size()) {
            return List.of();
        }

        int from = (int) start;
        int to = bounds.endExclusive(from, pageSize, items.size());

        return new ArrayList<>(items.subList(from, to));
    }
}