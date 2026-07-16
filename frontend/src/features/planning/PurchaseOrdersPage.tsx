import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function PurchaseOrdersPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/v1/purchases', { headers: authHeaders() })
      .then(res => res.json())
      .then(res => {
        setData(res?.items || []);
        setLoading(false);
      })
      .catch(() => {
        setData([]);
        setLoading(false);
      });
  }, []);

  const items = Array.isArray(data) ? data : [];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Purchase Orders</h1>
        <p className="text-muted-foreground">Incoming supplier materials, expected receipt dates, and delivery status.</p>
      </div>
      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8">Loading Purchase Orders...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">PO Number</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Supplier</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Plant</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Order Date</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">ETA Date</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Total Cost</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((po, idx) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4 font-bold">{po.po_number || po.purchase_number}</td>
                      <td className="py-3 px-4">{po.supplier?.name || "Global Vendor"}</td>
                      <td className="py-3 px-4 text-xs">{po.plant?.name || "Main Plant"}</td>
                      <td className="py-3 px-4">{po.order_date}</td>
                      <td className="py-3 px-4 font-medium text-blue-600 dark:text-blue-400">{po.expected_receipt_date}</td>
                      <td className="py-3 px-4">${po.total_amount?.toLocaleString()}</td>
                      <td className="py-3 px-4">
                        <Badge variant={po.status === 'RECEIVED' ? 'default' : 'outline'}>
                          {po.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && (
                    <tr>
                      <td colSpan={7} className="text-center py-8 text-muted-foreground">No purchase orders found.</td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
