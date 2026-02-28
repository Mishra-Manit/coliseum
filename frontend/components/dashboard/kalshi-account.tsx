"use client";

import {
  DollarSign,
  ArrowUpDown,
  Package,
  CircleDot,
  AlertCircle,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  useKalshiBalance,
  useKalshiPositions,
  useKalshiOrders,
} from "@/hooks/use-api";

export function KalshiAccount() {
  const { data: balance, isLoading: balanceLoading } = useKalshiBalance();
  const { data: positions, isLoading: positionsLoading } =
    useKalshiPositions();
  const { data: orders, isLoading: ordersLoading } = useKalshiOrders();

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="font-display text-lg font-semibold text-foreground">
            Kalshi Account
          </CardTitle>
          <div className="flex items-center gap-2">
            {balanceLoading ? (
              <Skeleton className="h-7 w-24 bg-secondary rounded-lg" />
            ) : (
              <div className="flex items-center gap-1.5 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-lg">
                <DollarSign className="h-3.5 w-3.5 text-emerald-500" />
                <span className="text-sm font-bold text-foreground font-mono">
                  {balance?.balance_usd.toFixed(2) ?? "0.00"}
                </span>
              </div>
            )}
          </div>
        </div>
        {balance && (
          <div className="flex items-center gap-4 mt-1.5 text-[11px] text-muted-foreground font-mono">
            <span>
              Payout: ${balance.payout_usd.toFixed(2)}
            </span>
            <span>
              Balance: {balance.balance_cents}c
            </span>
          </div>
        )}
      </CardHeader>

      <Separator className="bg-border" />

      <CardContent className="pt-3">
        <Tabs defaultValue="positions" className="w-full">
          <TabsList className="bg-secondary/50 border border-border w-full rounded-lg">
            <TabsTrigger
              value="positions"
              className="flex-1 text-xs data-[state=active]:bg-amber-600 data-[state=active]:text-white rounded-md font-medium"
            >
              <Package className="h-3 w-3 mr-1.5" />
              Positions ({positions?.length ?? 0})
            </TabsTrigger>
            <TabsTrigger
              value="orders"
              className="flex-1 text-xs data-[state=active]:bg-amber-600 data-[state=active]:text-white rounded-md font-medium"
            >
              <ArrowUpDown className="h-3 w-3 mr-1.5" />
              Orders ({orders?.length ?? 0})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="positions" className="mt-3">
            {positionsLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full bg-secondary rounded-lg" />
                ))}
              </div>
            ) : positions && positions.length > 0 ? (
              <ScrollArea className="h-[250px]">
                <Table>
                  <TableHeader>
                    <TableRow className="border-border hover:bg-transparent">
                      <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 uppercase tracking-wider">
                        Market
                      </TableHead>
                      <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 uppercase tracking-wider">
                        Side
                      </TableHead>
                      <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 text-right uppercase tracking-wider">
                        Qty
                      </TableHead>
                      <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 text-right uppercase tracking-wider">
                        P&L
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {positions.map((pos) => (
                      <TableRow
                        key={pos.market_ticker}
                        className="border-border hover:bg-secondary/40"
                      >
                        <TableCell className="text-xs text-foreground font-mono py-2.5">
                          {pos.market_ticker}
                        </TableCell>
                        <TableCell className="py-2.5">
                          <Badge
                            variant="outline"
                            className={`text-[10px] px-1.5 h-[18px] font-mono font-semibold ${
                              pos.side === "yes"
                                ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/5"
                                : pos.side === "no"
                                ? "border-red-500/30 text-red-400 bg-red-500/5"
                                : "border-border text-muted-foreground"
                            }`}
                          >
                            {pos.side ?? "flat"}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-foreground text-right py-2.5 font-mono">
                          {pos.contracts}
                        </TableCell>
                        <TableCell
                          className={`text-xs text-right py-2.5 font-mono font-semibold ${
                            pos.realized_pnl > 0
                              ? "text-emerald-400"
                              : pos.realized_pnl < 0
                              ? "text-red-400"
                              : "text-muted-foreground"
                          }`}
                        >
                          {pos.realized_pnl > 0 ? "+" : ""}
                          {(pos.realized_pnl / 100).toFixed(2)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            ) : (
              <div className="text-center py-10 text-muted-foreground">
                <CircleDot className="h-7 w-7 mx-auto mb-2 opacity-20" />
                <p className="text-xs font-medium">No open positions</p>
              </div>
            )}
          </TabsContent>

          <TabsContent value="orders" className="mt-3">
            {ordersLoading ? (
              <div className="space-y-2">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-12 w-full bg-secondary rounded-lg" />
                ))}
              </div>
            ) : orders && orders.length > 0 ? (
              <ScrollArea className="h-[250px]">
                <Table>
                  <TableHeader>
                    <TableRow className="border-border hover:bg-transparent">
                      <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 uppercase tracking-wider">
                        Market
                      </TableHead>
                      <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 uppercase tracking-wider">
                        Action
                      </TableHead>
                      <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 uppercase tracking-wider">
                        Status
                      </TableHead>
                      <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 text-right uppercase tracking-wider">
                        Price
                      </TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {orders.map((order) => (
                      <TableRow
                        key={order.order_id}
                        className="border-border hover:bg-secondary/40"
                      >
                        <TableCell className="text-xs text-foreground font-mono py-2.5">
                          {order.ticker}
                        </TableCell>
                        <TableCell className="py-2.5">
                          <span className="text-xs text-muted-foreground font-mono">
                            {order.action} {order.side}
                          </span>
                        </TableCell>
                        <TableCell className="py-2.5">
                          <Badge
                            variant="outline"
                            className={`text-[10px] px-1.5 h-[18px] font-mono ${
                              order.status === "executed"
                                ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/5"
                                : order.status === "resting"
                                ? "border-yellow-500/30 text-yellow-400 bg-yellow-500/5"
                                : "border-border text-muted-foreground"
                            }`}
                          >
                            {order.status}
                          </Badge>
                        </TableCell>
                        <TableCell className="text-xs text-foreground text-right py-2.5 font-mono">
                          {order.yes_price || order.no_price}c
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </ScrollArea>
            ) : (
              <div className="text-center py-10 text-muted-foreground">
                <AlertCircle className="h-7 w-7 mx-auto mb-2 opacity-20" />
                <p className="text-xs font-medium">No active orders</p>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
