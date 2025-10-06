import {
  Card,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ExternalLink } from "lucide-react";

export interface OilPrice {
  id: number;
  date: string;
  supplier_name: string;
  supplier_url: string;
  price: number;
}

export function SectionCards(params: { cards?: OilPrice[] }) {
  const cards = params.cards || [];
  return (
    <div className="*:data-[slot=card]:from-primary/5 *:data-[slot=card]:to-card dark:*:data-[slot=card]:bg-card grid grid-cols-1 gap-4 px-4 *:data-[slot=card]:bg-gradient-to-t *:data-[slot=card]:shadow-xs lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-4">
      {cards.map((card) => (
        <Card key={card.id} className="@container/card">
          <CardHeader>
            <CardDescription>
              Last updated:{" "}
              {new Date(card.date).toLocaleDateString("en-US", {
                year: "numeric",
                month: "short",
                day: "numeric",
              })}
            </CardDescription>
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
              href={card.supplier_url}
              target="_blank"
            >
              Go to {card.supplier_name} <ExternalLink className="!size-4" />
            </a>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}
