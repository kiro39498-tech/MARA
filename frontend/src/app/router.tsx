import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { AppLayout } from '@/layouts/AppLayout';
import { AuthLayout } from '@/layouts/AuthLayout';
import { RequireAuth, RequireGuest } from '@/app/route-guards';
import { RequirePermission } from '@/components/auth/RequirePermission';
import { PERMISSIONS } from '@/lib/rbac';

// Lazy loading Feature Pages for code-splitting
const LoginPage = lazy(() => import('@/features/auth/LoginPage').then(m => ({ default: m.LoginPage })));
const ForgotPasswordPage = lazy(() => import('@/features/auth/ForgotPasswordPage').then(m => ({ default: m.ForgotPasswordPage })));
const ResetPasswordPage = lazy(() => import('@/features/auth/ResetPasswordPage').then(m => ({ default: m.ResetPasswordPage })));
const DashboardPage = lazy(() => import('@/features/dashboard/DashboardPage').then(m => ({ default: m.DashboardPage })));
// ProductsPage → MaterialsPage (planning) is used for /products
const SuppliersPage = lazy(() => import('@/features/suppliers/SuppliersPage').then(m => ({ default: m.SuppliersPage })));
// WarehousesListPage → PlantsPage is used for /warehouses
const CustomersListPage = lazy(() => import('@/features/customers/CustomersListPage').then(m => ({ default: m.CustomersListPage })));
const CustomerDetailsPage = lazy(() => import('@/features/customers/CustomerDetailsPage').then(m => ({ default: m.CustomerDetailsPage })));
const PurchaseDetailsPage = lazy(() => import('@/features/purchases/PurchaseDetailsPage').then(m => ({ default: m.PurchaseDetailsPage })));
const PurchaseWizard = lazy(() => import('@/features/purchases/PurchaseWizard').then(m => ({ default: m.PurchaseWizard })));

// SalesPage → ProductionOrdersPage is used for /sales
const CreateSalePage = lazy(() => import('@/features/sales/CreateSalePage').then(m => ({ default: m.CreateSalePage })));
const SaleDetailsPage = lazy(() => import('@/features/sales/SaleDetailsPage').then(m => ({ default: m.SaleDetailsPage })));

const StockLedgerPage = lazy(() => import('@/features/stock/StockLedgerPage').then(m => ({ default: m.StockLedgerPage })));
const StockAdjustmentsPage = lazy(() => import('@/features/stock-adjustments/StockAdjustmentsPage').then(m => ({ default: m.StockAdjustmentsPage })));

const ReportsPage = lazy(() => import('@/features/reports/ReportsPage'));

// AlertsPage → ShortageAnalysisPage is used for /alerts
// AIForecastPage → MaterialProjectionPage is used for /ai/forecast
// AIReorderPage → RecommendationsPage is used for /ai/reorder
const AuditLogsPage = lazy(() => import('@/features/audit/AuditLogsPage').then(m => ({ default: m.default || m })));
const UnauthorizedPage = lazy(() => import('@/features/auth/UnauthorizedPage').then(m => ({ default: m.UnauthorizedPage })));
const SettingsPage = lazy(() => import('@/features/settings/SettingsPage').then(m => ({ default: m.SettingsPage })));

const UsersPage = lazy(() => import('@/features/users/UsersPage').then(m => ({ default: m.UsersPage })));
const DebugAuthPage = lazy(() => import('@/features/debug/DebugAuthPage').then(m => ({ default: m.DebugAuthPage })));

// Planning feature pages — migrated from dummy-pages.tsx
const MaterialsPage = lazy(() => import('@/features/planning/MaterialsPage'));
const PlantsPage = lazy(() => import('@/features/planning/PlantsPage'));
const InventoryHealthPage = lazy(() => import('@/features/planning/InventoryHealthPage'));
const ProductionOrdersPage = lazy(() => import('@/features/planning/ProductionOrdersPage'));
const PurchaseOrdersPage = lazy(() => import('@/features/planning/PurchaseOrdersPage'));
const MaterialProjectionPage = lazy(() => import('@/features/planning/MaterialProjectionPage'));
const ShortageAnalysisPage = lazy(() => import('@/features/planning/ShortageAnalysisPage'));
const RecommendationsPage = lazy(() => import('@/features/planning/RecommendationsPage'));
const SupplierPerformancePage = lazy(() => import('@/features/suppliers/SupplierPerformancePage'));
const PlanningCopilotPage = lazy(() => import('@/features/ai/PlanningCopilotPage'));

// Fallback skeleton loader while routes load
const PageLoader = () => (
    <div className="flex items-center justify-center p-8 h-full">
        <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
    </div>
);

export function AppRouter() {
    return (
        <Suspense fallback={<PageLoader />}>
            <Routes>
                <Route path="/debug-auth" element={<DebugAuthPage />} />

                {/* Auth Routes */}
                <Route element={<RequireGuest />}>
                    <Route element={<AuthLayout />}>
                        <Route path="/auth/login" element={<LoginPage />} />
                        <Route path="/auth/forgot-password" element={<ForgotPasswordPage />} />
                        <Route path="/auth/reset-password" element={<ResetPasswordPage />} />
                    </Route>
                </Route>

                {/* Protected App Routes */}
                <Route element={<RequireAuth />}>
                    <Route element={<AppLayout />}>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<DashboardPage />} />

                        {/* Manufacturing Planning Routes */}
                        <Route path="/materials" element={<MaterialsPage />} />
                        <Route path="/plants" element={<PlantsPage />} />
                        <Route path="/inventory-health" element={<InventoryHealthPage />} />
                        <Route path="/production-orders" element={<ProductionOrdersPage />} />
                        <Route path="/purchase-orders" element={<PurchaseOrdersPage />} />
                        
                        <Route path="/material-projection" element={<MaterialProjectionPage />} />
                        <Route path="/shortage-analysis" element={<ShortageAnalysisPage />} />
                        <Route path="/recommendations" element={<RecommendationsPage />} />
                        <Route path="/supplier-performance" element={<SupplierPerformancePage />} />
                        <Route path="/planning-copilot" element={<PlanningCopilotPage />} />

                        <Route path="/products" element={<MaterialsPage />} />
                        <Route path="/suppliers" element={<SuppliersPage />} />
                        <Route element={<RequirePermission permission={PERMISSIONS.WAREHOUSE_VIEW} />}>
                            <Route path="/warehouses" element={<PlantsPage />} />
                        </Route>
                        <Route element={<RequirePermission permission={PERMISSIONS.CUSTOMER_VIEW} />}>
                            <Route path="/customers" element={<CustomersListPage />} />
                            <Route path="/customers/:id" element={<CustomerDetailsPage />} />
                        </Route>
                        <Route path="/purchases">
                            <Route index element={<PurchaseOrdersPage />} />
                            <Route path="new" element={<PurchaseWizard />} />
                            <Route path=":id" element={<PurchaseDetailsPage />} />
                        </Route>
                        <Route path="/sales">
                            <Route index element={<ProductionOrdersPage />} />
                            <Route path="new" element={<CreateSalePage />} />
                            <Route path=":id" element={<SaleDetailsPage />} />
                        </Route>

                        <Route path="/stock-ledger" element={<StockLedgerPage />} />
                        <Route element={<RequirePermission permission={PERMISSIONS.STOCK_ADJUSTMENT_VIEW} />}>
                            <Route path="/stock-adjustments" element={<StockAdjustmentsPage />} />
                        </Route>

                        <Route element={<RequirePermission permission={PERMISSIONS.REPORTS_VIEW} />}>
                            <Route path="/reports" element={<ReportsPage />} />
                        </Route>

                        <Route element={<RequirePermission permission={PERMISSIONS.ALERTS_VIEW} />}>
                            <Route path="/alerts" element={<ShortageAnalysisPage />} />
                        </Route>

                        <Route element={<RequirePermission permission={PERMISSIONS.AI_FORECAST_VIEW} />}>
                            <Route path="/ai/forecast" element={<MaterialProjectionPage />} />
                        </Route>

                        <Route element={<RequirePermission permission={PERMISSIONS.AI_REORDER_VIEW} />}>
                            <Route path="/ai/reorder" element={<RecommendationsPage />} />
                        </Route>

                        <Route element={<RequirePermission permission={PERMISSIONS.ADMIN_AUDIT_VIEW} />}>
                            <Route path="/audit-logs" element={<AuditLogsPage />} />
                        </Route>

                        <Route path="/settings" element={<SettingsPage />} />

                        {/* Admin only - requires permission */}
                        <Route element={<RequirePermission permission={PERMISSIONS.ADMIN_USERS_MANAGE} />}>
                            <Route path="/users" element={<UsersPage />} />
                        </Route>

                        {/* Unauthorized page */}
                        <Route path="/unauthorized" element={<UnauthorizedPage />} />

                        {/* Fallback 404 */}
                        <Route path="*" element={
                            <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                                <h1 className="text-4xl font-bold">404</h1>
                                <p className="text-xl text-muted-foreground">Page Not Found</p>
                            </div>
                        } />
                    </Route>
                </Route>
            </Routes>
        </Suspense>
    );
}
