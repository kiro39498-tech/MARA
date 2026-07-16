import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { RefreshCw, Search, ChevronLeft, ChevronRight } from 'lucide-react';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function InventoryHealthPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const fetchHealth = () => {
    setLoading(true);
    const query = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
      paginated: 'true',
    });
    if (search) query.append('search', search);
    if (statusFilter) query.append('status_filter', statusFilter);

    fetch(`http://localhost:8000/api/v1/planning/inventory-health?${query.toString()}`, { headers: authHeaders() })
      .then(res => res.json())
      .then(res => {
        setData(res?.data || []);
        setTotal(res?.total || 0);
        setTotalPages(res?.total_pages || 1);
        setLoading(false);
      })
      .catch(() => {
        setData([]);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchHealth();
  }, [page, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchHealth();
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Inventory Health</h1>
          <p className="text-muted-foreground">Real-time stock buffers, reserved quantities, and safety violations.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={fetchHealth} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <form onSubmit={handleSearchSubmit} className="flex gap-2 w-full md:max-w-md">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input
              type="search"
              placeholder="Search by code, name, or plant..."
              className="pl-8 bg-background"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <Button type="submit">Search</Button>
        </form>

        <div className="flex gap-2 items-center w-full md:w-auto">
          <span className="text-sm text-muted-foreground whitespace-nowrap">Filter Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="border p-2 rounded bg-background text-sm w-full md:w-40"
          >
            <option value="">All Statuses</option>
            <option value="HEALTHY">Healthy</option>
            <option value="AT_RISK">At Risk</option>
            <option value="CRITICAL">Critical</option>
            <option value="SHORTAGE">Shortage</option>
          </select>
        </div>
      </div>

      <Card className="bg-card/45 backdrop-blur-md">
        <CardContent className="pt-6">
          {loading ? (
            <div className="text-center py-8">Loading Inventory Health...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead>
                  <tr className="border-b">
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Material</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Plant</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">On Hand</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Reserved</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Blocked</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Quality Hold</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Safety Stock</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Usable Qty</th>
                    <th className="py-3 px-4 font-semibold text-muted-foreground">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.map((inv, idx) => (
                    <tr key={idx} className="border-b last:border-0 hover:bg-muted/50">
                      <td className="py-3 px-4 font-semibold">
                        <div>{inv.material_code}</div>
                        <div className="text-xs text-muted-foreground font-normal">{inv.material_name}</div>
                      </td>
                      <td className="py-3 px-4 text-xs font-medium">{inv.plant_name}</td>
                      <td className="py-3 px-4">{inv.on_hand}</td>
                      <td className="py-3 px-4 text-orange-500">{inv.reserved}</td>
                      <td className="py-3 px-4 text-red-500">{inv.blocked}</td>
                      <td className="py-3 px-4 text-yellow-600">{inv.quality_hold}</td>
                      <td className="py-3 px-4 font-medium">{inv.safety_stock}</td>
                      <td className="py-3 px-4 font-bold text-green-600 dark:text-green-400">{inv.usable_inventory}</td>
                      <td className="py-3 px-4">
                        <Badge variant={inv.status === 'HEALTHY' ? 'default' : inv.status === 'AT_RISK' ? 'outline' : 'destructive'}>
                          {inv.status}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                  {data.length === 0 && (
                    <tr>
                      <td colSpan={9} className="text-center py-8 text-muted-foreground">
                        No inventory items matching selection.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex items-center justify-between mt-4 pt-4 border-t">
            <span className="text-sm text-muted-foreground">
              Showing page {page} of {totalPages} (Total {total} items)
            </span>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.max(1, p - 1))}
                disabled={page === 1 || loading}
              >
                <ChevronLeft className="h-4 w-4 mr-1" /> Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                disabled={page === totalPages || loading}
              >
                Next <ChevronRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
