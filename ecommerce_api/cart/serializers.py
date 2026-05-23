from django.db import transaction
from rest_framework import serializers

from cart.models import Cart, CartItem
from cart import selectors, services
from shop.models import Product


class CartItemSerializer(serializers.ModelSerializer):
    """
    Used by CartItemViewSet for create/update/delete and by CartViewSet.list to render items.
    Includes a read-only price snapshot from Product and computed totals.
    """

    product_id = serializers.PrimaryKeyRelatedField(
        source="product",
        queryset=Product.objects.all(),
        write_only=True,
    )
    product = serializers.SerializerMethodField(read_only=True)

    unit_price = serializers.DecimalField(
        source="product.price",
        max_digits=12,
        decimal_places=2,
        read_only=True,
    )
    total_price = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = CartItem
        fields = [
            "id",
            "product_id",
            "product",
            "quantity",
            "unit_price",
            "total_price",
        ]
        read_only_fields = ["id", "product", "unit_price", "total_price"]

    def get_product(self, obj: CartItem):
        p = obj.product
        return {
            "id": p.id,
            "name": getattr(p, "name", None),
            "description": getattr(p, "description", None),
            "price": getattr(p, "price", None),
            "is_active": getattr(p, "is_active", None),
        }

    def get_total_price(self, obj: CartItem):
        return selectors.get_total_item_price(item=obj)

    def validate_quantity(self, value: int):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be >= 1.")
        return value

    def create(self, validated_data):
        """
        Keep your existing flow (services.create_item) but return the created item.
        Your current perform_create sets serializer.instance manually; this allows either:
        - view calls serializer.save() (standard DRF)
        - or you keep perform_create as-is; both will work.
        """
        request = self.context.get("request")
        if request is None or request.user.is_anonymous:
            raise serializers.ValidationError("Authentication required.")

        cart = selectors.get_cart(user=request.user)
        product = validated_data.get("product")
        quantity = validated_data.get("quantity", 1)

        item = services.create_item(cart=cart, product=product, quantity=quantity)
        return item

    def update(self, instance: CartItem, validated_data):
        if "product" in validated_data:
            raise serializers.ValidationError(
                {"product_id": "Changing product is not allowed."}
            )

        instance.quantity = validated_data.get("quantity", instance.quantity)
        instance.save(update_fields=["quantity"])
        return instance


class CartSerializer(serializers.ModelSerializer):
    """
    Optional: a nicer serializer for returning the whole cart.
    If you switch CartViewSet.list to use this, you'll return cart metadata + items + totals.
    """

    items = CartItemSerializer(many=True, read_only=True)
    total_price = serializers.SerializerMethodField(read_only=True)
    total_items = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Cart
        fields = [
            "id",
            "created_at",
            "updated_at",
            "total_items",
            "total_price",
            "items",
        ]
        read_only_fields = fields

    def get_total_price(self, obj: Cart):
        return selectors.get_total_cart_price(cart=obj)

    def get_total_items(self, obj: Cart):
        return selectors.get_total_cart_items(cart=obj)
