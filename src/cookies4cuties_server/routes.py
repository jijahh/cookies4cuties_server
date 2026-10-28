from datetime import datetime
from decimal import Decimal
from typing import Annotated
from uuid import uuid4
from pathlib import PurePath
from supabase import Client
import json
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)

from .auth import require_admin
from .config import get_settings
from .supabase_client import get_supabase

router = APIRouter()
settings = get_settings()

SupabaseDep = Annotated[Client, Depends(get_supabase)]

ALLOWED_IMAGE_TYPES = {
    "image/jpeg": "jpg",
    "image/jpg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}

PICKUP_LOCATIONS = {
    "pampanga",
    "katipunan",
    "rockwell",
}

PAYMENT_METHODS = {
    "cash_on_pickup",
    "cash_on_delivery",
    "online",
}


@router.post("/orders", status_code=201)
async def create_order(
    supabase: SupabaseDep,
    email: Annotated[str, Form()],
    phone_number: Annotated[str, Form()],
    items: Annotated[
        str,
        Form(description='JSON array, e.g. [{"product_id": 1, "quantity": 2}]'),
    ],
    total_price: Annotated[Decimal, Form(gt=0)],
    pickup_location: Annotated[str, Form()],
    payment_method: Annotated[str, Form()],
    proof_of_payment: Annotated[
        UploadFile | None,
        File(description="Required for online payments"),
    ] = None,
):
    """Create an order and upload its payment proof, if applicable."""

    storage_path = None
    uploaded_to_storage = False

    try:
        # Validate basic customer information.
        email = email.strip()
        phone_number = phone_number.strip()

        if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            raise HTTPException(422, "Invalid email address.")

        if not phone_number:
            raise HTTPException(422, "Phone number is required.")

        if pickup_location not in PICKUP_LOCATIONS:
            raise HTTPException(422, "Invalid pickup location.")

        if payment_method not in PAYMENT_METHODS:
            raise HTTPException(422, "Invalid payment method.")

        # Validate order items.
        try:
            parsed_items = json.loads(items)

            if not isinstance(parsed_items, list) or not parsed_items:
                raise ValueError("Items must be a non-empty JSON array.")

            if len(parsed_items) > 20:
                raise ValueError("Too many distinct items.")

            validated_items = []

            for item in parsed_items:
                product_id = int(item["product_id"])
                quantity = int(item["quantity"])

                if product_id <= 0 or quantity <= 0:
                    raise ValueError("Product IDs and quantities must be positive.")

                validated_items.append(
                    {
                        "product_id": product_id,
                        "quantity": quantity,
                    }
                )

        except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            raise HTTPException(
                422,
                f"Invalid order items: {exc}",
            ) from exc

        # Online payment requires a proof image.
        if payment_method == "online" and proof_of_payment is None:
            raise HTTPException(
                422,
                "Please upload proof of payment for online orders.",
            )

        # Don't accept proof images for cash payments in this version.
        if payment_method != "online" and proof_of_payment is not None:
            raise HTTPException(
                422,
                "Proof of payment is only accepted for online payments.",
            )

        # Upload payment proof to Supabase Storage.
        if proof_of_payment is not None:
            content_type = proof_of_payment.content_type

            if content_type not in ALLOWED_IMAGE_TYPES:
                raise HTTPException(
                    415,
                    "Only JPEG, PNG, and WebP images are supported.",
                )

            content = await proof_of_payment.read()
            max_size = settings.max_upload_size_mb * 1024 * 1024

            if not content:
                raise HTTPException(400, "The uploaded image is empty.")

            if len(content) > max_size:
                raise HTTPException(
                    413,
                    f"Image must be {settings.max_upload_size_mb} MB or smaller.",
                )

            extension = ALLOWED_IMAGE_TYPES[content_type]
            storage_path = f"orders/{uuid4().hex}.{extension}"

            bucket = supabase.storage.from_(settings.supabase_storage_bucket)

            bucket.upload(
                storage_path,
                content,
                {
                    "content-type": content_type,
                    "upsert": "false",
                },
            )

            uploaded_to_storage = True

        # The database supplies the order ID and timestamp.
        order_data = {
            "email": email,
            "phone": phone_number,
            "items": validated_items,
            "total_price": str(total_price),
            "pickup_location": pickup_location,
            "payment_method": payment_method,
            "proof_url": storage_path,
            "order_status": "pending" if payment_method == "online" else "confirmed",
            "payment_verified": False if payment_method == "online" else True,
        }

        result = supabase.table("orders").insert(order_data).execute()

        if not result.data:
            raise RuntimeError("No order record was returned.")

        return result.data[0]

    except HTTPException:
        if uploaded_to_storage and storage_path:
            try:
                supabase.storage.from_(settings.supabase_storage_bucket).remove(
                    [storage_path]
                )
            except Exception:
                pass
        raise

    except Exception as exc:
        if uploaded_to_storage and storage_path:
            try:
                supabase.storage.from_(settings.supabase_storage_bucket).remove(
                    [storage_path]
                )
            except Exception:
                pass
        print(exc)

        raise HTTPException(
            502,
            "Could not create the order. Check your Supabase configuration.",
        ) from exc

    finally:
        if proof_of_payment is not None:
            await proof_of_payment.close()


@router.get(
    "/admin/orders",
    dependencies=[Depends(require_admin)],
)
def get_orders(
    supabase: SupabaseDep,
    order_status: str | None = None,
    payment_method: str | None = None,
    payment_verified: bool | None = None,
    email: str | None = None,
    pickup_location: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    min_total: Decimal | None = Query(default=None, ge=0),
    max_total: Decimal | None = Query(default=None, ge=0),
    sort_by: str = Query(
        default="created_at",
        pattern="^(created_at|total_price|order_status|email|pickup_location|payment_method)$",
    ),
    sort_order: str = Query(
        default="desc",
        pattern="^(asc|desc)$",
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if created_from and created_to and created_from > created_to:
        raise HTTPException(
            status_code=422,
            detail="created_from must be earlier than created_to.",
        )

    if min_total is not None and max_total is not None:
        if min_total > max_total:
            raise HTTPException(
                status_code=422,
                detail="min_total cannot exceed max_total.",
            )

    query = supabase.table("orders").select("*")

    # Optional filters
    if order_status:
        query = query.eq("order_status", order_status)

    if payment_method:
        query = query.eq("payment_method", payment_method)

    if payment_verified is not None:
        query = query.eq("payment_verified", payment_verified)

    if email:
        query = query.ilike("email", f"%{email.strip()}%")

    if pickup_location:
        query = query.eq("pickup_location", pickup_location)

    if created_from:
        query = query.gte("created_at", created_from.isoformat())

    if created_to:
        query = query.lte("created_at", created_to.isoformat())

    if min_total is not None:
        query = query.gte("total_price", str(min_total))

    if max_total is not None:
        query = query.lte("total_price", str(max_total))

    # Sorting and pagination
    query = query.order(
        sort_by,
        desc=(sort_order == "desc"),
    )

    query = query.range(offset, offset + limit - 1)

    result = query.execute()

    return result.data


@router.post(
    "/admin/products",
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create_product(
    supabase: SupabaseDep,
    product_name: Annotated[
        str,
        Form(min_length=1, max_length=120),
    ],
    unit_price: Annotated[
        Decimal,
        Form(gt=0),
    ],
    product_details: Annotated[str, Form()] = "",
    active: Annotated[bool, Form()] = True,
    image: Annotated[UploadFile | None, File()] = None,
):
    product_name = product_name.strip()

    if not product_name:
        raise HTTPException(
            status_code=422,
            detail="Product name cannot be empty.",
        )

    storage_path = None
    uploaded_to_storage = False

    try:
        # Optionally upload the product image.
        if image is not None:
            allowed_types = {
                "image/jpeg": "jpg",
                "image/jpg": "jpg",
                "image/png": "png",
                "image/webp": "webp",
            }

            if image.content_type not in allowed_types:
                raise HTTPException(
                    status_code=415,
                    detail="Only JPEG, PNG, and WebP images are supported.",
                )

            content = await image.read()
            max_size = settings.max_upload_size_mb * 1024 * 1024

            if not content:
                raise HTTPException(
                    status_code=400,
                    detail="The uploaded image is empty.",
                )

            if len(content) > max_size:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"Image must be {settings.max_upload_size_mb} " "MB or smaller."
                    ),
                )

            extension = allowed_types[image.content_type]
            storage_path = f"products/{uuid4().hex}.{extension}"

            bucket = supabase.storage.from_(settings.supabase_storage_bucket)

            bucket.upload(
                storage_path,
                content,
                {
                    "content-type": image.content_type,
                    "upsert": "false",
                },
            )

            uploaded_to_storage = True

        # Insert product details into the database.
        product_data = {
            "product_name": product_name,
            "unit_price": str(unit_price),
            "product_details": product_details.strip(),
            "product_image_path": storage_path,
            "active": active,
        }

        result = supabase.table("products").insert(product_data).execute()

        if not result.data:
            raise RuntimeError("Product record was not returned.")

        return result.data[0]

    except HTTPException:
        if uploaded_to_storage and storage_path:
            try:
                supabase.storage.from_(settings.supabase_storage_bucket).remove(
                    [storage_path]
                )
            except Exception:
                pass
        raise

    except Exception as exc:
        if uploaded_to_storage and storage_path:
            try:
                supabase.storage.from_(settings.supabase_storage_bucket).remove(
                    [storage_path]
                )
            except Exception:
                pass

        raise HTTPException(
            status_code=502,
            detail="Could not create the product. Check Supabase configuration.",
        ) from exc

    finally:
        if image is not None:
            await image.close()


@router.patch(
    "/admin/orders/{order_id}",
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def update_order(
    supabase: SupabaseDep,
    order_id: int,
    order_status: Annotated[str, Form()] = None,
    payment_verified: Annotated[bool, Form()] = None,
):
    if not order_status and not payment_verified:
        raise HTTPException(status_code=400, detail="No fields provided for update")
    update_data = {}
    if order_status:
        update_data["order_status"] = order_status
    if payment_verified:
        update_data["payment_verified"] = payment_verified
    try:
        response = (
            supabase.table("orders").update(update_data).eq("id", order_id).execute()
        )
        if not response.data:
            raise HTTPException(status_code=404, detail="Order not found")

        return response.data
    except Exception as exc:
        raise HTTPException(
            502,
            "Could not find order. Check your Supabase configuration.",
        ) from exc
