import { ChartAreaInteractive } from "@/components/chart-area-interactive";
import { OilPrice, SectionCards } from "@/components/section-cards";
import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { AlertCircleIcon } from "lucide-react";

// Revalidate this page every 10 minutes to fetch fresh data
export const revalidate = 600; // 10 minutes

export default async function Page() {
  const API_URL = process.env.API_URL ?? "http://localhost:8000";
  const API_KEY = process.env.API_KEY ?? "";
  if (!API_KEY) {
    throw new Error("API_KEY is not set");
  }
  const req = await fetch(API_URL + "/prices", {
    headers: {
      "x-api-key": "API_KEY",
    },
  });

  if (!req.ok) {
    return (
      <div className="@container/main flex flex-col gap-4 py-4 mx-4 md:gap-6 md:py-6">
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertTitle>Unable to Load Data</AlertTitle>
          <AlertDescription>
            We couldn&apos;t retrieve the oil price data at this time. Please
            try again later.
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  const data: OilPrice[] = await req.json();
  const cards = data.reduce((acc, curr) => {
    const existing = acc.get(curr.supplier_name);
    if (!existing || new Date(curr.date) > new Date(existing.date)) {
      acc.set(curr.supplier_name, curr);
    }
    return acc;
  }, new Map<string, OilPrice>());
  const latestPrices = Array.from(cards.values());
  return (
    <>
      <div className="@container/main flex flex-col gap-4 py-4 md:gap-6 md:py-6">
        <SectionCards cards={latestPrices} />
        <div className="px-4 lg:px-6">
          <ChartAreaInteractive data={data} />
        </div>
      </div>
    </>
  );
}
