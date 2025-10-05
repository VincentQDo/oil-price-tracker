import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ExternalLink } from "lucide-react";

export function SectionCards() {
  const cards: { id: number; price: number; supplier: string }[] = [
    { id: 1, price: 1250, supplier: "Shell" },
    { id: 2, price: 1500, supplier: "Exxon" },
    { id: 3, price: 1750, supplier: "Chevron" },
    { id: 4, price: 2000, supplier: "BP" },
  ];
  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      {cards.map((card, index) => (
        <Card key={index} className="@container/card">
          <CardHeader>
            <CardDescription>{card.supplier}</CardDescription>
            <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
              ${card.price}
              <span className="text-muted-foreground text-sm font-normal">
                /gallon
              </span>
            </CardTitle>
            {/* <CardAction>
                <Badge variant="outline">
                  <IconTrendingUp />
                  +12.5%
                </Badge>
              </CardAction> */}
          </CardHeader>
          <CardFooter className="flex-col items-start gap-1.5 text-sm">
            <a
              className="line-clamp-1 flex gap-2 font-medium border-b border-transparent hover:border-current"
              href="#"
            >
              Go to {card.supplier} website <ExternalLink className="!size-4" />
            </a>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
