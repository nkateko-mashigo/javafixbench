package dev.javafixbench.pagination.bounds;

public final class PageBounds {
    public int endExclusive(int start, int pageSize, int totalItems) {
        if (start < 0 || pageSize <= 0 || totalItems < 0
                || start > totalItems) {
            throw new IllegalArgumentException("Invalid page bounds");
        }

        return (int) Math.min(
                (long) start + pageSize - 1L,
                totalItems
        );
    }
}