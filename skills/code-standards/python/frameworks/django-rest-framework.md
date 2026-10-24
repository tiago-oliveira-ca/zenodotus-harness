# Django REST Framework Standards

Apply these Django REST Framework (DRF) standards whenever writing, reviewing, or refactoring DRF
code — serializers, ViewSets, APIViews, authentication, permissions, pagination, filtering,
testing, and project structure. These are opinionated, battle-tested patterns sourced from OWASP,
the official DRF docs, and senior Django practitioners.

General Python style (PEP 8/20/257, naming, type hints, docstrings, exceptions, idioms) is
covered by the parent `../SKILL.md` — read it first. This file only covers what's specific to DRF.

This file consolidates the core standards with the deep serializer, view, and testing references
into one document. Its sections are:

1. Project Structure
2. Production-Ready DRF Settings
3. Serializers (core rules + deep reference)
4. ViewSets and Views (core rules + deep reference)
5. Authentication and Permissions
6. Query Optimization (Preventing N+1)
7. Service Layer Pattern
8. Testing (core patterns + deep reference)
9. Error Handling
10. Documentation (drf-spectacular)
11. Models
12. Security

---

## 1. Project Structure

Organize each Django app with an `api/` sub-package for DRF concerns:

```
myproject/
  config/
    settings/
      base.py
      development.py
      production.py
    urls.py
  apps/
    users/
      api/
        v1/
          serializers.py
          views.py
          urls.py
        v2/
          serializers.py
          views.py
          urls.py
      models.py
      services.py          ← Write/mutation logic lives here
      selectors.py         ← Read/query logic lives here
      tests/
        conftest.py
        factories.py
        test_serializers.py
        test_views.py
    products/
      api/v1/...
      models.py
      services.py
      selectors.py
```

**Key rules:**
- Models and services are version-agnostic (shared across API versions)
- Only serializers, views, and URLs change per API version
- Each app must be independently pluggable — no tight inter-app coupling
- **Fat Models / Thin Views:** Logic belongs in model methods, managers, or `services.py`. Views and serializers orchestrate — they don't implement.
- **Selectors pattern:** `selectors.py` holds all read queries (returns querysets/objects). `services.py` holds all writes (creates, updates, deletes). This keeps both layers thin, testable, and independent of the HTTP layer.
- Use environment variables (`django-environ` or `python-decouple`) for all secrets

---

## 2. Production-Ready DRF Settings

```python
REST_FRAMEWORK = {
    # Never leave as AllowAny globally
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # for admin/browsable API
    ],
    # Remove BrowsableAPIRenderer in production — it leaks schema info
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    # Always paginate — unbounded list responses are a liability
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # Filtering
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    # Throttling is disabled by default — always configure it
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
    'EXCEPTION_HANDLER': 'yourapp.exceptions.custom_exception_handler',
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

---

## 3. Serializers

Core rules first, then the deep reference (ModelSerializer patterns, validation, nesting,
inheritance, custom fields, and eager-loading).

### Always use explicit field allowlists
```python
# BAD — exposes every model field, including sensitive ones added in the future
class Meta:
    model = User
    fields = '__all__'          # Never
    # exclude = ['password']    # Also never — allowlist is safer than blocklist

# GOOD
class Meta:
    model = User
    fields = ['id', 'username', 'email', 'first_name', 'last_name']
    read_only_fields = ['id', 'created_at']
```

### Separate read and write serializers for complex resources
```python
def get_serializer_class(self):
    if self.action in ('create', 'update', 'partial_update'):
        return ProductWriteSerializer
    if self.action == 'list':
        return ProductListSerializer
    return ProductDetailSerializer
```

### Always use `raise_exception=True`
```python
# BAD
if not serializer.is_valid():
    return Response(serializer.errors, status=400)

# GOOD — DRF handles the 400 response automatically
serializer.is_valid(raise_exception=True)
```

### Cross-field validation belongs in `validate()`
```python
def validate(self, data):
    if data['end_date'] <= data['start_date']:
        raise serializers.ValidationError("end_date must be after start_date.")
    return data
```

### `read_only_fields` vs `SerializerMethodField`
- Use `read_only_fields` for plain model fields/properties you want read-only
- Use `SerializerMethodField` for computed values that require method logic
- Use `source=` for field renaming or traversing related models (e.g., `source='profile.bio'`)

### 3.1 ModelSerializer Patterns

Always start with ModelSerializer for model-backed endpoints:

```python
class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']
```

#### read_only_fields vs SerializerMethodField

| | `read_only_fields` | `SerializerMethodField` |
|---|---|---|
| Backed by model field/property | Yes | No |
| Requires custom logic | No | Yes |
| Writable | No | No (always read-only) |
| Computation cost | Zero | Runs Python method per object |

```python
# read_only_fields — for plain model fields
class Meta:
    read_only_fields = ['id', 'created_at', 'updated_at', 'author']

# SerializerMethodField — for computed values
word_count = serializers.SerializerMethodField()
author_full_name = serializers.SerializerMethodField()

def get_word_count(self, obj):
    return len(obj.body.split())

def get_author_full_name(self, obj):
    # Access request via self.context['request']
    return f"{obj.author.first_name} {obj.author.last_name}"
```

#### source= parameter

```python
class UserSerializer(serializers.ModelSerializer):
    # Rename a model field in the API
    active = serializers.BooleanField(source='is_active')

    # Traverse FK/OneToOne with dotted path (remember to prefetch!)
    department_name = serializers.CharField(source='profile.department.name', read_only=True)

    # Call a model method
    display_name = serializers.CharField(source='get_full_name', read_only=True)
```

### 3.2 Validation

#### Validation execution order
1. Field-level validators (defined as `validators=` on individual fields)
2. `validate_<field_name>()` methods
3. `validate()` for cross-field object-level logic

#### Field-level validation
```python
def validate_quantity(self, value):
    if value <= 0:
        raise serializers.ValidationError("Quantity must be positive.")
    return value

def validate_sku(self, value):
    if not value.startswith('SKU-'):
        raise serializers.ValidationError("SKU must start with 'SKU-'.")
    return value.upper()
```

#### Cross-field validation — always in `validate()`
```python
def validate(self, data):
    if data['end_date'] <= data['start_date']:
        raise serializers.ValidationError(
            {'end_date': 'end_date must be after start_date.'}
        )
    if data.get('min_attendees', 0) > data.get('max_attendees', 0):
        raise serializers.ValidationError(
            'min_attendees cannot exceed max_attendees.'
        )
    return data
```

#### UniqueTogetherValidator conflict fix
When `unique_together` + `required=False` fields conflict with auto-generated validators:

```python
class Meta:
    model = Tag
    fields = ['name', 'category']
    validators = []  # Remove auto-generated UniqueTogetherValidator

def validate(self, data):
    qs = Tag.objects.filter(name=data['name'], category=data.get('category'))
    if self.instance:
        qs = qs.exclude(pk=self.instance.pk)
    if qs.exists():
        raise serializers.ValidationError("This tag already exists in that category.")
    return data
```

### 3.3 Nested Serializers

#### Read-only nested (simple)
```python
class ArticleSerializer(serializers.ModelSerializer):
    author = UserMiniSerializer(read_only=True)  # Nested, read-only
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'author', 'tags']
```

#### Writable nested — override create() and update()
```python
class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ['id', 'customer', 'status', 'items']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for item_data in items_data:
                OrderItem.objects.create(order=order, **item_data)
        return order

    def update(self, instance, validated_data):
        items_data = validated_data.pop('items', None)
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            if items_data is not None:
                # Full replace strategy
                instance.items.all().delete()
                for item_data in items_data:
                    OrderItem.objects.create(order=instance, **item_data)
        return instance
```

**Avoid `depth = N`** — it has no prefetch control and exposes all nested fields.
For complex writable nesting, consider `drf-writable-nested`.

### 3.4 Serializer Inheritance

```python
# Base serializer with common fields
class ProductBaseSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'category_name', 'created_at']
        read_only_fields = ['id', 'created_at']

# Write variant — inherit Meta to avoid duplicating model/validators
class ProductWriteSerializer(ProductBaseSerializer):
    class Meta(ProductBaseSerializer.Meta):
        fields = ['name', 'price', 'category', 'sku']
        read_only_fields = []

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be positive.")
        return value

# List variant — minimal payload
class ProductListSerializer(ProductBaseSerializer):
    class Meta(ProductBaseSerializer.Meta):
        fields = ['id', 'name', 'price']
```

**Always inherit child Meta from parent Meta** to preserve `model`, `read_only_fields`, and validators.

### 3.5 Custom Fields and to_representation

#### to_representation — for output transformation
```python
def to_representation(self, instance):
    data = super().to_representation(instance)
    request = self.context.get('request')
    # Field-level permissions
    if not request or not request.user.is_staff:
        data.pop('salary', None)
        data.pop('internal_notes', None)
    return data
```

#### to_internal_value — for input normalization
```python
def to_internal_value(self, data):
    # Normalize incoming data before validation
    if 'name' in data:
        data['name'] = data['name'].strip().title()
    return super().to_internal_value(data)
```

#### Custom field
```python
class TimestampField(serializers.Field):
    def to_representation(self, value):
        return value.timestamp()

    def to_internal_value(self, data):
        from datetime import datetime
        return datetime.fromtimestamp(data)
```

### 3.6 N+1 Prevention: setup_eager_loading

```python
class BookSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.name', read_only=True)
    genres = GenreSerializer(many=True, read_only=True)

    @staticmethod
    def setup_eager_loading(queryset):
        queryset = queryset.select_related('author', 'category')
        queryset = queryset.prefetch_related(
            'genres',
            Prefetch(
                'reviews',
                queryset=Review.objects.filter(is_published=True),
                to_attr='published_reviews'
            )
        )
        return queryset

    class Meta:
        model = Book
        fields = ['id', 'title', 'author_name', 'genres']


class BookViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return BookSerializer.setup_eager_loading(Book.objects.all())
```

---

## 4. ViewSets and Views

Core rules first, then the deep reference (class selection, hooks, custom actions, mixins,
routing, filtering, pagination, versioning).

### Use the right tool
| Scenario | Use |
|---|---|
| Full CRUD on a model | `ModelViewSet` |
| Read-only resource | `ReadOnlyModelViewSet` |
| Subset of CRUD | `GenericViewSet` + specific mixins |
| Non-CRUD, custom logic | `APIView` |

### Always scope `get_queryset()` to the current user
```python
def get_queryset(self):
    qs = Product.objects.select_related('category').prefetch_related('tags')
    # USER SCOPING: list endpoints don't trigger has_object_permission
    if not self.request.user.is_staff:
        qs = qs.filter(owner=self.request.user)
    return qs
```

### Use `perform_create`/`perform_update` to inject request context
```python
def perform_create(self, serializer):
    serializer.save(owner=self.request.user)

def perform_destroy(self, instance):
    instance.is_deleted = True   # Soft delete pattern
    instance.save()
```

### Prefer mixin composition over ModelViewSet when not all CRUD is needed
```python
class AuditLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet      # No update or delete — intentional
):
    ...
```

### 4.1 View Class Selection Guide

| Scenario | Use |
|---|---|
| Full CRUD on a model | `ModelViewSet` |
| Read-only list + detail | `ReadOnlyModelViewSet` |
| Subset of CRUD | `GenericViewSet` + explicit mixins |
| Non-CRUD, fully custom | `APIView` |
| Moderate customization | `GenericAPIView` + mixins |

#### ModelViewSet — standard CRUD

```python
class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Product.objects.filter(
            owner=self.request.user
        ).select_related('category').prefetch_related('tags')

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
```

#### APIView — full control, non-CRUD

```python
class UserSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get('q', '')
        users = User.objects.filter(username__icontains=query)[:20]
        serializer = UserMiniSerializer(users, many=True)
        return Response(serializer.data)
```

### 4.2 ModelViewSet Hooks

#### get_queryset() — filtering, scoping, optimization

```python
def get_queryset(self):
    qs = Order.objects.select_related('customer').prefetch_related('items__product')

    # CRITICAL: scope to request.user — permission classes don't filter lists
    if not self.request.user.is_staff:
        qs = qs.filter(customer=self.request.user)

    # Optional param filtering
    status = self.request.query_params.get('status')
    if status:
        qs = qs.filter(status=status)

    return qs
```

Never access `self.queryset` directly in view logic — always call `self.get_queryset()` so
filtering is re-evaluated per request.

#### get_serializer_class() — different serializers per action

```python
SERIALIZER_MAP = {
    'list': ProductListSerializer,
    'create': ProductWriteSerializer,
    'update': ProductWriteSerializer,
    'partial_update': ProductWriteSerializer,
    'retrieve': ProductDetailSerializer,
}

def get_serializer_class(self):
    return SERIALIZER_MAP.get(self.action, ProductDetailSerializer)
```

#### get_serializer_context() — inject extra context

```python
def get_serializer_context(self):
    context = super().get_serializer_context()
    context['organization'] = self.request.user.organization
    return context
```

#### perform_create / perform_update / perform_destroy

```python
def perform_create(self, serializer):
    # Inject user, set defaults — called after is_valid()
    serializer.save(
        owner=self.request.user,
        status='draft',
    )

def perform_update(self, serializer):
    serializer.save(last_edited_by=self.request.user)

def perform_destroy(self, instance):
    # Soft delete instead of hard delete
    instance.is_deleted = True
    instance.deleted_by = self.request.user
    instance.save()
```

Use `perform_create`/`perform_update` for post-validation injection. Override the full
`create()`/`update()` methods only when you need to change the HTTP response format.

### 4.3 Custom Actions with @action

```python
from rest_framework.decorators import action
from rest_framework.response import Response

class UserViewSet(viewsets.ModelViewSet):
    # detail=False → /users/activate-bulk/
    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAdminUser],
        url_path='activate-bulk',
    )
    def activate_bulk(self, request):
        ids = request.data.get('ids', [])
        updated = User.objects.filter(pk__in=ids).update(is_active=True)
        return Response({'activated': updated})

    # detail=True → /users/{pk}/set-password/
    @action(
        detail=True,
        methods=['post'],
        serializer_class=PasswordChangeSerializer,  # Override serializer for this action
        url_path='set-password',
    )
    def set_password(self, request, pk=None):
        user = self.get_object()  # ALWAYS call get_object() — triggers permission check
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'status': 'password updated'})

    # Expose current user without pk
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
```

**Key @action parameters:**
- `detail=True/False` — True adds `{pk}` to the URL; False creates a collection-level route
- `url_path` — customizes the URL segment (default: method name with `_` → `-`)
- `permission_classes`, `serializer_class`, `filter_backends` — override ViewSet-level per action

### 4.4 Mixin Composition

Prefer explicit mixin composition over `ModelViewSet` when you only need a subset of CRUD.
This prevents accidental exposure of endpoints.

```python
from rest_framework import mixins, viewsets

# Read-only + create; no update or delete
class AuditLogViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet
):
    queryset = AuditLog.objects.order_by('-created_at')
    serializer_class = AuditLogSerializer
```

Available mixins:

| Mixin | Action | HTTP |
|---|---|---|
| `ListModelMixin` | `list` | GET collection |
| `RetrieveModelMixin` | `retrieve` | GET detail |
| `CreateModelMixin` | `create` | POST |
| `UpdateModelMixin` | `update`, `partial_update` | PUT, PATCH |
| `DestroyModelMixin` | `destroy` | DELETE |

`ModelViewSet` = all five + `GenericViewSet`.
`ReadOnlyModelViewSet` = `ListModelMixin` + `RetrieveModelMixin` + `GenericViewSet`.

### 4.5 URL Routing

#### DefaultRouter (recommended for most APIs)

```python
# apps/products/api/v1/urls.py
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, CategoryViewSet

router = DefaultRouter()
router.register(r'products', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')

urlpatterns = router.urls
```

Always register ViewSets with a router. Never manually wire `@action` methods into `urlpatterns`
— this bypasses the router's action context setting.

#### Root URL configuration

```python
# config/urls.py
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('apps.products.api.v1.urls')),
    path('api/v1/', include('apps.users.api.v1.urls')),
    path('api/v2/', include('apps.products.api.v2.urls')),
]
```

| Router | API root view | Format suffixes |
|---|---|---|
| `SimpleRouter` | No | No |
| `DefaultRouter` | Yes | Yes |

### 4.6 Filtering, Searching, Ordering

```python
import django_filters

class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    name = django_filters.CharFilter(field_name='name', lookup_expr='icontains')
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')

    class Meta:
        model = Product
        fields = ['min_price', 'max_price', 'name', 'category', 'is_active']


class ProductViewSet(viewsets.ModelViewSet):
    filterset_class = ProductFilter

    # SearchFilter — ?search=term
    # Prefixes: ^ starts-with, = exact, @ full-text, no prefix = icontains
    search_fields = ['^name', '=sku', '@description', 'category__name']

    # OrderingFilter — ?ordering=price,-created_at
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']  # default
```

### 4.7 Pagination

```python
from rest_framework.pagination import PageNumberPagination, CursorPagination

class StandardPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class FeedCursorPagination(CursorPagination):
    """Best for real-time feeds or large datasets — most DB-efficient."""
    page_size = 20
    ordering = '-created_at'  # Must be unique, immutable field
```

| Style | Use case |
|---|---|
| `PageNumberPagination` | Default — easy for clients |
| `LimitOffsetPagination` | When clients need flexible window |
| `CursorPagination` | Real-time feeds, millions of rows |

Always paginate. Pagination is disabled by default — configure `DEFAULT_PAGINATION_CLASS`.

### 4.8 Versioning

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
}

# config/urls.py
urlpatterns = [
    path('api/<version>/', include('apps.api_router')),
]
```

#### Version-specific logic

```python
def get_serializer_class(self):
    if self.request.version == 'v2':
        return UserSerializerV2
    return UserSerializerV1
```

**Versioning rule:** Models and services are version-agnostic. Only serializers, views, and
URLs are versioned.

---

## 5. Authentication and Permissions

### JWT (SimpleJWT) — recommended for SPAs and mobile apps
```python
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Short-lived
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,                # Requires token_blacklist app
    'SIGNING_KEY': env('JWT_SECRET_KEY'),            # Separate from Django SECRET_KEY
    'AUTH_HEADER_TYPES': ('Bearer',),
    'UPDATE_LAST_LOGIN': False,                      # Avoids DB write on every validation
}
```

### Custom permissions always implement both levels
```python
class IsOwnerOrReadOnly(BasePermission):
    message = 'You must be the owner of this object.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.owner == request.user
```

### Field-level permissions via `to_representation()`
```python
def to_representation(self, instance):
    data = super().to_representation(instance)
    request = self.context.get('request')
    if not request or not request.user.is_staff:
        data.pop('salary', None)
        data.pop('internal_notes', None)
    return data
```

---

## 6. Query Optimization (Preventing N+1)

The N+1 problem is the #1 DRF performance issue. It occurs silently when a serializer
accesses a related object on each item in a queryset.

```python
class ArticleViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return (
            Article.objects
            .select_related('author', 'category')         # ForeignKey → SQL JOIN
            .prefetch_related(                             # ManyToMany → separate query
                'tags',
                Prefetch(
                    'comments',
                    queryset=Comment.objects.filter(is_approved=True),
                    to_attr='approved_comments'            # Required for SMF cache access
                )
            )
            .annotate(comment_count=Count('comments'))    # DB aggregation >> Python loops
        )
```

### `select_related` vs `prefetch_related`
- `select_related` → ForeignKey, OneToOneField → SQL JOIN (one query)
- `prefetch_related` → ManyToManyField, reverse FK → separate query, Python join
- Use `Prefetch()` with `to_attr` when you need to filter/order the related set

### Annotations over Python aggregation
```python
# BAD: triggers N queries
total = serializers.SerializerMethodField()
def get_total(self, obj):
    return sum(item.qty * item.price for item in obj.items.all())

# GOOD: one annotation in the DB
total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
# In ViewSet.get_queryset():
.annotate(total=Sum(F('items__quantity') * F('items__unit_price')))
```

---

## 7. Service Layer Pattern

Business logic belongs in `services.py`, not in views or serializers. Services are plain
Python — no HttpRequest, no DRF imports.

```python
# apps/orders/services.py
from django.db import transaction

@transaction.atomic
def create_order(user, cart_items: list[dict]) -> Order:
    """Create an order. Raises InsufficientStockError if stock unavailable."""
    order = Order.objects.create(user=user, status='pending')
    for item in cart_items:
        decrement_stock(product_id=item['product_id'], quantity=item['quantity'])
        OrderItem.objects.create(order=order, **item)
    transaction.on_commit(lambda: send_confirmation.delay(order.id))
    return order
```

```python
# apps/orders/api/v1/views.py
def perform_create(self, serializer):
    order = create_order(
        user=self.request.user,
        cart_items=serializer.validated_data['items'],
    )
    serializer.instance = order
```

**Where logic belongs:**
- **Model methods** — single-model logic (`model.is_expired()`, `model.publish()`)
- **Services** — cross-model operations, external calls, anything reusable from Celery/CLI
- **Serializers** — data transformation and validation only
- **Views** — HTTP routing, auth, delegating to services

**Avoid signals for business logic** — they are implicit and hard to trace. Use
`transaction.on_commit()` for post-transaction side effects.

---

## 8. Testing

Core patterns first, then the deep reference (structure, fixtures/factories, view tests, auth
patterns, serializer tests, permission-boundary testing, pagination testing).

```python
# conftest.py
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def auth_client(api_client, user_factory):
    user = user_factory()
    api_client.force_authenticate(user=user)
    return api_client, user
```

```python
# test_views.py
@pytest.mark.django_db
class TestProductViewSet:
    def test_list_returns_only_owned_products(self, auth_client, product_factory):
        client, user = auth_client
        own = product_factory(owner=user)
        other = product_factory()       # different owner

        response = client.get(reverse('product-list'))

        assert response.status_code == status.HTTP_200_OK
        ids = [p['id'] for p in response.data['results']]
        assert own.id in ids
        assert other.id not in ids      # ownership scoping verified

    def test_unauthenticated_returns_401(self, api_client):
        response = api_client.get(reverse('product-list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
```

**Testing checklist:**
- Always test: success cases, auth boundaries (unauthenticated, wrong user), validation errors
- Verify both status code AND response data shape
- Test DB state after mutations (POST, PUT, DELETE)
- Use `factory_boy` or `model_bakery` for test data — avoid raw `Model.objects.create()` in fixtures
- Prefer `pytest-django` over `APITestCase` for fixture composability

### 8.1 Test Structure

```
apps/
  products/
    tests/
      conftest.py          ← shared fixtures for this app
      factories.py         ← factory_boy factories
      test_models.py
      test_serializers.py
      test_views.py
```

#### pytest.ini / pyproject.toml

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --reuse-db --strict-markers
```

### 8.2 Fixtures and Factories

#### conftest.py

```python
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user(db, django_user_model):
    return django_user_model.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='TestPass123!'
    )

@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client, user

@pytest.fixture
def admin_user(db, django_user_model):
    return django_user_model.objects.create_superuser(
        username='admin', email='admin@example.com', password='AdminPass123!'
    )

@pytest.fixture
def admin_client(api_client, admin_user):
    api_client.force_authenticate(user=admin_user)
    return api_client, admin_user
```

#### factory_boy factories

```python
# factories.py
import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from apps.products.models import Product, Category

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.LazyAttribute(lambda obj: f'{obj.username}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'TestPass123!')

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker('word')
    slug = factory.LazyAttribute(lambda obj: obj.name.lower())

class ProductFactory(DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('product_name', locale='en_US')
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    category = factory.SubFactory(CategoryFactory)
    owner = factory.SubFactory(UserFactory)
    is_active = True
```

### 8.3 View Tests

#### Core pattern — test class per ViewSet

```python
import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestProductViewSet:
    # --- List ---
    def test_list_returns_ok(self, auth_client, product_factory):
        client, user = auth_client
        product_factory(owner=user)

        response = client.get(reverse('product-list'))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_list_only_returns_owned_products(self, auth_client, product_factory):
        client, user = auth_client
        own = product_factory(owner=user)
        other = product_factory()   # different owner

        response = client.get(reverse('product-list'))

        ids = [p['id'] for p in response.data['results']]
        assert own.id in ids
        assert other.id not in ids

    # --- Create ---
    def test_create_sets_owner_from_request(self, auth_client):
        client, user = auth_client
        payload = {'name': 'Widget', 'price': '9.99', 'category': 1}

        response = client.post(reverse('product-list'), payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['owner'] == user.id

    def test_create_missing_name_returns_400(self, auth_client):
        client, _ = auth_client
        response = client.post(reverse('product-list'), {'price': '9.99'}, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data

    # --- Retrieve ---
    def test_retrieve_returns_detail(self, auth_client, product_factory):
        client, user = auth_client
        product = product_factory(owner=user)

        response = client.get(reverse('product-detail', kwargs={'pk': product.pk}))

        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == product.id
        assert response.data['name'] == product.name

    # --- Update ---
    def test_partial_update_succeeds(self, auth_client, product_factory):
        client, user = auth_client
        product = product_factory(owner=user)

        response = client.patch(
            reverse('product-detail', kwargs={'pk': product.pk}),
            {'price': '19.99'},
            format='json',
        )

        assert response.status_code == status.HTTP_200_OK
        product.refresh_from_db()
        assert str(product.price) == '19.99'

    # --- Delete ---
    def test_destroy_removes_product(self, auth_client, product_factory):
        client, user = auth_client
        product = product_factory(owner=user)

        response = client.delete(reverse('product-detail', kwargs={'pk': product.pk}))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Product.objects.filter(pk=product.pk).exists()
```

### 8.4 Authentication Testing Patterns

```python
@pytest.mark.django_db
class TestAuthBoundaries:
    def test_unauthenticated_list_returns_401(self, api_client):
        response = api_client.get(reverse('product-list'))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_create_returns_401(self, api_client):
        response = api_client.post(reverse('product-list'), {})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_other_user_cannot_update(self, api_client, product_factory, user_factory):
        owner = user_factory()
        attacker = user_factory()
        product = product_factory(owner=owner)

        api_client.force_authenticate(user=attacker)
        response = api_client.patch(
            reverse('product-detail', kwargs={'pk': product.pk}),
            {'price': '1.00'},
            format='json'
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_other_user_cannot_delete(self, api_client, product_factory, user_factory):
        owner = user_factory()
        attacker = user_factory()
        product = product_factory(owner=owner)

        api_client.force_authenticate(user=attacker)
        response = api_client.delete(reverse('product-detail', kwargs={'pk': product.pk}))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_access_any_product(self, admin_client, product_factory, user_factory):
        client, _ = admin_client
        owner = user_factory()
        product = product_factory(owner=owner)

        response = client.get(reverse('product-detail', kwargs={'pk': product.pk}))
        assert response.status_code == status.HTTP_200_OK
```

### 8.5 Serializer Unit Tests

```python
@pytest.mark.django_db
class TestProductSerializer:
    def test_valid_data_is_accepted(self, category_factory):
        category = category_factory()
        data = {'name': 'Widget', 'price': '9.99', 'category': category.pk}

        serializer = ProductWriteSerializer(data=data)

        assert serializer.is_valid(), serializer.errors

    def test_negative_price_rejected(self, category_factory):
        data = {'name': 'Widget', 'price': '-1.00', 'category': category_factory().pk}

        serializer = ProductWriteSerializer(data=data)

        assert not serializer.is_valid()
        assert 'price' in serializer.errors

    def test_read_serializer_includes_category_name(self, product_factory):
        product = product_factory()

        serializer = ProductDetailSerializer(product)

        assert 'category_name' in serializer.data
        assert serializer.data['category_name'] == product.category.name

    def test_sensitive_fields_hidden_for_non_staff(self, rf, user_factory, product_factory):
        user = user_factory()
        product = product_factory(owner=user)
        request = rf.get('/')
        request.user = user

        serializer = ProductDetailSerializer(product, context={'request': request})

        assert 'internal_cost' not in serializer.data
```

### 8.6 Permission Boundary Testing

Test all four permission boundaries for every protected resource:

1. Unauthenticated → 401
2. Authenticated, not owner → 403
3. Owner → 200/201/204
4. Staff/admin → 200/201/204

```python
@pytest.mark.parametrize('method,expected_anon,expected_other', [
    ('get', 401, 403),
    ('patch', 401, 403),
    ('delete', 401, 403),
])
def test_permission_boundaries(method, expected_anon, expected_other,
                               api_client, product_factory, user_factory):
    owner = user_factory()
    product = product_factory(owner=owner)
    url = reverse('product-detail', kwargs={'pk': product.pk})

    # Unauthenticated
    response = getattr(api_client, method)(url)
    assert response.status_code == expected_anon

    # Different user
    api_client.force_authenticate(user=user_factory())
    response = getattr(api_client, method)(url)
    assert response.status_code == expected_other
```

### 8.7 Testing Pagination

```python
def test_list_is_paginated(self, auth_client, product_factory):
    client, user = auth_client
    product_factory.create_batch(25, owner=user)

    response = client.get(reverse('product-list'))

    assert response.status_code == status.HTTP_200_OK
    assert 'results' in response.data
    assert 'count' in response.data
    assert 'next' in response.data
    assert len(response.data['results']) == 20  # Default PAGE_SIZE
    assert response.data['count'] == 25
```

---

## 9. Error Handling

```python
# yourapp/exceptions.py
from rest_framework.views import exception_handler
from rest_framework.response import Response
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        response.data = {
            'error': {
                'status_code': response.status_code,
                'message': response.data.get('detail', str(exc)),
                'errors': response.data if isinstance(response.data, dict) else None,
            }
        }
    else:
        logger.exception("Unhandled exception", exc_info=exc)
        response = Response(
            {'error': {'status_code': 500, 'message': 'Internal server error'}},
            status=500
        )
    return response
```

---

## 10. Documentation (drf-spectacular)

Use `drf-spectacular` (OpenAPI 3). Do NOT use `drf-yasg` (OpenAPI 2 only, legacy).

```python
INSTALLED_APPS = ['drf_spectacular']
REST_FRAMEWORK = {'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema'}

SPECTACULAR_SETTINGS = {
    'TITLE': 'My API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,    # Disable in production
}
```

---

## 11. Models

- **Abstract Base Models:** Create `TimeStampedModel` (with `created_at`, `updated_at`) and inherit from it everywhere. Use `UUIDField` as PK over auto-increment.
- **`__str__`:** Always define a meaningful `__str__` on every model.
- **`related_name`:** Always set on `ForeignKey`, `ManyToManyField`, `OneToOneField`.
- **Database Indexes:** Add `db_index=True` or `Meta.indexes` on fields used in `WHERE`, `ORDER BY`, or `JOIN`.
- **`choices` with Enums:** Use `models.TextChoices` / `models.IntegerChoices` — no bare tuples.
- **No logic in `save()`:** Avoid business logic in `save()` overrides; prefer the service layer.

```python
import uuid
from django.db import models

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Hero(TimeStampedModel):
    class PowerLevel(models.IntegerChoices):
        LOW = 1, "Low"
        MEDIUM = 2, "Medium"
        HIGH = 3, "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    team = models.ForeignKey(
        "teams.Team", on_delete=models.CASCADE, related_name="heroes"
    )
    power_level = models.IntegerField(
        choices=PowerLevel.choices, default=PowerLevel.LOW
    )

    def __str__(self) -> str:
        return self.name
```

---

## 12. Security

- **`DEBUG = False` in production.** Always. Load via environment variable.
- **No secrets in code.** Use `django-environ` or `python-decouple`. Never commit `.env`.
- **HTTPS enforcement:**

```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

- **CORS:** Use `django-cors-headers`. Set `CORS_ALLOWED_ORIGINS` explicitly. Never `CORS_ALLOW_ALL_ORIGINS = True` in production.
- **SQL Injection:** Always use Django ORM or parameterized `.raw()` queries. Never concatenate user input into query strings.
- **Mass Assignment:** Use explicit `fields` allowlists in serializers (never `__all__`).
- **Rate Limiting:** Apply DRF throttling globally and per-view. Use `django-axes` for login brute-force protection.
- **Audit Logging:** Log all auth failures, permission denials, and sensitive data access.
- **Dependency scanning:** Run `pip-audit` regularly. Monitor CVEs.

---

## Anti-pattern quick reference

| Anti-pattern | Instead |
|---|---|
| `fields = '__all__'` (especially on models with PII) | Explicit `fields` allowlist, always |
| No `select_related`/`prefetch_related` | Add to `get_queryset()` |
| `AllowAny` as default permission | Default to `IsAuthenticated` |
| No pagination configured | Set `DEFAULT_PAGINATION_CLASS` |
| No throttling configured | Set `DEFAULT_THROTTLE_CLASSES` |
| Business logic in views/serializers | Move to `services.py` |
| `BrowsableAPIRenderer` in production | Remove from `DEFAULT_RENDERER_CLASSES` |
| `is_valid()` without `raise_exception=True` | Always use `raise_exception=True` |
| List endpoint not scoped to request.user | Filter `get_queryset()` by user |
| `post_save` signal for emails/tasks | Use `transaction.on_commit()` in service |
| Writable `depth = N` on ModelSerializer | Override `create()`/`update()` explicitly |
| Cross-field validation in `validate_<field>()` | Use `validate()` for multi-field rules |
| Read queries mixed into `services.py` | Extract to `selectors.py` |
| Logic in `save()` override | Move to service function |
| Bare tuples for model `choices` | Use `TextChoices` / `IntegerChoices` |
| `CORS_ALLOW_ALL_ORIGINS = True` | Explicit `CORS_ALLOWED_ORIGINS` list |

---

## Pre-flight checklist — run before delivering any DRF code

Run this on every DRF PR review:

- [ ] Serializer uses explicit `fields` allowlist (never `__all__` or `exclude`)
- [ ] `get_queryset()` scopes results to `request.user` for user-owned resources
- [ ] `select_related`/`prefetch_related` present for all related field traversals
- [ ] `DEFAULT_PERMISSION_CLASSES` is `IsAuthenticated` (not `AllowAny`)
- [ ] Pagination is configured globally (`DEFAULT_PAGINATION_CLASS`)
- [ ] Throttling is configured (`DEFAULT_THROTTLE_CLASSES`)
- [ ] `BrowsableAPIRenderer` is disabled in production settings
- [ ] Business logic lives in `services.py`; read queries in `selectors.py`
- [ ] `serializer.is_valid(raise_exception=True)` — never `if not serializer.is_valid()`
- [ ] Tests verify both status codes AND response data shape
- [ ] `DEBUG = False` and secrets loaded from environment in production settings
- [ ] `CORS_ALLOW_ALL_ORIGINS` is not `True` in production
