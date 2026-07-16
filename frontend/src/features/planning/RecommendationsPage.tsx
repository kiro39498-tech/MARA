import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronLeft, ChevronRight, RefreshCw } from 'lucide-react';

const authHeaders = () => ({
  'Authorization': `Bearer ${localStorage.getItem('access_token') || ''}`,
  'Content-Type': 'application/json',
});

export default function RecommendationsPage() {
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [actionFilter, setActionFilter] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const fetchRecommendations = () => {
    setLoading(true);
    const query = new URLSearchParams({
      page: String(page),
      page_size: String(pageSize),
      paginated: 'true',
    });
    if (statusFilter) query.append('status_filter', statusFilter);
    if (actionFilter) query.append('action_type', actionFilter);

    fetch(`http://localhost:8000/api/v1/planning/recommendations?${query.toString()}`, { headers: authHeaders() })
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
    fetchRecommendations();
  }, [page, statusFilter, actionFilter]);

  const updateStatus = async (id: number, status: string, rejectionReason?: string) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/planning/recommendations/${id}/status`, {
        method: 'PUT',
        headers: {
          ...authHeaders(),
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status, rejection_reason: rejectionReason || '' })
      });
      if (res.ok) {
        fetchRecommendations();
      }
    } catch (err) {
      console.error("Failed to update status", err);
    }
  };

  const handleApprove = (id: number) => {
    updateStatus(id, 'APPROVED');
  };

  const handleReject = (id: number) => {
    const reason = prompt("Enter reason for rejection (optional):");
    if (reason !== null) {
      updateStatus(id, 'REJECTED', reason);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return <Badge className="bg-green-600 hover:bg-green-700 text-white font-bold">Approved</Badge>;
      case 'REJECTED':
        return <Badge className="bg-red-600 hover:bg-red-700 text-white font-bold">Rejected</Badge>;
      case 'REVIEWED':
        return <Badge className="bg-blue-600 hover:bg-blue-700 text-white font-bold">Reviewed</Badge>;
      case 'IMPLEMENTED':
        return <Badge className="bg-purple-600 hover:bg-purple-700 text-white font-bold">Implemented</Badge>;
      default:
        return <Badge className="bg-yellow-600 hover:bg-yellow-700 text-white font-bold">New</Badge>;
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Replenishment Recommendations</h1>
          <p className="text-muted-foreground">Planning engine suggestions. Select expedite or plant transfer actions with one-click approval.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="icon" onClick={fetchRecommendations} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4 items-center justify-start">
        <div className="flex gap-2 items-center w-full md:w-auto">
          <span className="text-sm text-muted-foreground whitespace-nowrap">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setPage(1);
            }}
            className="border p-2 rounded bg-background text-sm w-full md:w-40"
          >
            <option value="">All Statuses</option>
            <option value="NEW">New</option>
            <option value="REVIEWED">Reviewed</option>
            <option value="APPROVED">Approved</option>
            <option value="REJECTED">Rejected</option>
            <option value="IMPLEMENTED">Implemented</option>
          </select>
        </div>

        <div className="flex gap-2 items-center w-full md:w-auto">
          <span className="text-sm text-muted-foreground whitespace-nowrap">Action Type:</span>
          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value);
              setPage(1);
            }}
            className="border p-2 rounded bg-background text-sm w-full md:w-40"
          >
            <option value="">All Actions</option>
            <option value="EXPEDITE">Expedite PO</option>
            <option value="NEW_PO">New PO</option>
            <option value="TRANSFER">Stock Transfer</option>
          </select>
        </div>
      </div>

      <div className="grid gap-4">
        {loading ? (
          <div className="text-center py-8">Evaluating recommendations...</div>
        ) : (
          data.map((rec, idx) => (
            <Card key={idx} className="bg-card/45 backdrop-blur-md">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div className="flex items-center gap-2 flex-wrap">
                  <Badge variant={rec.priority === 'CRITICAL' ? 'destructive' : 'secondary'}>
                    {rec.recommendation_type || rec.action_type}
                  </Badge>
                  <span className="font-bold text-lg">{rec.material_code}</span>
                  {getStatusBadge(rec.status)}
                </div>
                <Badge variant="outline">{rec.priority} Priority</Badge>
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <p className="text-sm font-medium">{rec.reason}</p>
                <div className="text-xs text-muted-foreground bg-muted p-2 rounded">
                  <strong>Evidence:</strong> {rec.evidence}
                </div>
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mt-2 pt-2 border-t">
                  <div className="flex gap-4 text-xs text-muted-foreground flex-wrap">
                    <span>Plant: <strong>{rec.plant_name}</strong></span>
                    <span>Quantity: <strong>{rec.quantity} units</strong></span>
                    <span>Confidence: <strong>{(rec.confidence * 100).toFixed(0)}%</strong></span>
                  </div>
                  {rec.status === 'NEW' && (
                    <div className="flex gap-2">
                      <Button variant="outline" size="sm" onClick={() => handleReject(rec.id)}>Reject</Button>
                      <Button size="sm" onClick={() => handleApprove(rec.id)}>Approve Action</Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))
        )}

        {data.length === 0 && !loading && (
          <Card className="p-8 text-center text-muted-foreground bg-card/45 backdrop-blur-md">
            No recommendations match the current filters.
          </Card>
        )}
      </div>

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
    </div>
  );
}
