"use client";

import { CircleDot } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ScrollArea } from "@/components/ui/scroll-area";
import { usePortfolioState } from "@/hooks/use-api";
import { BgTint, BorderTint } from "@/lib/styles";

interface KalshiAccountProps {
  onSelectOpportunity?: (id: string) => void;
}

export function KalshiAccount({ onSelectOpportunity }: KalshiAccountProps) {
  const { data: state, isLoading } = usePortfolioState();

  const positions = state?.open_positions ?? [];

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="font-display text-lg font-semibold text-foreground">
            Open Positions
          </CardTitle>
          <Badge
            variant="outline"
            className="border-border bg-secondary/50 text-muted-foreground text-[10px] font-mono"
          >
            {positions.length} active
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        {isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-12 w-full bg-secondary rounded-lg" />
            ))}
          </div>
        ) : positions.length > 0 ? (
          <ScrollArea className="h-[300px]">
            <Table>
              <TableHeader>
                <TableRow className="border-border hover:bg-transparent">
                  <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 uppercase tracking-wider w-full">
                    Market
                  </TableHead>
                  <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 uppercase tracking-wider whitespace-nowrap">
                    Side
                  </TableHead>
                  <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 text-right uppercase tracking-wider whitespace-nowrap">
                    Qty
                  </TableHead>
                  <TableHead className="text-[10px] text-muted-foreground font-semibold h-8 text-right uppercase tracking-wider whitespace-nowrap">
                    Entry
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {positions.map((pos) => {
                  const isClickable =
                    !!pos.opportunity_id && !!onSelectOpportunity;
                  return (
                    <TableRow
                      key={pos.id}
                      onClick={
                        isClickable
                          ? () => onSelectOpportunity!(pos.opportunity_id!)
                          : undefined
                      }
                      className={`border-border transition-colors ${
                        isClickable
                          ? `cursor-pointer hover:${BgTint.amberHover} hover:${BorderTint.amberSelected}`
                          : "hover:bg-secondary/40"
                      }`}
                    >
                      <TableCell className="text-xs text-foreground font-mono py-2.5 max-w-0 w-full">
                        <span
                          className="block truncate"
                          title={pos.market_ticker}
                        >
                          {pos.market_ticker}
                        </span>
                      </TableCell>
                      <TableCell className="py-2.5">
                        <Badge
                          variant="outline"
                          className={`text-[10px] px-1.5 h-[18px] font-mono font-semibold ${
                            pos.side === "YES"
                              ? `${BorderTint.yesBadge} text-emerald-400 ${BgTint.emeraldBox}`
                              : pos.side === "NO"
                              ? `${BorderTint.noBadge} text-red-400 ${BgTint.redBox}`
                              : "border-border text-muted-foreground"
                          }`}
                        >
                          {pos.side}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-foreground text-right py-2.5 font-mono whitespace-nowrap">
                        {pos.contracts}
                      </TableCell>
                      <TableCell className="text-xs text-foreground text-right py-2.5 font-mono whitespace-nowrap">
                        {Math.round(pos.average_entry * 100)}c
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </ScrollArea>
        ) : (
          <div className="text-center py-10 text-muted-foreground">
            <CircleDot className="h-7 w-7 mx-auto mb-2 opacity-20" />
            <p className="text-xs font-medium">No open positions</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
