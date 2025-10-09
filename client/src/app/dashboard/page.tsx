import { ChartAreaInteractive } from "@/components/chart-area-interactive";
import { OilPrice, SectionCards } from "@/components/section-cards";
import { SiteHeader } from "@/components/site-header";

export default async function Page() {
  const API_URL = process.env.API_URL ?? "http://localhost:8000";
  const req = await fetch(API_URL + "/prices", {
    next: { revalidate: 1000 * 60 * 60 * 12 }, // 12 hours
  });
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
      <SiteHeader />
      <div className="flex flex-1 flex-col">
        <div className="@container/main flex flex-1 flex-col gap-2">
          <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
            <SectionCards cards={latestPrices} />
            <div className="px-4 lg:px-6">
              <ChartAreaInteractive data={data} />
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
