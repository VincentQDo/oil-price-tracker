import { Alert, AlertTitle, AlertDescription } from "@/components/ui/alert";
import { AlertCircleIcon } from "lucide-react";

export default function UnauthorizedPage() {
  return (
    <div className="@container/main flex flex-col gap-4 py-4 mx-4 md:gap-6 md:py-6">
      <Alert variant="destructive">
        <AlertCircleIcon />
        <AlertTitle>Unauthorized Access</AlertTitle>
        <AlertDescription>
          You do not have permission to view this page. Please try again later.
        </AlertDescription>
      </Alert>
    </div>
  );
}
