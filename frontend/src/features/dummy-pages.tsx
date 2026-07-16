/**
 * dummy-pages.tsx — DEPRECATED COMPATIBILITY SHIM
 *
 * All page components have been migrated to their own feature directories.
 * This file re-exports from the new locations so any lingering imports continue
 * to work. Remove once all consumers have been updated.
 */

export { default as MaterialsPage }          from '@/features/planning/MaterialsPage';
export { default as PlantsPage }             from '@/features/planning/PlantsPage';
export { default as InventoryHealthPage }    from '@/features/planning/InventoryHealthPage';
export { default as ProductionOrdersPage }   from '@/features/planning/ProductionOrdersPage';
export { default as PurchaseOrdersPage }     from '@/features/planning/PurchaseOrdersPage';
export { default as MaterialProjectionPage } from '@/features/planning/MaterialProjectionPage';
export { default as ShortageAnalysisPage }   from '@/features/planning/ShortageAnalysisPage';
export { default as RecommendationsPage }    from '@/features/planning/RecommendationsPage';
export { default as SupplierPerformancePage } from '@/features/suppliers/SupplierPerformancePage';
export { default as PlanningCopilotPage }    from '@/features/ai/PlanningCopilotPage';

// Auth re-export (pass-through that was already here)
export { LoginPage } from '@/features/auth/LoginPage';

// Simple alias stubs
export function PurchasesPage() { return null; }
export function SalesPage()     { return null; }
export function UsersPage()     { return <div className="p-6">Users &amp; Roles Manager. Use Settings / User Management routes.</div>; }
