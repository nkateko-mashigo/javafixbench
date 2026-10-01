package dev.javafixbench.shipping;

public final class ShippingLabel {
    public String format(DeliveryAddress address) {
        return address.recipient() + "\n"
                + address.street() + "\n" + address.city();
    }
}