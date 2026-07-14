"""Main API v1 router."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    products,
    warehouses,
    customers,
    forecast,
    analytics,
    suppliers,
    purchases,
    sales,
    stock_adjustments,
    stock_ledger,
    reports,
    notifications,
    audit_logs,
    dashboard,
    health,
    planning_api,
)

api_router = APIRouter()

# Health check endpoints (no auth required)
api_router.include_router(health.router, tags=["Health"])

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(
    products.router, prefix="/products", tags=["Products"]
)
api_router.include_router(
    warehouses.router, prefix="/warehouses", tags=["Warehouses"]
)
api_router.include_router(
    customers.router, prefix="/customers", tags=["Customers"]
)
api_router.include_router(
    forecast.router, prefix="/forecast", tags=["Forecast"]
)
api_router.include_router(
    analytics.router, prefix="/analytics", tags=["Analytics"]
)
api_router.include_router(
    suppliers.router, prefix="/suppliers", tags=["Suppliers"]
)
api_router.include_router(
    purchases.router, prefix="/purchases", tags=["Purchases"]
)
api_router.include_router(sales.router, prefix="/sales", tags=["Sales"])
api_router.include_router(
    stock_ledger.router, prefix="/stock-ledger", tags=["Stock Ledger"]
)
api_router.include_router(
    stock_adjustments.router,
    prefix="/stock-adjustments",
    tags=["Stock Adjustments"],
)
api_router.include_router(reports.router, prefix="/reports", tags=["Reports"])
api_router.include_router(
    notifications.router, prefix="/notifications", tags=["Notifications"]
)
api_router.include_router(
    audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"]
)
api_router.include_router(
    planning_api.router, prefix="/planning", tags=["Planning"]
)
api_router.include_router(
    dashboard.router, prefix="/dashboard", tags=["Dashboard"]
)
