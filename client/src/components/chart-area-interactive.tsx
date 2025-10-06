"use client";

import * as React from "react";
import { Area, AreaChart, CartesianGrid, XAxis } from "recharts";

import { useIsMobile } from "@/hooks/use-mobile";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  ChartConfig,
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
} from "@/components/ui/chart";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { OilPrice } from "./section-cards";

export const description = "An interactive area chart";

export function ChartAreaInteractive(params: { data?: OilPrice[] }) {
  const isMobile = useIsMobile();
  const [timeRange, setTimeRange] = React.useState("3m");

  React.useEffect(() => {
    if (isMobile) {
      setTimeRange("3m");
    }
  }, [isMobile]);

  const filteredData =
    params.data?.filter((item) => {
      const date = new Date(item.date);
      const startDate = new Date();
      switch (timeRange) {
        case "2y":
          startDate.setFullYear(startDate.getFullYear() - 2);
          break;
        case "6m":
          startDate.setMonth(startDate.getMonth() - 6);
          break;
        case "3m":
        default:
          startDate.setMonth(startDate.getMonth() - 3);
          break;
      }
      return date >= startDate;
    }) || [];

  // Transform data into a map of date to { supplier1: price, supplier2: price, ... }
  const tmp = filteredData.reduce((acc, curr) => {
    if (!acc.get(curr.date)) acc.set(curr.date, {});
    acc.get(curr.date)![curr.supplier_name.replaceAll(" ", "")] = curr.price;
    return acc;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
  }, new Map<string, any>());
  console.log("tmp", tmp);

  // Transform the map into an array of objects like so: [{ date: "2023-01-01", Supplier1: price, Supplier2: price, ... }, ...]
  const chartData = Array.from(tmp, ([date, prices]) => ({
    date,
    ...prices,
  })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  console.log("chartData", chartData);

  const supplierNames = new Set<string>();
  chartData.forEach((item) => {
    Object.keys(item).forEach((key) => {
      if (key !== "date") {
        supplierNames.add(key);
      }
    });
  });
  const chartConfig =
    supplierNames.size > 0
      ? (Object.fromEntries(
          [...supplierNames].map((k, i) => {
            // Create a config object like so: { Supplier 1: { label: "Supplier 1", color: "hsl(0, 70%, 50%)" }, ... }
            // The replace simply add the spaces that were removed for the key names
            return [
              k,
              {
                label: k.replace(/([A-Z])/g, " $1").trim(),
                color: `hsl(${(i * 60) % 360}, 70%, 50%)`,
              },
            ];
          })
        ) satisfies ChartConfig)
      : ({} satisfies ChartConfig);
  console.log("chartConfig", chartConfig);

  return (
    <Card className="@container/card">
      <CardHeader>
        <CardTitle>Oil Prices</CardTitle>
        <CardDescription>
          <span className="hidden @[540px]/card:block">
            Prices for the last 3 months
          </span>
          <span className="@[540px]/card:hidden">Last 3 months</span>
        </CardDescription>
        <CardAction>
          <ToggleGroup
            type="single"
            value={timeRange}
            onValueChange={setTimeRange}
            variant="outline"
            className="hidden *:data-[slot=toggle-group-item]:!px-4 @[767px]/card:flex"
          >
            <ToggleGroupItem value="2y">Last 2 years</ToggleGroupItem>
            <ToggleGroupItem value="6m">Last 6 months</ToggleGroupItem>
            <ToggleGroupItem value="3m">Last 3 months</ToggleGroupItem>
          </ToggleGroup>
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger
              className="flex w-40 **:data-[slot=select-value]:block **:data-[slot=select-value]:truncate @[767px]/card:hidden"
              size="sm"
              aria-label="Select a value"
            >
              <SelectValue placeholder="Last 3 months" />
            </SelectTrigger>
            <SelectContent className="rounded-xl">
              <SelectItem value="2y" className="rounded-lg">
                Last 2 years
              </SelectItem>
              <SelectItem value="6m" className="rounded-lg">
                Last 6 months
              </SelectItem>
              <SelectItem value="3m" className="rounded-lg">
                Last 3 months
              </SelectItem>
            </SelectContent>
          </Select>
        </CardAction>
      </CardHeader>
      <CardContent className="px-2 pt-4 sm:px-6 sm:pt-6">
        <ChartContainer
          config={chartConfig}
          className="aspect-auto h-[250px] w-full"
        >
          <AreaChart data={chartData}>
            <defs>
              {Object.entries(chartConfig).map(([key, { color }]) => (
                <linearGradient
                  id={`fill${key}`}
                  x1="0"
                  y1="0"
                  x2="0"
                  y2="1"
                  key={key}
                >
                  <stop offset="5%" stopColor={color} stopOpacity={1.0} />
                  <stop offset="95%" stopColor={color} stopOpacity={0.1} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid vertical={false} />
            <XAxis
              dataKey="date"
              tickLine={false}
              axisLine={false}
              tickMargin={8}
              minTickGap={32}
              tickFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleDateString("en-US", {
                  year: "2-digit",
                  month: "short",
                  day: "numeric",
                });
              }}
            />
            <ChartTooltip
              cursor={false}
              content={
                <ChartTooltipContent
                  labelFormatter={(value) => {
                    return new Date(value).toLocaleDateString("en-US", {
                      year: "numeric",
                      month: "short",
                      day: "numeric",
                    });
                  }}
                  indicator="dot"
                />
              }
            />
            {Object.entries(chartConfig).map(([key, { color, label }]) => (
              <Area
                key={key}
                dataKey={key}
                type="natural"
                fill={`url(#fill${key})`}
                stroke={color}
                stackId="a"
                name={label}
                isAnimationActive={false}
                dot={false}
              />
            ))}
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
